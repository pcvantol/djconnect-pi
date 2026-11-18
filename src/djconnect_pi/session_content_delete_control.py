"""Present the Core erasure scope and resolve only its original operation."""

import logging
from threading import RLock

from PySide6.QtCore import QObject, Signal, Slot

from .session_content_delete import (
    ContentIntent,
    ContentPreview,
    supported,
    target,
    wire_target,
)
from .session_projection import timestamp
from .session_transport import SessionError, private_scope_allowed

_LOGGER = logging.getLogger(__name__)


class ContentDeleteControl(QObject):
    ready = Signal(object)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.running = False
        self.visible = False
        self.status = ""
        self.preview = None
        self.lease = 0
        self.pending = None
        self.closed = False
        self._completion_lock = RLock()
        self.ready.connect(self.finish)

    def binding(self):
        try:
            binding = self.owner.transport.binding()
        except SessionError:
            return None
        return binding if binding.profile_id and binding.profile_id == binding.resolved_profile_id else None

    def basis(self):
        owner = self.owner
        if (self.closed or not self.visible or not owner._foreground or owner.backend.demoMode
                or not supported(owner._caps) or not private_scope_allowed(owner)):
            return None
        binding = self.binding()
        if binding is None:
            return None
        return binding, owner._owner_epoch, owner._view_epoch, owner._session.get("session_id", "")

    def admitted(self, selected):
        kind, sid, identifier = selected
        owner = self.owner
        if kind == "moment":
            return sid == owner._session.get("session_id") and any(
                row.get("moment_id") == identifier for row in owner._moments
            )
        return any(
            row.get("entry_id") == identifier and row.get("session_id") == sid
            and row.get("kind") in {"dj_moment", "conversation_user", "conversation_dj"}
            and row.get("state") != "source_withdrawn"
            and (timestamp(row.get("retained_until")) or 0) > owner._clock.now()
            for row in (*owner._retained_flow, *owner._timeline.get("entries", []))
        )

    def cancel(self):
        self.lease += 1
        self.preview = None
        self.status = "uncertain" if self.pending else ""

    def sync(self):
        binding = self.binding()
        if self.pending and binding is not None and self.pending.preview.binding != binding:
            self.pending = None
            self.cancel()
        if self.preview:
            basis, preview = self.preview
            if basis != self.basis() or not self.admitted(preview.selected) or self.owner._clock.now() >= preview.expires:
                self.cancel()

    def snapshot(self):
        self.sync()
        preview = self.preview[1] if self.preview else None
        return {
            "available": self.basis() is not None and self.pending is None,
            "status_available": self.basis() is not None and self.pending is not None,
            "status": self.status,
            "lease": self.lease if preview else 0,
            "expires": int(preview.expires * 1000) if preview else 0,
            "unit": preview.unit[0] if preview else "",
            "remove_entries": sum(row[2] == "remove" for row in preview.entries) if preview else 0,
            "unavailable_entries": sum(row[2] == "unavailable" for row in preview.entries) if preview else 0,
            "remove_messages": len(preview.removed) if preview else 0,
            "unavailable_messages": len(preview.unavailable) if preview else 0,
            "moments": len(preview.moments) if preview else 0,
            "fenced": preview.fenced if preview else 0,
        }

    def begin(self, kind, session_id, identifier):
        basis = self.basis()
        if basis is None or self.pending or self.owner.busy or self.owner.questionBusy or kind not in {"entry", "moment"}:
            return False
        try:
            selected = target({"kind": kind, "session_id": session_id, "target_id": identifier})
        except SessionError:
            return False
        if not self.admitted(selected):
            return False
        self.cancel()
        return self.launch("prepare", basis, selected)

    def confirm(self, lease):
        self.sync()
        if lease != self.lease or self.preview is None or self.owner.busy or self.owner.questionBusy:
            return False
        basis, preview = self.preview
        try:
            intent = ContentIntent.confirmed(preview, basis[1], self.owner._caps, now=self.owner._clock.now(), confirmed=True)
        except SessionError:
            self.cancel()
            return False
        self.cancel()
        self.pending = intent
        return self.launch("delete", basis, intent)

    def check_status(self):
        self.sync()
        basis = self.basis()
        if basis is None or self.pending is None or self.owner.busy or self.owner.questionBusy:
            return False
        return self.launch("status", basis, self.pending)

    def launch(self, action, basis, value):
        lease = self.lease
        owner = self.owner
        binding, epoch, *_ = basis
        self.running = True
        self.status = "loading"
        owner.changed.emit()

        def worker():
            result = None
            attempted = False
            try:
                caps = owner.transport.capabilities(binding, isolated=True)
                if self.basis() != basis or self.lease != lease or not supported(caps):
                    raise SessionError("context_changed")
                if action == "prepare" and self.admitted(value):
                    data = owner.transport.prepare_content_delete(binding, wire_target(value))
                    result = ContentPreview.parse(data, binding, value, now=owner._clock.now())
                elif action == "delete" and self.admitted(value.preview.selected):
                    payload = value.claim(binding, epoch, caps, now=owner._clock.now())
                    if self.basis() != basis or self.lease != lease:
                        raise SessionError("context_changed")
                    attempted = True
                    owner.transport.delete_content(binding, value, payload)
                    result = "completed"
                elif action == "status":
                    result = owner.transport.content_delete_status(binding, value)
            except SessionError:
                pass  # A POST without a validated receipt has an unknown outcome.
            except (RuntimeError, TypeError, ValueError) as exc:
                _LOGGER.warning("Content erasure worker failed (%s)", type(exc).__name__)
            with self._completion_lock:
                if not self.closed:
                    self.ready.emit((action, basis, value, lease, attempted, result))

        owner.backend._session_executor.submit(worker)
        return True

    @Slot(object)
    def finish(self, response):
        action, basis, value, lease, attempted, result = response
        self.running = False
        if action == "prepare":
            if self.lease == lease:
                self.status = "failed"
                if (self.basis() == basis and result is not None and self.admitted(value)
                        and self.owner._clock.now() < result.expires):
                    self.preview = basis, result
                    self.status = "confirm"
        elif self.pending is value:
            current = self.basis()
            if result == "completed" and current is not None and current[:2] == basis[:2]:
                self.pending = None
                self.status = "deleted"
                self.owner.applyContentWithdrawal(value.preview)
            elif action == "delete" and not attempted:
                self.pending = None
                self.status = "failed"
            else:
                self.status = result if result in {"pending", "unknown", "expired_unknown"} else "uncertain"
        self.owner.changed.emit()

    def shutdown(self):
        with self._completion_lock:
            self.closed = True
        self.cancel()
