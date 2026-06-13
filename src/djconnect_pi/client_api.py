from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
import json
import logging
import socket
import threading

from .config import CLIENT_TYPE, Config, load_config, save_config

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
        pair_handler: Callable[[], None],
        forget_handler: Callable[[], None],
    ) -> None:
        self.cfg = cfg
        self.config_path = config_path
        self.playback_provider = playback_provider
        self.command_handler = command_handler
        self.dj_response_handler = dj_response_handler
        self.pair_handler = pair_handler
        self.forget_handler = forget_handler

    def reload_config(self) -> None:
        self.cfg = load_config(self.config_path)


class ClientAPIHandler(BaseHTTPRequestHandler):
    server: "ClientAPIServer"

    def log_message(self, fmt: str, *args: object) -> None:
        _LOGGER.info("Client API " + fmt, *args)

    def do_GET(self) -> None:
        _LOGGER.debug("Client API GET %s", self.path)
        if self.path == "/api/device/info":
            self._write_json(self._info())
            return
        if self.path == "/api/device/pairing-info":
            self._write_json(self._pairing_info())
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
        if self.path == "/api/device/forget":
            if not self._authorized():
                _LOGGER.warning("Client API unauthorized forget request")
                self._write_json({"success": False, "error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
                return
            _LOGGER.info("Client API forget pairing request for device_id=%s", self.server.state.cfg.device_id)
            self.server.state.forget_handler()
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
        cfg.device_token = token
        cfg.ha_url = ha_url
        cfg.paired = True
        save_config(self.server.state.config_path, cfg)
        self.server.state.pair_handler()
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

    def _authorized(self) -> bool:
        expected = self.server.state.cfg.device_token
        if not expected:
            return False
        auth = str(self.headers.get("Authorization") or "")
        return auth.strip() == f"Bearer {expected}"

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


class ClientAPIServer(ThreadingHTTPServer):
    def __init__(self, server_address, RequestHandlerClass, state: ClientAPIState):
        super().__init__(server_address, RequestHandlerClass)
        self.state = state


class ClientAPI:
    def __init__(self, state: ClientAPIState) -> None:
        self.state = state
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
        self._start_mdns(local_url)
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


def _mdns_properties(cfg: Config, local_url: str) -> dict[str, str]:
    return {
        "device_id": cfg.device_id,
        "client_type": CLIENT_TYPE,
        "version": cfg.version,
        "device_name": cfg.device_name,
        "local_url": local_url,
    }


def _local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect(("8.8.8.8", 80))
            return str(sock.getsockname()[0])
        except OSError:
            return socket.gethostbyname(socket.gethostname())
