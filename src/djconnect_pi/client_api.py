from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
import json
import logging
import socket
import threading
from urllib.parse import parse_qs, urlparse

from .config import CLIENT_TYPE, Config, load_config, save_config
from .web_portal import index_html

try:
    from zeroconf import ServiceInfo, Zeroconf
except ImportError:  # pragma: no cover - install dependency on target image
    ServiceInfo = None
    Zeroconf = None

_LOGGER = logging.getLogger(__name__)
MAX_REQUEST_BYTES = 64 * 1024


class ClientAPIState:
    def __init__(
        self,
        *,
        cfg: Config,
        config_path,
        playback_provider: Callable[[], dict[str, Any]],
        command_handler: Callable[[str, dict[str, Any]], dict[str, Any]],
        dj_response_handler: Callable[[dict[str, Any]], dict[str, Any]],
        screenshot_handler: Callable[[], dict[str, Any]],
        pair_handler: Callable[[], None],
        forget_handler: Callable[[], None],
        portal_state_provider: Callable[[set[str]], dict[str, Any]] | None = None,
        mdns_refresh_handler: Callable[[], None] | None = None,
    ) -> None:
        self.cfg = cfg
        self.config_path = config_path
        self.playback_provider = playback_provider
        self.command_handler = command_handler
        self.dj_response_handler = dj_response_handler
        self.screenshot_handler = screenshot_handler
        self.pair_handler = pair_handler
        self.forget_handler = forget_handler
        self.portal_state_provider = portal_state_provider
        self.mdns_refresh_handler = mdns_refresh_handler

    def reload_config(self) -> None:
        self.cfg = load_config(self.config_path)


