"""Original owner-confirmed content-erasure scope, identifiers only in RAM."""

import json
from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite
from threading import Lock
from uuid import UUID

from .session_projection import timestamp
from .session_transport import (
    SessionBinding,
    SessionError,
    deletion_identifier,
    deletion_operation,
)
from .shared_settings import operation_id


def supported(data):
    if not isinstance(data, dict):
        return False
    caps, versions = data.get("capabilities", {}), data.get("contract_versions", {})
    return (
        isinstance(caps, dict)
        and isinstance(versions, dict)
        and caps.get("session_content_delete") is True
        and type(versions.get("session_content_delete")) is int
        and versions["session_content_delete"] == 1
    )


def target(value, *, unit=False):
    if not isinstance(value, dict) or set(value) != {"kind", "session_id", "target_id"}:
        raise SessionError("invalid")
    kinds = (
        {"moment", "exchange", "attempt"}
        if unit
        else {"moment", "entry", "message", "request"}
    )
    kind, sid = value["kind"], value["session_id"]
    if not isinstance(kind, str) or kind not in kinds or not isinstance(sid, str):
        raise SessionError("invalid")
    if sid:
        deletion_identifier(sid, 200)
    elif kind in {"moment", "entry"}:
        raise SessionError("invalid")
    return kind, sid, deletion_identifier(value["target_id"], 200)


def wire_target(value):
    return dict(zip(("kind", "session_id", "target_id"), value, strict=True))


def _rows(data, key, fields):
    rows = data.get(key)
    if not isinstance(rows, list) or len(rows) > 1000:
        raise SessionError("invalid")
    result = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(fields):
            raise SessionError("invalid")
        values = []
        for name in fields:
            value = row[name]
            if name == "disposition":
                if not isinstance(value, str) or value not in {"remove", "unavailable"}:
                    raise SessionError("invalid")
            else:
                deletion_identifier(value, 200)
            values.append(value)
        result.append(tuple(values))
    if len(set(result)) != len(result) or len({row[:2] for row in result}) != len(
        result
    ):
        raise SessionError("invalid")
    return tuple(result)


def _ids(data, key):
    rows = data.get(key)
    if not isinstance(rows, list) or len(rows) > 1000:
        raise SessionError("invalid")
    values = tuple(deletion_identifier(row, 200) for row in rows)
    if len(set(values)) != len(values):
        raise SessionError("invalid")
    return values


def _base(data, binding):
    if (
        not isinstance(data, dict)
        or data.get("success") is not True
        or type(data.get("schema_version")) is not int
        or data["schema_version"] != 1
        or not binding.profile_id
        or binding.profile_id != binding.resolved_profile_id
        or data.get("owner_profile_id") != binding.profile_id
    ):
        raise SessionError("invalid")


def _scope(data):
    entries = _rows(data, "affected_entries", ("session_id", "entry_id", "disposition"))
    removed, unavailable = (
        _ids(data, "removed_message_ids"),
        _ids(data, "unavailable_message_ids"),
    )
    if (
        set(removed) & set(unavailable)
        or data.get("music_playback_undone") is not False
    ):
        raise SessionError("invalid")
    return entries, removed, unavailable


