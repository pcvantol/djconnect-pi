from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import ipaddress
import json
import logging
import time
from urllib.parse import urlparse, urlunparse

from .config import CLIENT_TYPE, Config

_LOGGER = logging.getLogger(__name__)


class WebSocketFastPathError(RuntimeError):
    pass


class WebSocketFastPathAuthError(WebSocketFastPathError):
    pass


@dataclass
class WebSocketFastPath:
    cfg: Config
    default_timeout: float = 4.0
    transport: str = "http"
    connected: bool = False
    last_error: str = ""
    last_capability_refresh: float = 0.0
    commands: tuple[str, ...] = ()
    unhealthy_until: float = 0.0
    _message_id: int = field(default=0, init=False, repr=False)

    def update_config(self, cfg: Config) -> None:
        self.cfg = cfg

    def diagnostics(self) -> dict[str, Any]:
        return {
            "fastPathTransport": self.transport,
            "websocketEnabled": self.cfg.websocket_fast_path_enabled,
            "websocketAuthConfigured": bool(self.cfg.ha_websocket_token),
            "websocketConnected": self.connected,
            "lastWebSocketError": self.last_error,
            "lastCapabilityRefresh": self.last_capability_refresh,
            "websocketCommands": list(self.commands),
        }

    def try_request(self, message_type: str, body: dict[str, Any], *, command: str, timeout: float) -> dict[str, Any] | None:
        self.transport = "http"
        if not self.can_handle(command):
            return None
        try:
            data = self._request(message_type, body, timeout=timeout)
        except Exception as exc:
            self._mark_unhealthy(exc)
            return None
        self.transport = "websocket"
        self.connected = True
        self.last_error = ""
        return data

    def can_handle(self, command: str) -> bool:
        if not self.cfg.websocket_fast_path_enabled:
            return False
        if not self.cfg.ha_websocket_token:
            return False
        if not self.cfg.device_token or not self.cfg.ha_url:
            return False
        if time.monotonic() < self.unhealthy_until:
            return False
        try:
            parsed = urlparse(self.cfg.ha_url)
        except ValueError:
            return False
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        if not _is_local_ha_url(parsed.hostname or ""):
            return False
        if not self.commands or time.monotonic() - self.last_capability_refresh > 300:
            try:
                self.refresh_capabilities(timeout=min(5.0, max(1.0, self.default_timeout)))
            except Exception as exc:
                self._mark_unhealthy(exc)
                return False
        return command in self.commands

    def refresh_capabilities(self, *, timeout: float) -> None:
        response = self._exchange("djconnect/capabilities", {}, timeout=timeout, requires_djconnect_auth=False)
        commands = response.get("commands")
        transports = response.get("transports")
        websocket_transport = isinstance(transports, dict) and transports.get("websocket") is True
        if response.get("success") is False:
            raise WebSocketFastPathError("WebSocket capabilities rejected")
        if response.get("websocket_supported") is not True or not websocket_transport:
            raise WebSocketFastPathError("WebSocket capability is not enabled by Home Assistant")
        if not isinstance(commands, list):
            raise WebSocketFastPathError("WebSocket capabilities missing commands")
        self.commands = tuple(str(item) for item in commands if isinstance(item, str))
        self.last_capability_refresh = time.time()
        self.connected = True
        self.last_error = ""

    def _request(self, message_type: str, body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
        response = self._exchange(message_type, body, timeout=timeout, requires_djconnect_auth=True)
        if response.get("success") is False:
            error = str(response.get("error") or "websocket_error")
            if error in {"unauthorized", "forbidden", "not_configured", "stale_pairing", "stale_token", "invalid_token"}:
                raise WebSocketFastPathAuthError(str(response.get("message") or error))
            raise WebSocketFastPathError(error)
        return response

    def _exchange(self, message_type: str, body: dict[str, Any], *, timeout: float, requires_djconnect_auth: bool) -> dict[str, Any]:
        ws = _websocket_create_connection(self._url(), timeout=timeout)
        try:
            auth_required = _websocket_recv_json(ws)
            if auth_required.get("type") != "auth_required":
                raise WebSocketFastPathError("Home Assistant WebSocket auth_required was not received")
            ws.send(json.dumps({"type": "auth", "access_token": self.cfg.ha_websocket_token}))
            auth_response = _websocket_recv_json(ws)
            if auth_response.get("type") != "auth_ok":
                raise WebSocketFastPathAuthError("Home Assistant WebSocket auth failed")
            message = {"id": self._next_id(), "type": message_type, **body}
            if requires_djconnect_auth:
                message.update(
                    {
                        "device_id": self.cfg.device_id,
                        "client_id": self.cfg.device_id,
                        "device_name": self.cfg.device_name,
                        "client_type": CLIENT_TYPE,
                        "device_token": self.cfg.device_token,
                    }
                )
                if self.cfg.music_dna_key:
                    message["music_dna_key"] = self.cfg.music_dna_key
            ws.send(json.dumps(message))
            response = _websocket_recv_json(ws)
            if response.get("type") == "result":
                if response.get("success") is False:
                    error = response.get("error")
                    if isinstance(error, dict):
                        return {"success": False, "error": str(error.get("code") or "websocket_error"), "message": str(error.get("message") or "")}
                    return {"success": False, "error": "websocket_error"}
                result = response.get("result")
                if isinstance(result, dict):
                    return result
                return {"success": True}
            if response.get("type") == message_type:
                return response
            raise WebSocketFastPathError("Unexpected Home Assistant WebSocket response")
        finally:
            try:
                ws.close()
            except Exception:
                pass

    def _url(self) -> str:
        parsed = urlparse(self.cfg.ha_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebSocketFastPathError("WebSocket fast path requires a local HTTP(S) Home Assistant URL")
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse((scheme, parsed.netloc, "/api/websocket", "", "", ""))

    def _next_id(self) -> int:
        self._message_id += 1
        return self._message_id

    def _mark_unhealthy(self, exc: Exception) -> None:
        self.transport = "http"
        self.connected = False
        self.last_error = exc.__class__.__name__
        self.unhealthy_until = time.monotonic() + 30
        _LOGGER.debug("WebSocket fast path unavailable; falling back to HTTP: %s", exc.__class__.__name__)


def _websocket_create_connection(url: str, *, timeout: float) -> Any:
    try:
        import websocket
    except ImportError as exc:
        raise WebSocketFastPathError("websocket-client is not installed") from exc
    return websocket.create_connection(url, timeout=timeout)


def _is_local_ha_url(hostname: str) -> bool:
    host = hostname.strip().lower().strip("[]")
    if not host:
        return False
    if host == "localhost" or host.endswith(".local") or "." not in host:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def _websocket_recv_json(ws: Any) -> dict[str, Any]:
    raw = ws.recv()
    if not isinstance(raw, str):
        raise WebSocketFastPathError("Home Assistant WebSocket returned a non-text frame")
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise WebSocketFastPathError("Home Assistant WebSocket returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise WebSocketFastPathError("Home Assistant WebSocket returned non-object JSON")
    return data
