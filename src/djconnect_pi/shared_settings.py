"""Private settings3 consumer. Reads never initialize or repair server choices."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections.abc import Callable
from copy import deepcopy
from threading import RLock
from typing import Any
from uuid import UUID

import requests

FIELDS = frozenset(
    {"persona", "voice", "gender", "mood", "presence", "announcement_output"}
)
CHOICES = {
    "persona": ("home_dj", "radio_dj", "club_dj", "festival_dj"),
    "gender": ("default", "female", "male"),
    "mood": ("chill", "groove", "energy", "party"),
    "presence": ("music_only", "occasional", "balanced", "talkative", "presenter"),
    "announcement_output": ("client_device", "both", "ha_speaker", "text_only"),
}


class SettingsError(Exception):
    """Closed presentation category; never include private response bodies."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def operation_id() -> str:
    """UUIDv7 on the supported Python 3.11 runtime."""
    return str(
        UUID(
            int=(int(time.time() * 1000) << 80)
            | (7 << 76)
            | (secrets.randbits(12) << 64)
            | (2 << 62)
            | secrets.randbits(62)
        )
    )


def selection(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise SettingsError("invalid")
    for field, values in CHOICES.items():
        if not isinstance(value[field], str) or value[field] not in values:
            raise SettingsError("invalid")
    voice = value["voice"]
    if not isinstance(voice, dict):
        raise SettingsError("invalid")
    if voice.get("kind") == "provider_default":
        if set(voice) != {"kind"}:
            raise SettingsError("invalid")
    elif voice.get("kind") == "provider_voice":
        if set(voice) != {"kind", "provider_id", "voice_id"}:
            raise SettingsError("invalid")
        for field in ("provider_id", "voice_id"):
            s = voice[field]
            if (
                not isinstance(s, str)
                or not 0 < len(s) <= 128
                or any(ord(c) < 32 or ord(c) == 127 for c in s)
            ):
                raise SettingsError("invalid")
    else:
        raise SettingsError("invalid")
    return deepcopy(value)


def snapshot_response(data: Any) -> dict[str, Any]:
    if (
        not isinstance(data, dict)
        or data.get("success") is not True
        or type(data.get("contract_version")) is not int
        or data["contract_version"] != 3
    ):
        raise SettingsError("unsupported")
    if not isinstance(data.get("binding"), str) or not data["binding"]:
        raise SettingsError("invalid")
    snap = data.get("snapshot")
    if (
        not isinstance(snap, dict)
        or type(snap.get("defaults_revision")) is not int
        or snap["defaults_revision"] < 0
    ):
        raise SettingsError("invalid")
    selection(snap.get("defaults"))
    session = snap.get("session")
    if session is not None:
        if not isinstance(session, dict) or any(
            not isinstance(session.get(k), str) or not session[k]
            for k in ("session_id", "generation")
        ):
            raise SettingsError("invalid")
        if type(session.get("revision")) is not int or session["revision"] < 0:
            raise SettingsError("invalid")
        if session.get("settings") is not None:
            selection(session["settings"])
        elif session.get("selection_required") is not True:
            raise SettingsError("invalid")
    allowed = data.get("allowed_values")
    if not isinstance(allowed, dict) or any(
        not isinstance(allowed.get(k), list) for k in CHOICES
    ):
        raise SettingsError("invalid")
    if not isinstance(allowed.get("voice"), dict) or not isinstance(
        allowed["voice"].get("voices"), list
    ):
        raise SettingsError("invalid")
    writable = data.get("writable_fields")
    if not isinstance(writable, list) or any(
        not isinstance(k, str) or k not in FIELDS for k in writable
    ):
        raise SettingsError("invalid")
    return deepcopy(data)


class SharedSettingsClient:
    """Serialized RAM-only owner state; no Profile preferences in local config."""

    def __init__(self, config: Callable, timeout: float = 4.0) -> None:
        self.config = config
        self.timeout = timeout
        self._lock = RLock()
        self._context: tuple = ()
        self._snapshot: dict | None = None
        self.managed = False
        self._pending: dict | None = None
        self._unknown = False

    def context(self) -> tuple:
        c = self.config()
        return (
            c.ha_url,
            c.device_id,
            c.device_token,
            getattr(c, "active_profile_id", ""),
        )

    def _identity(self) -> dict:
        return {
            "contract_version": 3,
            "device_id": self._context[1],
            "client_type": "raspberry_pi",
        }

    def _request(
        self, method: str, suffix: str = "", payload: dict | None = None
    ) -> dict:
        context = self._context
        if not context or context != self.context():
            raise SettingsError("reload")
        ha_url, _, token, _ = context
        if not self.config().paired or not token or not ha_url:
            raise SettingsError("denied")
        url = ha_url.rstrip("/") + "/api/djconnect/v1/profile/settings" + suffix
        headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
        kwargs = {"params" if method == "get" else "json": payload or self._identity()}
        try:
            response = getattr(requests, method)(
                url, headers=headers, timeout=self.timeout, **kwargs
            )
        except requests.RequestException:
            raise SettingsError("offline") from None
        if response.status_code in (401, 403):
            raise SettingsError("denied")
        if response.status_code in (404, 405, 426):
            if response.status_code == 426:
                self.managed = True
            raise SettingsError("unsupported")
        if response.status_code == 409:
            raise SettingsError("conflict")
        if response.status_code >= 500:
            raise SettingsError("offline")
        if response.status_code >= 400:
            raise SettingsError("rejected")
        try:
            data = response.json()
        except ValueError:
            raise SettingsError(
                "uncertain" if method == "patch" else "invalid"
            ) from None
        if not isinstance(data, dict) or data.get("success") is not True:
            raise SettingsError("uncertain" if method == "patch" else "invalid")
        return data

    def read(self) -> dict:
        with self._lock:
            context = self.context()
            if context != self._context:
                self._snapshot = None
                if context[:3] != self._context[:3]:
                    self.managed = False
                self._context = context
                self._pending = None
                self._unknown = False
            try:
                if self._pending is not None:
                    self._recover_pending()
                data = snapshot_response(self._request("get"))
                if context != self.context():
                    raise SettingsError("denied")
                self._snapshot = data
                self.managed = True
                return self.projection()
            except SettingsError:
                self._snapshot = None
                raise

    def _recover_pending(self) -> None:
        pending = self._pending
        if pending is None:
            return
        receipt = self._request(
            "post",
            "/operation",
            {
                **self._identity(),
                "binding": pending["binding"],
                "operation_id": pending["operation_id"],
            },
        )
        if receipt.get("contract_version") != 3:
            raise SettingsError("uncertain")
        phase = receipt.get("phase")
        if phase == "accepted":
            original = receipt.get("receipt", {})
            if (
                original.get("operation_id") != pending["operation_id"]
                or original.get("accepted") is not True
            ):
                raise SettingsError("uncertain")
            self._pending = None
        elif phase == "unknown":
            # The owner reports expired absence, not rejection. Never replay it.
            self._pending = None
            self._unknown = True
        elif phase != "not_accepted":
            raise SettingsError("uncertain")

    def edit_token(self) -> str:
        return hashlib.sha256(
            json.dumps(
                {
                    k: self._snapshot[k]
                    for k in (
                        "binding",
                        "snapshot",
                        "voice_revision",
                        "allowed_values",
                        "writable_fields",
                    )
                    if k in self._snapshot
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

    def update(self, patch: dict, edit_token: str) -> dict:
        with self._lock:
            if self._pending is not None:
                raise SettingsError("uncertain")
            if self._snapshot is None or self.context() != self._context:
                raise SettingsError("reload")
            if edit_token != self.edit_token():
                raise SettingsError("conflict")
            data = self._snapshot
            if (
                not isinstance(patch, dict)
                or not patch
                or set(patch) - set(data["writable_fields"])
            ):
                raise SettingsError("rejected")
            snap = data["snapshot"]
            session = snap.get("session")
            current = (session or {}).get("settings") or snap["defaults"]
            selection({**current, **patch})
            requires_all = data.get("migration", {}).get("requires_review") or bool(
                session and session.get("selection_required")
            )
            if requires_all and set(patch) != FIELDS:
                raise SettingsError("selection_required")
            oid = operation_id()
            body = {
                **self._identity(),
                "binding": data["binding"],
                "operation_id": oid,
                "patch": deepcopy(patch),
                "expected_defaults_revision": snap["defaults_revision"],
                "expected_session": {
                    k: session[k] for k in ("session_id", "generation", "revision")
                }
                if session
                else None,
            }
            self._pending = body
            self._unknown = False
            try:
                result = self._request("patch", payload=body)
                if (
                    result.get("accepted") is not True
                    or result.get("operation_id") != oid
                ):
                    raise SettingsError("uncertain")
                self._pending = None
            except SettingsError as exc:
                if exc.category in {"offline", "uncertain"}:
                    # Resolve by pure receipt reads, never by resending PATCH.
                    try:
                        self._recover_pending()
                    except SettingsError:
                        pass
                    if self._pending is not None or self._unknown:
                        self._snapshot = None
                        raise SettingsError("uncertain") from None
                else:
                    self._pending = None
                    self._snapshot = None
                    raise
            # Receipts are historical. Always obtain current authoritative state.
            return self.read()

    def projection(self) -> dict:
        if self._snapshot is None or self.context() != self._context:
            return {}
        data = self._snapshot
        snap = data["snapshot"]
        session = snap.get("session")
        allowed = data["allowed_values"]
        options = {k: [v for v in CHOICES[k] if v in allowed[k]] for k in CHOICES}
        voice = allowed["voice"]
        voices = [
            {"label_key": "shared_voice_default", "value": {"kind": "provider_default"}}
        ]
        for v in voice["voices"]:
            if (
                isinstance(v, dict)
                and isinstance(v.get("voice_id"), str)
                and isinstance(v.get("name"), str)
            ):
                value = {
                    "kind": "provider_voice",
                    "provider_id": voice.get("provider_id"),
                    "voice_id": v["voice_id"],
                }
                try:
                    selection({**snap["defaults"], "voice": value})
                except SettingsError:
                    continue
                voices.append({"label": v["name"][:256], "value": value})
        options["voice"] = voices
        return {
            "edit_token": self.edit_token(),
            "operation_pending": self._pending is not None,
            "operation_unknown": self._unknown,
            "values": deepcopy((session or {}).get("settings") or snap["defaults"]),
            "options": options,
            "active": bool(session),
            "writable": data["writable_fields"],
            "selection_required": bool(
                data.get("migration", {}).get("requires_review")
                or (session and session.get("selection_required"))
            ),
            "voice_available": data.get("voice_availability", {}).get("available")
            is True,
            "speaker_available": data.get("announcement_output", {}).get(
                "speaker_available"
            )
            is True,
        }
