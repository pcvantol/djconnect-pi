from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import logging
import time
import requests

from .config import CLIENT_TYPE, Config

_LOGGER = logging.getLogger(__name__)


class DJConnectError(RuntimeError):
    pass


class BackendUnavailable(DJConnectError):
    pass


class UnsupportedBackendCapability(DJConnectError):
    pass


class StaleBackendAction(DJConnectError):
    pass


class AuthenticationError(DJConnectError):
    pass


class ProtocolVersionMismatch(DJConnectError):
    def __init__(self, client_version: str, ha_version: str, message: str = "") -> None:
        self.client_version = client_version
        self.ha_version = ha_version
        super().__init__(message or f"DJConnect version mismatch: client {client_version}, Home Assistant {ha_version}")


@dataclass
class Playback:
    title: str = ""
    artist: str = ""
    image_url: str = ""
    is_playing: bool = False
    volume: int = 50
    shuffle: bool = False
    repeat: str = "off"
    position_seconds: int = 0
    duration_seconds: int = 0
    output_device: str = ""
    output_devices: tuple[str, ...] = ()


@dataclass
class MusicBackendSummary:
    backend: str = ""
    name: str = ""
    available: bool = True
    revision: int = 0
    capabilities: dict[str, bool] | None = None
    target_player_id: str = ""
    target_player_name: str = ""
    error: str = ""


