"""Minimal RAM-only confirmed single-archive intent; no UI or effect scheduler.

The UI owner must supply a fresh authorized detail read before confirmation and
withdraw its pending ticket on navigation/context changes. This primitive keeps
only identifiers, original authority, revision and deadlines, never page bodies.
"""
from dataclasses import dataclass, field
from math import isfinite
from threading import Lock
from uuid import UUID

from .session_transport import (
    SessionBinding,
    SessionError,
    deletion_identifier,
    deletion_operation,
)
from .shared_settings import operation_id


def single_delete_supported(payload):
    if not isinstance(payload, dict):
        return False
    caps, versions = payload.get("capabilities"), payload.get("contract_versions")
    return (isinstance(caps, dict) and isinstance(versions, dict)
            and caps.get("session_history_delete") is True
            and type(versions.get("session_history_delete")) is int
            and versions["session_history_delete"] == 1)


@dataclass(frozen=True)
class SingleDeleteIntent:
    binding: SessionBinding = field(repr=False)
    epoch: int
    session_id: str
    revision: str = field(repr=False)
    operation: str
    expires_at: float
    _claimed: list = field(default_factory=list, repr=False, compare=False)
    _lock: object = field(default_factory=Lock, repr=False, compare=False)

    @classmethod
    def confirmed(cls, binding, epoch, detail, capabilities, *, session_id, admitted_until, now, confirmed):
        # admitted_until is the ORIGINAL known parent retention deadline. It is
        # not a new five-minute display grant or a default private-scope TTL.
        if (confirmed is not True or not single_delete_supported(capabilities)
                or type(epoch) is not int or epoch < 0
                or not binding.profile_id or binding.profile_id != binding.resolved_profile_id
                or type(now) not in (int, float) or not isfinite(now)
                or type(admitted_until) not in (int, float) or not isfinite(admitted_until)
                or admitted_until <= now or not isinstance(detail, dict)
                or detail.get("success") is not True
                or type(detail.get("schema_version")) is not int or detail["schema_version"] != 2
                or type(detail.get("history_contract_version")) is not int or detail["history_contract_version"] != 2):
            raise SessionError("invalid")
        header = detail.get("session")
        if (not isinstance(header, dict) or not isinstance(header.get("lifecycle_status"), str)
                or header["lifecycle_status"] not in {"ENDED", "INTERRUPTED"}):
            raise SessionError("unavailable")
        sid = deletion_identifier(header.get("session_id"), 200)
        if sid != deletion_identifier(session_id, 200):
            raise SessionError("context_changed")
        revision = deletion_identifier(header.get("revision"), 4096)
        op = deletion_operation(operation_id())
        created = (UUID(op).int >> 80) / 1000
        if created > now + 30 or now >= created + 300:
            raise SessionError("invalid")
        return cls(binding, epoch, sid, revision, op, min(admitted_until, created + 300))

    def claim(self, binding, epoch, capabilities, *, now):
        """Burn one send ticket before HTTP. Timeout/close cannot rearm it.

        Call with the owner's live epoch and conservative ExpiryClock. A started
        HTTP request may finish; accepting its receipt still needs a live epoch
        check by the UI owner. There is no cancellation/exactly-once claim here.
        """
        with self._lock:
            if self._claimed:
                raise SessionError("uncertain")
            if (binding != self.binding or type(epoch) is not int or epoch != self.epoch
                    or not single_delete_supported(capabilities)):
                raise SessionError("context_changed")
            created = (UUID(self.operation).int >> 80) / 1000
            if (type(now) not in (int, float) or not isfinite(now)
                    or created > now + 30 or now >= self.expires_at):
                raise SessionError("unavailable")
            self._claimed.append(True)
            return {"session_id": self.session_id, "expected_revision": self.revision,
                    "operation_id": self.operation, "confirmed": True}
