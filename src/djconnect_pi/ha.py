from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests

from .config import CLIENT_TYPE, Config


class DJConnectError(RuntimeError):
    pass


@dataclass
class Playback:
    title: str = "Nothing playing"
    artist: str = ""
    image_url: str = ""
    is_playing: bool = False
    volume: int = 50
    shuffle: bool = False
    repeat: str = "off"


class HAClient:
    def __init__(self, cfg: Config, timeout: float = 8.0) -> None:
        self.cfg = cfg
        self.timeout = timeout

    def pair(self, pair_code: str) -> dict[str, Any]:
        payload = self._base_payload(pair_code=pair_code, ha_pairing_status="pending")
        response = requests.post(self._url("/api/djconnect/pair"), json=payload, timeout=self.timeout)
        data = self._json(response)
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
                }
            )
        response = requests.post(
            self._url("/api/djconnect/status"),
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._json(response)

    def command(self, command: str, **payload: Any) -> dict[str, Any]:
        body = {"command": command, **payload}
        response = requests.post(
            self._url("/api/djconnect/command"),
            json=body,
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._json(response)

    def playback_from_status(self, data: dict[str, Any]) -> Playback:
        playback = data.get("playback") if isinstance(data.get("playback"), dict) else data
        return Playback(
            title=str(playback.get("title") or playback.get("track") or playback.get("last_track") or "Nothing playing"),
            artist=str(playback.get("artist") or playback.get("artists") or ""),
            image_url=str(playback.get("image_url") or playback.get("album_image_url") or ""),
            is_playing=bool(playback.get("is_playing") or playback.get("playing")),
            volume=int(playback.get("volume") or playback.get("volume_percent") or 50),
            shuffle=bool(playback.get("shuffle")),
            repeat=str(playback.get("repeat_state") or playback.get("repeat") or "off"),
        )

    def _base_payload(self, **extra: Any) -> dict[str, Any]:
        return {
            "device_id": self.cfg.device_id,
            "device_name": self.cfg.device_name,
            "client_type": CLIENT_TYPE,
            "version": self.cfg.version,
            "firmware": self.cfg.version,
            "capabilities": {
                "touch": True,
                "voice": False,
                "local_audio": False,
                "local_dj_response_endpoint": False,
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
            raise DJConnectError(f"Protocol version mismatch: {response.text}")
        if response.status_code >= 400:
            raise DJConnectError(f"Home Assistant returned {response.status_code}: {response.text}")
        if not response.content:
            return {}
        data = response.json()
        if not isinstance(data, dict):
            raise DJConnectError("Home Assistant returned non-object JSON")
        return data