class HAClient:
    def __init__(self, cfg: Config, timeout: float = 4.0) -> None:
        self.cfg = cfg
        self.timeout = timeout

    def pair(self, pair_code: str) -> dict[str, Any]:
        payload = self._base_payload(pair_code=pair_code, ha_pairing_status="pending")
        url = self._url("/api/djconnect/pair")
        _LOGGER.debug("POST %s for device_id=%s client_type=%s", url, self.cfg.device_id, CLIENT_TYPE)
        started = time.monotonic()
        response = requests.post(url, json=payload, timeout=self.timeout)
        _LOGGER.debug("POST %s returned HTTP %s in %.0fms", url, response.status_code, _elapsed_ms(started))
        data = self._json(response)
        self.update_backend_summary(data)
        self._validate_ha_version(data)
        token = data.get("device_token") or data.get("token")
        if token:
            self.cfg.device_token = str(token)
            self.cfg.paired = True
        return data

    def status(self, playback: Playback | None = None, queue_items: list[dict[str, object]] | None = None) -> dict[str, Any]:
        payload = self._base_payload(ha_pairing_status="paired" if self.cfg.paired else "pending")
        if playback is not None:
            output_devices = list(playback.output_devices)
            playback_payload = {
                "has_playback": bool(playback.title or playback.artist or playback.image_url or playback.duration_seconds),
                "title": playback.title,
                "track_name": playback.title,
                "artist": playback.artist,
                "image_url": playback.image_url,
                "is_playing": playback.is_playing,
                "volume": playback.volume,
                "shuffle": playback.shuffle,
                "repeat_state": playback.repeat,
                "position": playback.position_seconds,
                "duration": playback.duration_seconds,
                "output_device": playback.output_device,
                "output_devices": output_devices,
            }
            if playback.output_device:
                playback_payload["device"] = {"id": playback.output_device, "name": playback.output_device}
            payload.update(
                {
                    "last_track": playback.title,
                    "artist": playback.artist,
                    "volume": playback.volume,
                    "shuffle": playback.shuffle,
                    "repeat_state": playback.repeat,
                    "spotify_status": "playing" if playback.is_playing else "paused",
                    "position": playback.position_seconds,
                    "duration": playback.duration_seconds,
                    "playback": playback_payload,
                    "output_device": playback.output_device,
                    "output_devices": output_devices,
                    "available_outputs": [{"id": name, "name": name} for name in output_devices],
                }
            )
            if playback.output_device:
                payload["sound_output"] = playback.output_device
                payload["output"] = playback.output_device
        if queue_items is not None:
            payload["queue"] = {"items": queue_items}
        url = self._url("/api/djconnect/status")
        _LOGGER.debug("POST %s paired=%s playback_included=%s", url, self.cfg.paired, playback is not None)
        started = time.monotonic()
        response = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        _LOGGER.debug("POST %s returned HTTP %s in %.0fms", url, response.status_code, _elapsed_ms(started))
        data = self._json(response)
        self.update_backend_summary(data)
        self._validate_ha_version(data)
        return data

    def command(self, command: str, **payload: Any) -> dict[str, Any]:
        body = self._base_payload(command=command, **payload)
        url = self._url("/api/djconnect/command")
        _LOGGER.debug(
            "POST %s command=%s client_type=%s device_id=%s requested_limit=%s payload_keys=%s",
            url,
            command,
            CLIENT_TYPE,
            self.cfg.device_id,
            payload.get("limit", ""),
            sorted(payload),
        )
        started = time.monotonic()
        response = requests.post(
            url,
            json=body,
            headers=self._headers(),
            timeout=self.timeout,
        )
        _LOGGER.debug("POST %s command=%s returned HTTP %s in %.0fms", url, command, response.status_code, _elapsed_ms(started))
        data = self._json(response)
        _LOGGER.debug("Decoded command=%s response_shape=%s", command, _response_shape(data))
        self.update_backend_summary(data)
        self._validate_ha_version(data)
        return data

    def ask_dj_history(self, since_revision: int = 0) -> dict[str, Any]:
        url = self._url(f"/api/djconnect/ask_dj/history?since_revision={max(0, int(since_revision))}")
        _LOGGER.debug("GET %s client_type=%s device_id=%s", url, CLIENT_TYPE, self.cfg.device_id)
        started = time.monotonic()
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        _LOGGER.debug("GET %s returned HTTP %s in %.0fms", url, response.status_code, _elapsed_ms(started))
        data = self._json(response)
        self.update_backend_summary(data)
        self._validate_ha_version(data)
        return data

    def ask_dj_message(self, text: str, client_message_id: str) -> dict[str, Any]:
        body = self._ask_dj_payload(
            text=text,
            client_message_id=client_message_id,
            audio_response="auto",
        )
        url = self._url("/api/djconnect/ask_dj/message")
        _LOGGER.debug("POST %s client_type=%s device_id=%s client_message_id=%s", url, CLIENT_TYPE, self.cfg.device_id, client_message_id)
        started = time.monotonic()
        response = requests.post(url, json=body, headers=self._headers(), timeout=self.timeout)
        _LOGGER.debug("POST %s returned HTTP %s in %.0fms", url, response.status_code, _elapsed_ms(started))
        data = self._json(response)
        self.update_backend_summary(data)
        self._validate_ha_version(data)
        return data

    def ask_dj_clear_history(self) -> dict[str, Any]:
        body = self._ask_dj_payload()
        url = self._url("/api/djconnect/ask_dj/history/clear")
        _LOGGER.debug("POST %s client_type=%s device_id=%s", url, CLIENT_TYPE, self.cfg.device_id)
        started = time.monotonic()
        response = requests.post(url, json=body, headers=self._headers(), timeout=self.timeout)
        _LOGGER.debug("POST %s returned HTTP %s in %.0fms", url, response.status_code, _elapsed_ms(started))
        data = self._json(response)
        self.update_backend_summary(data)
        self._validate_ha_version(data)
        return data

    def ask_dj_action(self, action: dict[str, Any]) -> dict[str, Any]:
        command = str(action.get("command") or "").strip()
        kind = str(action.get("kind") or "").strip().lower()
        action_style = str(action.get("action_style") or "").strip().lower()
        if not command:
            if kind == "confirmation" or action_style == "confirmation":
                command = "ask_dj_followup_response"
            elif kind == "output":
                command = "set_output"
            elif kind == "control":
                command = str(action.get("action") or action.get("type") or "control").strip()
            else:
                command = "ask_dj_play_recommendation"
        value: Any = action.get("value") if command == "set_output" and kind == "output" else action
        return self.command(command, value=value)

    def playback_from_status(self, data: dict[str, Any]) -> Playback:
        playback = data.get("playback") if isinstance(data.get("playback"), dict) else data
        output_device_source = (
            playback.get("output_devices")
            or playback.get("devices")
            or playback.get("available_devices")
            or playback.get("outputs")
            or playback.get("device")
            or playback.get("active_device")
            or playback.get("current_device")
            or data.get("output_devices")
            or data.get("devices")
            or data.get("available_devices")
            or data.get("outputs")
            or data.get("device")
            or data.get("active_device")
            or data.get("current_device")
        )
        output_devices = _string_list(output_device_source)
        output_device = _active_output_device(
            output_device_source,
            _output_device_name(
                playback.get("output_device")
                or playback.get("device_name")
                or playback.get("active_device")
                or playback.get("current_device")
                or playback.get("device")
                or playback.get("source")
                or data.get("output_device")
                or data.get("device_name")
                or data.get("active_device")
                or data.get("current_device")
                or data.get("device")
                or data.get("source")
            ),
        )
        backend_available = data.get("backend_available")
        if data.get("success") is False or backend_available is False:
            _LOGGER.debug(
                "Playback status reports backend_available=%s error=%s message=%s",
                backend_available,
                data.get("error", ""),
                data.get("message", ""),
            )
        return Playback(
            title=str(playback.get("title") or playback.get("track") or playback.get("track_name") or playback.get("last_track") or ""),
            artist=str(playback.get("artist") or playback.get("artists") or playback.get("album_artist") or ""),
            image_url=_image_url_from(playback),
            is_playing=bool(playback.get("is_playing") or playback.get("playing")),
            volume=int(playback.get("volume") or playback.get("volume_percent") or 50),
            shuffle=bool(playback.get("shuffle")),
            repeat=str(playback.get("repeat_state") or playback.get("repeat") or "off"),
            position_seconds=_seconds_from_playback(
                playback,
                "position",
                "position_seconds",
                "progress",
                "progress_seconds",
                "elapsed",
                "elapsed_seconds",
            ),
            duration_seconds=_seconds_from_playback(
                playback,
                "duration",
                "duration_seconds",
                "length",
                "length_seconds",
                "track_duration",
                "track_duration_seconds",
            ),
            output_device=output_device,
            output_devices=tuple(output_devices),
        )

    def update_backend_summary(self, data: dict[str, Any]) -> MusicBackendSummary:
        summary = music_backend_summary_from(data)
        if not _has_backend_summary(data):
            return summary
        self.cfg.music_backend = summary.backend
        self.cfg.music_backend_name = summary.name
        self.cfg.music_backend_available = summary.available
        self.cfg.music_backend_revision = summary.revision
        self.cfg.music_backend_capabilities = dict(summary.capabilities or {})
        target_player: dict[str, str] = {}
        if summary.target_player_id:
            target_player["id"] = summary.target_player_id
        if summary.target_player_name:
            target_player["name"] = summary.target_player_name
        self.cfg.music_target_player = target_player
        self.cfg.music_backend_error = summary.error
        return summary

    def _base_payload(self, **extra: Any) -> dict[str, Any]:
        return {
            "device_id": self.cfg.device_id,
            "device_name": self.cfg.device_name,
            "client_type": CLIENT_TYPE,
            "version": self.cfg.version,
            "app_version": self.cfg.version,
            "firmware": self.cfg.version,
            "local_url": self.cfg.local_url,
            "language": self.cfg.language,
            "capabilities": {
                "touch": True,
                "voice": False,
                "voice_supported": False,
                "tts_supported": False,
                "local_audio": False,
                "local_audio_supported": False,
                "local_dj_response_endpoint": False,
                "ask_dj_supported": True,
                "ask_dj_mode": "text_actions",
                "ask_dj_free_input_supported": True,
                "ask_dj_actions_supported": True,
            },
            **extra,
        }

    def _ask_dj_payload(self, **extra: Any) -> dict[str, Any]:
        identity = {
            "client_type": CLIENT_TYPE,
            "device_id": self.cfg.device_id,
            "device_name": self.cfg.device_name,
        }
        return {
            "identity": identity,
            "client_id": self.cfg.device_id,
            "device_id": self.cfg.device_id,
            "device_name": self.cfg.device_name,
            "client_type": CLIENT_TYPE,
            "version": self.cfg.version,
            "app_version": self.cfg.version,
            "language": self.cfg.language,
            **extra,
        }

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-DJConnect-Device-ID": self.cfg.device_id,
            "X-DJConnect-Client-Type": CLIENT_TYPE,
        }
        if self.cfg.device_token:
            headers["Authorization"] = f"Bearer {self.cfg.device_token}"
        return headers

    def _url(self, path: str) -> str:
        if not self.cfg.ha_url:
            raise DJConnectError("Home Assistant URL is not configured")
        return f"{self.cfg.ha_url.rstrip('/')}{path}"

    def _json(self, response: requests.Response) -> dict[str, Any]:
        if response.status_code == 426:
            _LOGGER.warning("Home Assistant protocol mismatch HTTP 426")
            raise ProtocolVersionMismatch(self.cfg.version, "unknown", f"Protocol version mismatch: {response.text}")
        data: dict[str, Any] = {}
        if response.content:
            try:
                parsed = response.json()
            except ValueError as exc:
                _LOGGER.warning(
                    "Home Assistant returned invalid JSON: status=%s bytes=%s error=%s",
                    response.status_code,
                    len(response.content),
                    exc,
                )
                raise DJConnectError("Home Assistant returned invalid JSON") from exc
            if not isinstance(parsed, dict):
                _LOGGER.warning("Home Assistant returned non-object JSON: %s", type(parsed).__name__)
                raise DJConnectError("Home Assistant returned non-object JSON")
            data = parsed
        if response.status_code >= 400:
            error = str(data.get("error") or data.get("message") or response.text or f"HTTP {response.status_code}")
            _LOGGER.warning("Home Assistant returned HTTP %s: %s", response.status_code, error)
            if response.status_code in {401, 403, 404}:
                raise AuthenticationError(error)
            raise DJConnectError(f"Home Assistant returned HTTP {response.status_code}: {error}")
        if not response.content:
            _LOGGER.warning("Home Assistant returned empty HTTP %s response body; this violates the DJConnect JSON contract", response.status_code)
            raise DJConnectError("Home Assistant returned empty JSON response")
        if data.get("success") is False and str(data.get("error") or "") in {
            "unauthorized",
            "forbidden",
            "not_configured",
            "stale_pairing",
            "stale_token",
            "invalid_token",
        }:
            error = str(data.get("message") or data.get("error") or "authentication failed")
            _LOGGER.warning("Home Assistant rejected pairing/auth state: error=%s", data.get("error"))
            raise AuthenticationError(error)
        if data.get("success") is False and data.get("backend_available") is False:
            error = str(data.get("error") or "playback backend unavailable")
            message = str(data.get("message") or error)
            _LOGGER.warning("Home Assistant playback backend unavailable: error=%s message=%s", error, message)
            raise BackendUnavailable(error)
        if data.get("success") is False and data.get("error") == "unsupported_backend_capability":
            capability = str(data.get("capability") or "unknown")
            backend = str(data.get("backend") or data.get("music_backend") or "unknown")
            message = str(data.get("message") or f"Backend {backend} does not support {capability}")
            _LOGGER.warning("Home Assistant backend capability unsupported: backend=%s capability=%s message=%s", backend, capability, message)
            raise UnsupportedBackendCapability(message)
        if data.get("success") is False and str(data.get("error") or "") in {
            "music_backend_revision_mismatch",
            "stale_backend_action",
            "stale_music_backend_action",
            "stale_music_backend_revision",
        }:
            message = str(data.get("message") or "Music backend changed; ask DJ again before using this action.")
            _LOGGER.warning("Home Assistant rejected stale backend action: error=%s message=%s", data.get("error"), message)
            raise StaleBackendAction(message)
        _LOGGER.debug("Home Assistant JSON response keys=%s", sorted(data))
        return data

    def _validate_ha_version(self, data: dict[str, Any]) -> None:
        ha_version = str(data.get("ha_version") or data.get("ha_major_minor") or "").strip()
        if not ha_version:
            return
        if _compatible_ha_version(self.cfg.version, ha_version):
            return
        _LOGGER.warning("Home Assistant version %s is incompatible with client %s", ha_version, self.cfg.version)
        raise ProtocolVersionMismatch(self.cfg.version, ha_version)