@dataclass(frozen=True)
class ContentPreview:
    binding: SessionBinding = field(repr=False)
    selected: tuple
    confirmation: str = field(repr=False)
    unit: tuple
    entries: tuple
    removed: tuple
    unavailable: tuple
    moments: tuple
    fenced: int
    created: float
    expires: float

    @classmethod
    def parse(cls, data, binding, selected, *, now):
        _base(data, binding)
        if target(data.get("target")) != selected:
            raise SessionError("context_changed")
        created, expires = (
            timestamp(data.get("created_at")),
            timestamp(data.get("expires_at")),
        )
        if (
            created is None
            or expires is None
            or type(now) not in (int, float)
            or not isfinite(now)
            or not isfinite(created)
            or not isfinite(expires)
            or created > now + 30
            or not created < expires <= created + 300
            or not now < expires
        ):
            raise SessionError("unavailable")
        entries, removed, unavailable = _scope(data)
        moments = _rows(data, "affected_moments", ("session_id", "moment_id"))
        fenced = data.get("fenced_request_count")
        if (
            type(fenced) is not int
            or not 0 <= fenced <= 1000
            or sum(map(len, (entries, removed, unavailable, moments))) + fenced > 1000
        ):
            raise SessionError("invalid")
        unit = target(data.get("unit"), unit=True)
        if unit[1] != selected[1] or (selected[0] == "moment" and unit != selected):
            raise SessionError("context_changed")
        return cls(
            binding,
            selected,
            deletion_identifier(data.get("confirmation_id"), 200),
            unit,
            entries,
            removed,
            unavailable,
            moments,
            fenced,
            created,
            expires,
        )


@dataclass(frozen=True)
class ContentIntent:
    preview: ContentPreview
    epoch: int
    operation: str
    expires: float
    _claimed: list = field(default_factory=list, repr=False, compare=False)
    _lock: object = field(default_factory=Lock, repr=False, compare=False)

    @property
    def digest(self):
        return sha256(
            json.dumps(
                {"confirmation_id": self.preview.confirmation},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()

    @classmethod
    def confirmed(cls, preview, epoch, caps, *, now, confirmed):
        if (
            confirmed is not True
            or not isinstance(preview, ContentPreview)
            or not supported(caps)
            or type(epoch) is not int
            or epoch < 0
            or type(now) not in (int, float)
            or not isfinite(now)
            or not preview.created - 30 <= now < preview.expires
        ):
            raise SessionError("invalid")
        op = deletion_operation(operation_id())
        created = (UUID(op).int >> 80) / 1000
        if not created - 30 <= now < created + 300:
            raise SessionError("invalid")
        return cls(preview, epoch, op, min(preview.expires, created + 300))

    def claim(self, binding, epoch, caps, *, now):
        with self._lock:
            if self._claimed:
                raise SessionError("uncertain")
            if (
                binding != self.preview.binding
                or epoch != self.epoch
                or type(epoch) is not int
                or not supported(caps)
            ):
                raise SessionError("context_changed")
            if (
                type(now) not in (int, float)
                or not isfinite(now)
                or not self.preview.created - 30 <= now < self.expires
            ):
                raise SessionError("unavailable")
            self._claimed.append(True)
            return {
                "contract_version": 1,
                "confirmation_id": self.preview.confirmation,
                "operation_id": self.operation,
                "confirmed": True,
            }

    def receipt(self, data):
        preview = self.preview
        _base(data, preview.binding)
        if (
            data.get("state") != "completed"
            or data.get("deleted") is not True
            or data.get("operation_id") != self.operation
            or data.get("confirmation_id") != preview.confirmation
            or data.get("request_digest") != self.digest
            or target(data.get("unit"), unit=True) != preview.unit
            or _scope(data) != (preview.entries, preview.removed, preview.unavailable)
        ):
            raise SessionError("uncertain")
        # affected_moments/fenced_request_count belong to prepare, not the receipt.
        return True

    def outcome(self, data):
        _base(data, self.preview.binding)
        state = data.get("state")
        if (
            not isinstance(state, str)
            or state not in {"unknown", "pending", "completed", "expired_unknown"}
            or data.get("operation_id") != self.operation
            or data.get("confirmation_id") != self.preview.confirmation
            or data.get("request_digest") != self.digest
            or data.get("definitive") is not (state == "completed")
        ):
            raise SessionError("uncertain")
        if state == "completed":
            self.receipt(data.get("receipt"))
        elif "receipt" in data:
            raise SessionError("uncertain")
        if "unit" in data and target(data["unit"], unit=True) != self.preview.unit:
            raise SessionError("uncertain")
        return state
