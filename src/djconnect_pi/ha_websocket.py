from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import logging
import time
from urllib.parse import urlparse, urlunparse
import requests

from .config import CLIENT_TYPE, Config

_LOGGER = logging.getLogger(__name__)


class WebSocketFastPathError(RuntimeError):
    pass


class WebSocketFastPathAuthError(WebSocketFastPathError):
    pass


REQUESTED_COMMANDS: tuple[str, ...] = (
    "djconnect/command",
    "djconnect/ask_dj/message",
    "djconnect/ask_dj/history",
    "djconnect/ask_dj/history/clear",
    "djconnect/music_dna/profile",
    "djconnect/music_dna/settings",
    "djconnect/music_dna/clear",
    "djconnect/music_discovery/feed",
    "djconnect/music_discovery/refresh",
    "djconnect/music_discovery/play",
    "djconnect/music_discovery/feedback",
    "djconnect/track_insight",
)


@dataclass
class WebSocketFastPath:
    cfg: Config
    default_timeout: float = 4.0
    transport: str = "http"
    connected: bool = False
    last_error: str = ""
    last_capability_refresh: float = 0.0
    commands: tuple[str, ...] = ()
    features: dict[str, bool] = field(default_factory=dict)
    fallbacks: dict[str, str] = field(default_factory=dict)
    unhealthy_until: float = 0.0
    _access_token: str = field(default="", init=False, repr=False)
    _access_token_expires_at: float = field(default=0.0, init=False, repr=False)
    _websocket_url: str = field(default="", init=False, repr=False)
    _message_id: int = field(default=0, init=False, repr=False)

    def update_config(self, cfg: Config) -> None:
        self.cfg = cfg

    def diagnostics(self) -> dict[str, Any]:
        return {
            "fast_path_enabled": self.cfg.websocket_fast_path_enabled,
            "fast_path_transport": self.transport,
            "websocket_connected": self.connected,
            "advertised_commands": list(self.commands),
            "last_capability_refresh": self.last_capability_refresh,
            "last_error": self.last_error,
            "fastPathTransport": self.transport,
            "fastPathEnabled": self.cfg.websocket_fast_path_enabled,
            "websocketEnabled": self.cfg.websocket_fast_path_enabled,
            "websocketAuthConfigured": bool(self.cfg.device_token),
            "websocketConnected": self.connected,
            "lastWebSocketError": self.last_error,
            "lastCapabilityRefresh": self.last_capability_refresh,
            "websocketCommands": list(self.commands),
            "features": dict(self.features),
            "fallbacks": dict(self.fallbacks),
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
        if not self.commands or time.monotonic() - self.last_capability_refresh > 300:
            try:
                self.refresh_capabilities(timeout=min(5.0, max(1.0, self.default_timeout)))
            except Exception as exc:
                self._mark_unhealthy(exc)
                return False
        return command in self.commands

    def refresh_capabilities(self, *, timeout: float) -> None:
        self._ensure_session(timeout=timeout)
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
        features = response.get("features")
        self.features = {str(key): bool(value) for key, value in features.items()} if isinstance(features, dict) else {}
        fallbacks = response.get("fallbacks")
        self.fallbacks = _flatten_fallbacks(fallbacks) if isinstance(fallbacks, dict) else {}
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
        self._ensure_session(timeout=timeout)
        ws = _websocket_create_connection(self._url(), timeout=timeout)
        try:
            auth_required = _websocket_recv_json(ws)
            if auth_required.get("type") != "auth_required":
                raise WebSocketFastPathError("Home Assistant WebSocket auth_required was not received")
            ws.send(json.dumps({"type": "auth", "access_token": self._access_token}))
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

    def _ensure_session(self, *, timeout: float) -> None:
        if self._access_token and time.time() < self._access_token_expires_at - 30:
            return
        if not self.cfg.device_token:
            raise WebSocketFastPathAuthError("DJConnect bearer token is not configured")
        url = self._session_url()
        payload = {
            "device_id": self.cfg.device_id,
            "client_type": CLIENT_TYPE,
            "requested_commands": list(REQUESTED_COMMANDS),
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.cfg.device_token}",
            "X-DJConnect-Device-ID": self.cfg.device_id,
            "X-DJConnect-Client-Type": CLIENT_TYPE,
        }
        started = time.monotonic()
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        _LOGGER.debug("POST %s returned HTTP %s in %.0fms", url, response.status_code, (time.monotonic() - started) * 1000)
        data = _response_json(response)
        if response.status_code >= 400 or not isinstance(data.get("access_token"), str) or not str(data.get("access_token")).strip():
            raise WebSocketFastPathAuthError("WebSocket session bootstrap failed")
        self._access_token = str(data["access_token"])
        self._access_token_expires_at = _expires_at(data.get("expires_at"))
        self._websocket_url = str(data.get("websocket_url") or "")
        commands = data.get("commands")
        if isinstance(commands, list) and commands:
            self.commands = tuple(str(item) for item in commands if isinstance(item, str))

    def _session_url(self) -> str:
        return self._base_url("/api/djconnect/v1/websocket/session")

    def _url(self) -> str:
        if self._websocket_url:
            return self._websocket_url
        return self._base_url("/api/websocket", websocket=True)

    def _base_url(self, path: str, *, websocket: bool = False) -> str:
        parsed = urlparse(self.cfg.ha_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebSocketFastPathError("WebSocket fast path requires a local HTTP(S) Home Assistant URL")
        scheme = ("wss" if parsed.scheme == "https" else "ws") if websocket else parsed.scheme
        return urlunparse((scheme, parsed.netloc, path, "", "", ""))

    def _next_id(self) -> int:
        self._message_id += 1
        return self._message_id

    def _mark_unhealthy(self, exc: Exception) -> None:
        self.transport = "http"
        self.connected = False
        self.last_error = exc.__class__.__name__
        self.unhealthy_until = time.monotonic() + 30
        if isinstance(exc, WebSocketFastPathAuthError):
            self._access_token = ""
            self._access_token_expires_at = 0.0
            self._websocket_url = ""
        _LOGGER.debug("WebSocket fast path unavailable; falling back to HTTP: %s", exc.__class__.__name__)


def _websocket_create_connection(url: str, *, timeout: float) -> Any:
    try:
        import websocket
    except ImportError as exc:
        raise WebSocketFastPathError("websocket-client is not installed") from exc
    return websocket.create_connection(url, timeout=timeout)


def _flatten_fallbacks(value: dict[str, Any], prefix: str = "") -> dict[str, str]:
    flattened: dict[str, str] = {}
    for key, item in value.items():
        full_key = f"{prefix}_{key}" if prefix else str(key)
        if isinstance(item, dict):
            flattened.update(_flatten_fallbacks(item, full_key))
        elif item:
            flattened[full_key] = str(item)
    return flattened


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


def _response_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json() if response.content else {}
    except ValueError as exc:
        raise WebSocketFastPathError("WebSocket session returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise WebSocketFastPathError("WebSocket session returned non-object JSON")
    return data


def _expires_at(value: object) -> float:
    if value in (None, ""):
        return time.time() + 240
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        pass
    try:
        from datetime import datetime

        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return time.time() + 240