def _major_minor(version: str) -> tuple[int, int] | None:
    parts = version.strip().removeprefix("v").split(".")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _elapsed_ms(started: float) -> float:
    return (time.monotonic() - started) * 1000


def _seconds_from_playback(playback: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = playback.get(key)
        if value is None or value == "":
            value = playback.get(f"{key}_ms")
            if value is not None and value != "":
                return max(0, int(float(value) / 1000))
            continue
        return max(0, int(float(value)))
    return 0


def _image_url_from(item: dict[str, Any]) -> str:
    for key in (
        "image_url",
        "imageUrl",
        "album_image_url",
        "albumImageUrl",
        "album_art_url",
        "albumArtUrl",
        "art_url",
        "artUrl",
        "artwork",
        "artwork_url",
        "artworkUrl",
        "media_image_url",
        "mediaImageUrl",
        "entity_picture",
        "thumbnail_url",
        "thumbnailUrl",
        "thumbnail",
        "cover_url",
        "coverUrl",
        "cover",
        "image",
        "picture",
        "images",
        "artworks",
        "thumbnails",
        "url",
    ):
        url = _image_url_value(item.get(key))
        if url:
            return url
    for key in ("album", "track", "playlist", "show", "episode", "item", "metadata"):
        nested = item.get(key)
        if isinstance(nested, dict):
            url = _image_url_from(nested)
            if url:
                return url
    return ""


def _image_url_value(value: Any) -> str:
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("http://", "https://", "file://")):
            return text
        return ""
    if isinstance(value, dict):
        return _image_url_from(value)
    if isinstance(value, list):
        candidates = [item for item in value if isinstance(item, dict)]
        if candidates:
            candidates.sort(key=lambda item: int(item.get("width") or item.get("height") or 0), reverse=True)
            for candidate in candidates:
                url = _image_url_from(candidate)
                if url:
                    return url
        for item in value:
            url = _image_url_value(item)
            if url:
                return url
    return ""


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            if isinstance(item, dict):
                name = item.get("name") or item.get("device_name") or item.get("label") or item.get("id")
                if name:
                    result.append(str(name))
            elif item:
                result.append(str(item))
        return result
    if isinstance(value, dict):
        name = value.get("name") or value.get("device_name") or value.get("label")
        if name:
            return [str(name)]
        return _string_list(list(value.values()))
    if value:
        return [str(value)]
    return []


