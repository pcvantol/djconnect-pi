"""Owner-side controls for the released VibeCast B v1 display contract."""

import math
import re
import time
from threading import Lock

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from .config import CLIENT_TYPE
from .session_transport import SessionError

CODE = re.compile(r"[0-9]{6}")
OPAQUE = re.compile(r"[A-Za-z0-9_-]{43}")
SHARE_SECONDS = 7200


def supported(capabilities):
    broadcast = capabilities.get("session_broadcast") if isinstance(capabilities, dict) else None
    cap = broadcast.get("paired_display_admission") if isinstance(broadcast, dict) else None
    if not isinstance(cap, dict):
        return False
    clients = cap.get("owner_client_types")
    return (
        cap.get("supported") is True and type(cap.get("version")) is int and cap["version"] == 1
        and cap.get("owner_authentication") == "paired_device_bearer"
        and cap.get("owner_context_path") == "/api/djconnect/v1/display/owner/context"
        and cap.get("entry_path") == "/djconnect/vibecast/display"
        and isinstance(clients, list) and CLIENT_TYPE in clients
    )


def opaque(data, field):
    value = data.get(field)
    if not isinstance(value, str) or OPAQUE.fullmatch(value) is None:
        raise SessionError("invalid")
    return value


def generation(data):
    value = data.get("share_generation")
    if type(value) is not int or not 1 <= value <= 2**53 - 1:
        raise SessionError("invalid")
    return value


def duration(data, field, maximum):
    value = data.get(field)
    if type(value) not in (int, float) or not 0 < value <= maximum or not math.isfinite(value):
        raise SessionError("invalid")
    return value


class VibeCastSender(QObject):
    ready = Signal(object)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.visible = False
        self.running = False
        self.status = ""
        self.epoch = 0
        self.scope = None
        self.context = None
        self.claim = None
        self.closed = False
        self._lock = Lock()
        self.ready.connect(self.finish)
        self._claim_timer = QTimer(self)
        self._claim_timer.setSingleShot(True)
        self._claim_timer.timeout.connect(self.expire_claim)

    def basis(self):
        owner = self.owner
        cfg = owner.backend.cfg
        session_id = owner._session.get("session_id")
        if (self.closed or not owner._foreground or owner.backend.demoMode
                or owner._session.get("runtime_state") != "active" or not session_id or owner.lifecycleBusy
                or cfg.private_session or not supported(owner._caps)
                or (owner._bootstrap_binding is not None
                    and not (owner._bootstrap_current() and owner._bootstrap_private))):
            return None
        try:
            binding = owner.transport.binding()
        except SessionError:
            return None
        if not binding.profile_id or binding.profile_id != binding.resolved_profile_id:
            return None
        return (binding, session_id, owner._owner_epoch, owner._view_epoch,
                getattr(cfg, "music_backend", ""), getattr(cfg, "music_backend_revision", 0))

    def sync(self):
        if self.visible and self.scope != self.basis():
            self.hide()

    def snapshot(self):
        basis = self.basis()
        current = self.visible and self.scope == basis
        return {
            "available": basis is not None,
            "open": current,
            "busy": self.running,
            "status": self.status if current else "",
            "has_share": current and self.context is not None and self.context[1] is not None,
        }

    def open(self):
        scope = self.basis()
        if scope is None or self.running:
            return False
        self.visible = True
        self.scope = scope
        return self.action("context")

    def expire_claim(self):
        self.claim = None
        self.status = "expired"
        self.owner.changed.emit()

    def hide(self):
        self._claim_timer.stop()
        self.epoch += 1
        self.visible = False
        self.scope = self.context = self.claim = None
        self.status = ""

    def shutdown(self):
        with self._lock:
            self.closed = True
        self.hide()

    def action(self, action, code=""):
        self.sync()
        if not self.visible or self.running:
            return False
        context, claim = self.context, self.claim
        if action == "resolve" and (context is None or CODE.fullmatch(code) is None):
            return False
        if action == "approve" and (self.status != "confirm" or claim is None or time.monotonic() >= claim[1]):
            return False
        if action == "revoke" and (context is None or context[1] is None):
            return False
        self._claim_timer.stop()
        self.claim = None  # Approval consumes the local confirmation before dispatch.
        scope, epoch = self.scope, self.epoch
        self.running = True
        self.status = "loading"
        self.owner.changed.emit()

        def current():
            return self.visible and self.epoch == epoch and self.basis() == scope

        def worker():
            result, status = None, "failed"
            try:
                if current():
                    result = self.perform(action, code, context, claim, scope, current)
                    status = {"context": "ready", "resolve": "confirm",
                              "approve": "sharing", "revoke": "stopped"}[action]
                    if action == "context" and result[1] is not None:
                        status = "active"
            except SessionError:
                if action in {"approve", "revoke"}:
                    status = "uncertain"
            with self._lock:
                if not self.closed:
                    self.ready.emit((epoch, action, status, result))

        self.owner.backend._session_executor.submit(worker)
        return True

    def perform(self, action, code, context, claim, scope, current):
        binding, session_id, *_ = scope

        def call(route, payload):
            if not current():
                raise SessionError("context_changed")
            data = self.owner.transport.display_owner(binding, route, payload)
            if not current() or data.get("success") is not True or type(data.get("contract_version")) is not int or data["contract_version"] != 1:
                raise SessionError("context_changed")
            return data

        def fresh_context():
            data = call("context", {"session_id": session_id})
            if data.get("session_id") != session_id or data.get("route_trust") != "paired_owner_response":
                raise SessionError("context_changed")
            share = None
            if "share_id" in data:
                share = (opaque(data, "share_id"), generation(data))
                duration(data, "expires_in", 28800)
            return opaque(data, "issuer_epoch"), share

        if action == "context":
            return fresh_context()
        if action == "resolve":
            start = time.monotonic()
            data = call("resolve", {"code": code})
            if opaque(data, "issuer_epoch") != context[0]:
                raise SessionError("context_changed")
            payload = {"issuer_epoch": context[0], "claim_id": opaque(data, "claim_id"),
                       "browser_generation": opaque(data, "browser_generation"), "code": code}
            return payload, start + duration(data, "expires_in", 120)
        if fresh_context() != context:
            raise SessionError("context_changed")
        if action == "revoke":
            call("revoke", {"session_id": session_id, "share_id": context[1][0]})
            return context[0], None

        if time.monotonic() >= claim[1]:
            raise SessionError("unavailable")
        share = ({"mode": "create", "consent": True, "lifetime_seconds": SHARE_SECONDS}
                 if context[1] is None else
                 {"mode": "existing", "share_id": context[1][0], "share_generation": context[1][1]})
        data = call("approve", {"session_id": session_id, **claim[0], "share": share})
        if data.get("state") != "approved" or data.get("session_id") != session_id:
            raise SessionError("invalid")
        opaque(data, "display_id")
        duration(data, "share_expires_in", 28800)
        approved = (opaque(data, "share_id"), generation(data))
        if context[1] is not None and approved != context[1]:
            raise SessionError("context_changed")
        return context[0], approved

    @Slot(object)
    def finish(self, reply):
        epoch, action, status, result = reply
        self.running = False
        self.sync()
        if self.visible and self.epoch == epoch:
            self.status = status
            if action == "resolve":
                self.claim = result
                if result is not None:
                    remaining = max(0, math.ceil((result[1] - time.monotonic()) * 1000))
                    self._claim_timer.start(remaining)
            elif result is not None:
                self.context = result
            else:
                self.context = None
        self.owner.changed.emit()
