from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import logging
import requests

from .config import CLIENT_TYPE, Config

_LOGGER = logging.getLogger(__name__)


class DJConnectError(RuntimeError):
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


class HAClient:
    def __init__(self, cfg: Config, timeout: float = 8.0) -> None:
        self.cfg = cfg
        self.timeout = timeout

    def pair(self, pair_code: str) -> dict[str, Any]:
        payload = self._base_payload(pair_code=pair_code, ha_pairing_status="pending")
        url = self._url("/api/djconnect/pair")
        _LOGGER.debug("POST %s for device_id=%s client_type=%s", url, self.cfg.device_id, CLIENT_TYPE)
        response = requests.post(url, json=payload, timeout=self.timeout)
        _LOGGER.debug("POST %s returned HTTP %s", url, response.status_code)
        data = self._json(response)
        self._validate_ha_version(data)
        token = data.get("device_token") or data.get("token")
        if token:
            self.cfg.device_token = str(token)
            self.cfg.paired = True
        return data

    def status(self, playback: Playback | None = None) -> dict[str, Any]:
        payload = self._base_payload(ha_pairing_status="paired" if self.cfg.paired else "pending")
        if playback is not None:
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
                }
            )
        url = self._url("/api/djconnect/status")
        _LOGGER.debug("POST %s paired=%s playback_included=%s", url, self.cfg.paired, playback is not None)
        response = requests.post(
            url,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        _LOGGER.debug("POST %s returned HTTP %s", url, response.status_code)
        data = self._json(response)
        self._validate_ha_version(data)
        return data

    def command(self, command: str, **payload: Any) -> dict[str, Any]:
        body = self._base_payload(command=command, **payload)
        url = self._url("/api/djconnect/command")
        _LOGGER.debug("POST %s command=%s payload_keys=%s", url, command, sorted(payload))
        response = requests.post(
            url,
            json=body,
            headers=self._headers(),
            timeout=self.timeout,
        )
        _LOGGER.debug("POST %s command=%s returned HTTP %s", url, command, response.status_code)
        data = self._json(response)
        self._validate_ha_version(data)
        return data

    def playback_from_status(self, data: dict[str, Any]) -> Playback:
        playback = data.get("playback") if isinstance(data.get("playback"), dict) else data
        output_devices = _string_list(
            playback.get("output_devices")
            or playback.get("devices")
            or playback.get("available_devices")
            or data.get("output_devices")
            or data.get("devices")
            or data.get("available_devices")
        )
        return Playback(
            title=str(playback.get("title") or playback.get("track") or playback.get("last_track") or ""),
            artist=str(playback.get("artist") or playback.get("artists") or ""),
            image_url=str(
                playback.get("image_url")
                or playback.get("album_image_url")
                or playback.get("album_art_url")
                or playback.get("media_image_url")
                or playback.get("entity_picture")
                or ""
            ),
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
            output_device=str(
                playback.get("output_device")
                or playback.get("device_name")
                or playback.get("active_device")
                or playback.get("source")
                or (output_devices[0] if output_devices else "")
            ),
            output_devices=tuple(output_devices),
        )

    def _base_payload(self, **extra: Any) -> dict[str, Any]:
        return {
            "device_id": self.cfg.device_id,
            "device_name": self.cfg.device_name,
            "client_type": CLIENT_TYPE,
            "version": self.cfg.version,
            "firmware": self.cfg.version,
            "local_url": self.cfg.local_url,
            "capabilities": {
                "touch": True,
                "voice": False,
                "local_audio": False,
                "local_dj_response_endpoint": True,
            },
            **extra,
        }

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-DJConnect-Device-ID": self.cfg.device_id,
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
        if response.status_code >= 400:
            _LOGGER.warning("Home Assistant returned HTTP %s", response.status_code)
            raise DJConnectError(f"Home Assistant returned {response.status_code}: {response.text}")
        if not response.content:
            _LOGGER.debug("Home Assistant returned empty response body")
            return {}
        try:
            data = response.json()
        except ValueError as exc:
            _LOGGER.warning(
                "Home Assistant returned invalid JSON: status=%s bytes=%s error=%s",
                response.status_code,
                len(response.content),
                exc,
            )
            raise DJConnectError("Home Assistant returned invalid JSON") from exc
        if not isinstance(data, dict):
            _LOGGER.warning("Home Assistant returned non-object JSON: %s", type(data).__name__)
            raise DJConnectError("Home Assistant returned non-object JSON")
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
        return _string_list(list(value.values()))
    if value:
        return [str(value)]
    return []


def _compatible_ha_version(client_version: str, ha_version: str) -> bool:
    client_major_minor = _major_minor(client_version)
    ha_major_minor = _major_minor(ha_version)
    if client_major_minor is None or ha_major_minor is None:
        return False
    return client_major_minor == ha_major_minor