def _output_device_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("device_name") or value.get("label") or value.get("id") or "").strip()
    if value:
        return str(value).strip()
    return ""


def _active_output_device(devices: Any, explicit: str) -> str:
    explicit = explicit.strip()
    explicit_casefold = explicit.casefold()
    active_name = ""
    id_to_name: dict[str, str] = {}
    names: list[str] = []
    if isinstance(devices, list):
        for item in devices:
            if isinstance(item, dict):
                name = str(item.get("name") or item.get("device_name") or item.get("label") or item.get("id") or "").strip()
                device_id = str(item.get("id") or item.get("device_id") or item.get("value") or "").strip()
                if name:
                    names.append(name)
                for key in (device_id, name):
                    if key:
                        id_to_name[key.casefold()] = name or key
                if item.get("is_active") or item.get("active") or item.get("selected") or item.get("current"):
                    active_name = name or device_id
            elif item:
                names.append(str(item).strip())
    elif isinstance(devices, dict):
        return _active_output_device(list(devices.values()), explicit)

    if explicit:
        if explicit_casefold in id_to_name:
            return id_to_name[explicit_casefold]
        for name in names:
            if explicit_casefold == name.casefold():
                return name
        return explicit
    return active_name


def _response_shape(data: dict[str, Any]) -> dict[str, Any]:
    shape: dict[str, Any] = {
        "keys": sorted(data),
        "success": data.get("success"),
        "backend_available": data.get("backend_available"),
    }
    for key in ("playlists", "items", "queue", "devices", "outputs"):
        value = data.get(key)
        if isinstance(value, list):
            shape[f"{key}_count"] = len(value)
        elif isinstance(value, dict):
            shape[f"{key}_keys"] = sorted(value)
    for container_key in ("data", "result"):
        container = data.get(container_key)
        if isinstance(container, dict):
            shape[f"{container_key}_keys"] = sorted(container)
            for key in ("playlists", "items", "queue", "devices", "outputs"):
                value = container.get(key)
                if isinstance(value, list):
                    shape[f"{container_key}.{key}_count"] = len(value)
    if data.get("error") or data.get("message"):
        shape["error"] = data.get("error", "")
        shape["message"] = data.get("message", "")
    return shape