class ClientAPIHandler(BaseHTTPRequestHandler):
    server: "ClientAPIServer"

    def log_message(self, fmt: str, *args: object) -> None:
        _LOGGER.info("Client API " + fmt, *args)

    def do_GET(self) -> None:
        _LOGGER.debug("Client API GET %s", self.path)
        parsed = urlparse(self.path)
        if parsed.path in {"", "/"}:
            self._write_html(index_html(self.server.state.cfg.version))
            return
        if parsed.path == "/api/portal/state":
            include = {
                value.strip()
                for value in str(parse_qs(parsed.query).get("include", [""])[0]).split(",")
                if value.strip()
            }
            self._write_json(self._portal_state(include))
            return
        if parsed.path == "/api/device/info":
            self._write_json(self._info())
            return
        if parsed.path == "/api/device/pairing-info":
            self._write_json(self._pairing_info())
            return
        if parsed.path == "/api/debug/screen":
            if not self._loopback_request():
                _LOGGER.warning("Client API non-loopback debug screen request rejected")
                self._write_json({"success": False, "error": "forbidden"}, HTTPStatus.FORBIDDEN)
                return
            screen = str(parse_qs(parsed.query).get("screen", [""])[0]).strip()
            if not screen:
                self._write_json({"success": False, "error": "missing_screen"}, HTTPStatus.BAD_REQUEST)
                return
            _LOGGER.info("Client API local debug screen request: %s", screen)
            self._write_json(self.server.state.command_handler("debug_show_screen", {"screen": screen}))
            return
        if parsed.path == "/api/debug/screenshot":
            if self.server.state.cfg.device_token and not (self._authorized() or self._loopback_request()):
                _LOGGER.warning("Client API unauthorized debug screenshot request")
                self._write_json({"success": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            _LOGGER.info("Client API debug screenshot request")
            self._write_json(self.server.state.screenshot_handler())
            return
        self._write_json({"success": False, "error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        _LOGGER.debug("Client API POST %s", self.path)
        payload = self._read_json()
        if payload.get("_request_too_large"):
            self._write_json({"success": False, "error": "request_too_large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        if self.path == "/api/device/pair":
            self._handle_pair(payload)
            return
        if self.path == "/api/portal/command":
            command = str(payload.get("command") or "")
            _LOGGER.info("Client API web portal command=%s", command)
            self._write_json(self._portal_command(command, payload))
            return
        if self.path == "/api/device/command":
            if not self._authorized():
                _LOGGER.warning("Client API unauthorized command request")
                self._write_json({"success": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            command = str(payload.get("command") or "")
            _LOGGER.debug("Client API command=%s payload_keys=%s", command, sorted(payload))
            self._write_json(self.server.state.command_handler(command, payload))
            return
        if self.path == "/api/device/dj_response":
            if not self._authorized():
                _LOGGER.warning("Client API unauthorized DJ response request")
                self._write_json({"success": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            _LOGGER.debug("Client API DJ response payload_keys=%s", sorted(payload))
            self._write_json(self.server.state.dj_response_handler(payload))
            return
        if self.path == "/api/device/restart":
            status = self._device_auth_status()
            if status is not HTTPStatus.OK:
                _LOGGER.warning("Client API unauthorized Raspberry Pi restart request")
                self._write_json({"success": False, "error": "unauthorized"}, status)
                return
            _LOGGER.info("Client API Raspberry Pi restart request for device_id=%s", self.server.state.cfg.device_id)
            self.server.state.command_handler("reboot", {"command": "reboot"})
            self._write_json({"success": True, "message": "Restart scheduled"})
            return
        if self.path == "/api/device/shutdown":
            status = self._device_auth_status()
            if status is not HTTPStatus.OK:
                _LOGGER.warning("Client API unauthorized Raspberry Pi shutdown request")
                self._write_json({"success": False, "error": "unauthorized"}, status)
                return
            _LOGGER.info("Client API Raspberry Pi shutdown request for device_id=%s", self.server.state.cfg.device_id)
            self.server.state.command_handler("shutdown", {"command": "shutdown"})
            self._write_json({"success": True, "message": "Shutdown scheduled"})
            return
        if self.path == "/api/device/forget":
            if not self._authorized():
                _LOGGER.warning("Client API unauthorized forget request")
                self._write_json({"success": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            _LOGGER.info("Client API forget pairing request for device_id=%s", self.server.state.cfg.device_id)
            self.server.state.forget_handler()
            self.server.state.reload_config()
            if self.server.state.mdns_refresh_handler is not None:
                self.server.state.mdns_refresh_handler()
            self._write_json({"success": True})
            return
        self._write_json({"success": False, "error": "not_found"}, HTTPStatus.NOT_FOUND)

    def _handle_pair(self, payload: dict[str, Any]) -> None:
        self.server.state.reload_config()
        token = str(payload.get("device_token") or payload.get("token") or payload.get("bearer_token") or "").strip()
        ha_url = str(payload.get("ha_local_url") or payload.get("ha_url") or "").strip()
        if not token or not ha_url:
            _LOGGER.warning("Client API pair request missing required fields")
            self._write_json({"success": False, "error": "missing_pairing_fields"}, HTTPStatus.BAD_REQUEST)
            return
        cfg = self.server.state.cfg
        requested_client_type = str(payload.get("client_type") or CLIENT_TYPE).strip()
        if requested_client_type != CLIENT_TYPE:
            _LOGGER.warning("Client API pair request rejected for client_type=%s", requested_client_type)
            self._write_json({"success": False, "error": "invalid_client_type"}, HTTPStatus.BAD_REQUEST)
            return
        requested_device_id = str(payload.get("device_id") or cfg.device_id).strip()
        if requested_device_id != cfg.device_id:
            _LOGGER.warning("Client API pair request rejected for mismatched device_id=%s", requested_device_id)
            self._write_json({"success": False, "error": "invalid_device_id"}, HTTPStatus.BAD_REQUEST)
            return
        cfg.device_token = token
        cfg.ha_url = ha_url
        cfg.paired = True
        save_config(self.server.state.config_path, cfg)
        self.server.state.pair_handler()
        if self.server.state.mdns_refresh_handler is not None:
            self.server.state.mdns_refresh_handler()
        _LOGGER.info("Client API paired device_id=%s ha_url=%s", cfg.device_id, ha_url)
        self._write_json({"success": True, "device_id": cfg.device_id, "client_type": CLIENT_TYPE})

    def _info(self) -> dict[str, Any]:
        self.server.state.reload_config()
        cfg = self.server.state.cfg
        playback = self.server.state.playback_provider()
        return {
            "success": True,
            "device_id": cfg.device_id,
            "device_name": cfg.device_name,
            "client_type": CLIENT_TYPE,
            "firmware": cfg.version,
            "version": cfg.version,
            "app_version": cfg.version,
            "platform": "raspberry_pi",
            "paired": cfg.paired,
            "ha_pairing_status": "paired" if cfg.paired else "pending",
            "local_url": cfg.local_url,
            "capabilities": _capabilities(),
            "playback": playback,
        }

    def _pairing_info(self) -> dict[str, Any]:
        info = self._info()
        info["pair_code"] = self.server.state.cfg.pairing_code
        info["pairing_code"] = self.server.state.cfg.pairing_code
        info["pairing_token"] = self.server.state.cfg.pairing_code
        return info

    def _portal_state(self, include: set[str]) -> dict[str, Any]:
        if self.server.state.portal_state_provider is None:
            cfg = self.server.state.cfg
            playback = self.server.state.playback_provider()
            return {
                "success": True,
                "paired": cfg.paired,
                "backend_available": cfg.paired,
                "status_text": "Verbonden" if cfg.paired else "Niet gekoppeld",
                "playback": playback,
                "queue": [],
                "playlists": [],
                "logs": "",
                "settings": _portal_settings(cfg),
                "about": _portal_about(cfg),
                "diagnostics": [
                    {"name": "Local Client API", "status": "running", "detail": cfg.local_url},
                    {"name": "Home Assistant API", "status": "running" if cfg.paired else "stopped", "detail": cfg.ha_url},
                ],
            }
        return self.server.state.portal_state_provider(include)

    def _portal_command(self, command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not command:
            return {"success": False, "error": "missing_command"}
        if command == "settings":
            self._apply_portal_settings(payload)
            return {"success": True, "command": command}
        if command == "forget_pairing":
            self.server.state.forget_handler()
            self.server.state.reload_config()
            if self.server.state.mdns_refresh_handler is not None:
                self.server.state.mdns_refresh_handler()
            return {"success": True, "command": command}
        allowed = {
            "play",
            "pause",
            "next",
            "previous",
            "set_volume",
            "set_shuffle",
            "set_repeat",
            "set_output",
            "play_context_at",
            "start_playlist",
            "start_queue_item",
            "check_updates",
            "reboot",
            "shutdown",
            "debug_show_screen",
        }
        if command not in allowed:
            return {"success": False, "error": "unsupported_command"}
        return self.server.state.command_handler(command, payload)

    def _apply_portal_settings(self, payload: dict[str, Any]) -> None:
        self.server.state.reload_config()
        cfg = self.server.state.cfg
        language = str(payload.get("language") or cfg.language).strip().lower()
        if language in {"en", "nl"}:
            cfg.language = language
        log_level = str(payload.get("log_level") or cfg.log_level).strip().upper()
        if log_level in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            cfg.log_level = log_level
        if "screen_brightness_percent" in payload:
            cfg.screen_brightness_percent = max(10, min(100, int(payload["screen_brightness_percent"])))
        if "screen_timeout_seconds" in payload:
            cfg.screen_timeout_seconds = max(0, int(payload["screen_timeout_seconds"]))
        save_config(self.server.state.config_path, cfg)
        self.server.state.cfg = cfg
        self.server.state.command_handler("settings", payload)

    def _authorized(self) -> bool:
        expected = self.server.state.cfg.device_token
        if not expected:
            return False
        auth = str(self.headers.get("Authorization") or "")
        return auth.strip() == f"Bearer {expected}"

    def _device_auth_status(self) -> HTTPStatus:
        self.server.state.reload_config()
        cfg = self.server.state.cfg
        if not cfg.device_token:
            return HTTPStatus.UNAUTHORIZED
        auth = str(self.headers.get("Authorization") or "")
        if auth.strip() != f"Bearer {cfg.device_token}":
            return HTTPStatus.UNAUTHORIZED
        header_device_id = str(self.headers.get("X-DJConnect-Device-ID") or "").strip()
        if header_device_id and header_device_id != cfg.device_id:
            return HTTPStatus.FORBIDDEN
        return HTTPStatus.OK

    def _loopback_request(self) -> bool:
        host = self.client_address[0]
        return host in {"127.0.0.1", "::1"}

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        if length > MAX_REQUEST_BYTES:
            _LOGGER.warning("Rejected oversized Client API request: %s bytes", length)
            return {"_request_too_large": True}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except UnicodeDecodeError as exc:
            _LOGGER.warning("Client API request body is not valid UTF-8: %s", exc)
            return {}
        except json.JSONDecodeError as exc:
            _LOGGER.warning("Client API request body is not valid JSON: %s", exc)
            return {}
        _LOGGER.debug("Client API parsed JSON body keys=%s", sorted(data) if isinstance(data, dict) else type(data).__name__)
        return data if isinstance(data, dict) else {}

    def _write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(payload).encode("utf-8")
        _LOGGER.debug("Client API response path=%s status=%s keys=%s", self.path, int(status), sorted(payload))
        self.send_response(int(status))
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _write_html(self, payload: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(int(status))
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class ClientAPIServer(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, state: ClientAPIState):
        super().__init__(server_address, RequestHandlerClass)
        self.state = state


class ClientAPI:
    def __init__(self, state: ClientAPIState) -> None:
        self.state = state
        self.state.mdns_refresh_handler = self.refresh_mdns
        self.server: ClientAPIServer | None = None
        self.thread: threading.Thread | None = None
        self.zeroconf = None
        self.service_info = None

    def start(self) -> str:
        cfg = self.state.cfg
        try:
            self.server = ClientAPIServer((cfg.local_api_host, cfg.local_api_port), ClientAPIHandler, self.state)
        except OSError:
            _LOGGER.warning("Client API port %s unavailable; falling back to an ephemeral port", cfg.local_api_port)
            self.server = ClientAPIServer((cfg.local_api_host, 0), ClientAPIHandler, self.state)
        host, port = self.server.server_address
        advertised_host = _local_ip() if cfg.local_api_host in {"", "0.0.0.0"} else cfg.local_api_host
        local_url = f"http://{advertised_host}:{port}"
        cfg.local_api_port = int(port)
        cfg.local_url = local_url
        save_config(self.state.config_path, cfg)
        self.thread = threading.Thread(target=self.server.serve_forever, name="djconnect-client-api", daemon=True)
        self.thread.start()
        self.refresh_mdns()
        _LOGGER.info("Client API listening at %s", local_url)
        return local_url

    def stop(self) -> None:
        self._stop_mdns()
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None

    def _start_mdns(self, local_url: str) -> None:
        if self.zeroconf is not None:
            return
        if Zeroconf is None or ServiceInfo is None:
            _LOGGER.warning("zeroconf is not installed; mDNS discovery disabled")
            return
        cfg = self.state.cfg
        ip = _local_ip() if cfg.local_api_host in {"", "0.0.0.0"} else cfg.local_api_host
        service_type = "_djconnect._tcp.local."
        service_name = f"{cfg.device_name} {cfg.device_id}.{service_type}"
        properties = _mdns_properties(cfg, local_url)
        self.zeroconf = Zeroconf()
        self.service_info = ServiceInfo(
            service_type,
            service_name,
            addresses=[socket.inet_aton(ip)],
            port=cfg.local_api_port,
            properties=properties,
            server=f"{cfg.device_id}.local.",
        )
        self.zeroconf.register_service(self.service_info)
        _LOGGER.info("Advertised mDNS service %s on %s:%s", service_name, ip, cfg.local_api_port)

    def refresh_mdns(self) -> None:
        self.state.reload_config()
        cfg = self.state.cfg
        if cfg.paired and cfg.device_token:
            if self.zeroconf is None:
                _LOGGER.info("Skipping mDNS advertisement because DJConnect is paired with Home Assistant")
            else:
                _LOGGER.info("Stopping mDNS advertisement because DJConnect is paired with Home Assistant")
            self._stop_mdns()
            return
        if cfg.local_url:
            self._start_mdns(cfg.local_url)

    def _stop_mdns(self) -> None:
        if self.zeroconf is None or self.service_info is None:
            return
        self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()
        self.zeroconf = None
        self.service_info = None


def _capabilities() -> dict[str, bool]:
    return {
        "touch": True,
        "voice": False,
        "local_audio": False,
        "local_dj_response_endpoint": True,
    }


def _portal_settings(cfg: Config) -> dict[str, Any]:
    return {
        "language": cfg.language,
        "log_level": cfg.log_level,
        "screen_brightness_percent": cfg.screen_brightness_percent,
        "screen_timeout_seconds": cfg.screen_timeout_seconds,
        "update_channel": cfg.update_channel,
    }


def _portal_about(cfg: Config) -> dict[str, str]:
    return {
        "Versie": cfg.version,
        "Apparaatnaam": cfg.device_name,
        "Device ID": cfg.device_id,
        "Client adres": cfg.local_url,
        "Home Assistant": cfg.ha_url,
        "Home Assistant": "Gekoppeld" if cfg.paired else "Niet gekoppeld",
    }


def _mdns_properties(cfg: Config, local_url: str) -> dict[str, str]:
    return {
        "device_id": cfg.device_id,
        "client_type": CLIENT_TYPE,
        "version": cfg.version,
        "app_version": cfg.version,
        "device_name": cfg.device_name,
        "local_url": local_url,
        "pair_code": cfg.pairing_code,
        "paired": "true" if cfg.paired else "false",
    }


def _local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
        except OSError:
            return socket.gethostbyname(socket.gethostname())