def music_backend_summary_from(data: dict[str, Any]) -> MusicBackendSummary:
    target = data.get("music_target_player") if isinstance(data.get("music_target_player"), dict) else {}
    capabilities = data.get("music_backend_capabilities") if isinstance(data.get("music_backend_capabilities"), dict) else {}
    return MusicBackendSummary(
        backend=str(data.get("music_backend") or ""),
        name=str(data.get("music_backend_name") or data.get("music_backend") or ""),
        available=bool(data.get("music_backend_available", data.get("backend_available", True))),
        revision=_int_value(data.get("music_backend_revision"), 0),
        capabilities={str(key): bool(value) for key, value in capabilities.items()},
        target_player_id=str(target.get("id") or ""),
        target_player_name=str(target.get("name") or ""),
        error=str(data.get("music_backend_error") or ""),
    )


def _has_backend_summary(data: dict[str, Any]) -> bool:
    return any(
        key in data
        for key in (
            "music_backend",
            "music_backend_name",
            "music_backend_available",
            "music_backend_revision",
            "music_backend_capabilities",
            "music_target_player",
            "music_backend_error",
        )
    )


def _int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _compatible_ha_version(client_version: str, ha_version: str) -> bool:
    client_major_minor = _major_minor(client_version)
    ha_major_minor = _major_minor(ha_version)
    if client_major_minor is None or ha_major_minor is None:
        return False
    return client_major_minor == ha_major_minor
