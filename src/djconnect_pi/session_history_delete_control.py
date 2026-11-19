"""Explicit saved-Session erasure, separate worker and original archive ticket."""
from concurrent.futures import ThreadPoolExecutor
from threading import RLock
from uuid import UUID

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from .session_history_delete import (
    ArchiveDeleteSnapshot,
    BulkDeleteIntent,
    SingleDeleteIntent,
    archive_status_supported,
    bulk_delete_supported,
    original_archive_status,
    single_delete_supported,
)
from .session_projection import active_session, history_page
from .session_transport import SessionError, deletion_identifier


class HistoryDeleteControl(QObject):
    ready = Signal(object)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.kind = "single"
        self.visible = False
        self.closed = False
        self._completion_lock = RLock()
        self.running = False
        self.blocked = False
        self.status = ""
        self.serial = 0
        self.request = None
        self.confirmation = None
        self.pending = None
        self.executor = None
        self.recovery = None
        self._notify_timer = QTimer(self)
        self._notify_timer.setSingleShot(True)
        self._notify_timer.setInterval(0)
        self._notify_timer.timeout.connect(owner.changed.emit)
        self._recovery_timer = QTimer(self)
        self._recovery_timer.setSingleShot(True)
        self._recovery_timer.setInterval(0)
        self._recovery_timer.timeout.connect(self._read_recovery)
        self.ready.connect(self.finish)

    def basis(self, kind="single"):
        owner = self.owner
        try:
            binding = owner.transport.binding()
            if kind == "status":
                if (self.closed or not self.visible or not owner._foreground or owner.backend.demoMode
                        or not owner._history_supported() or not archive_status_supported(owner._caps)
                        or not binding.profile_id or binding.profile_id != binding.resolved_profile_id
                        or not self.pending or not self.pending["posted"]
                        or self.pending["intent"].binding != binding or owner._running_action in {"start", "end"}):
                    return None
                return (binding, owner._view_epoch, owner._session.get("session_id", ""))
            if kind == "bulk":
                if (self.closed or not self.visible or not owner._foreground or owner.backend.demoMode
                        or not owner._history_supported() or not bulk_delete_supported(owner._caps)
                        or not binding.profile_id or binding.profile_id != binding.resolved_profile_id
                        or owner._timeline.get("session") or owner._running_action in {"start", "end"}):
                    return None
                return (binding, owner._view_epoch, owner._session.get("session_id", ""))
            page = owner._timeline
            header = page.get("session", {})
            sid = deletion_identifier(header.get("session_id"), 200)
            revision = deletion_identifier(header.get("revision"), 4096)
            deadline = page.get("_session_deadline")
            if (self.closed or not self.visible or not owner._foreground or owner.backend.demoMode
                    or not owner._history_supported() or not single_delete_supported(owner._caps)
                    or not binding.profile_id or binding.profile_id != binding.resolved_profile_id
                    or header.get("lifecycle_status") not in ("ENDED", "INTERRUPTED")
                    or sid == owner._session.get("session_id")
                    or type(deadline) not in (int, float) or not owner._clock.now() < deadline < float("inf")
                    or owner._running_action in {"start", "end"}):
                return None
            return (binding, owner._view_epoch, owner._session.get("session_id", ""), sid, revision, deadline)
        except (SessionError, AttributeError, TypeError, ValueError):
            return None

    def valid(self, request):
        return (self.request is request and request is not None and request["basis"] == self.basis("status" if request.get("status_read") else request.get("kind", "single"))
                and (not request.get("status_read") or request.get("attempt") is self.pending)
                and (request.get("status_read") or not request.get("snapshot") or self.owner._clock.now() < request["snapshot"].expires_at))

    def sync(self):
        if self.pending:
            try:
                same_owner = self.pending["intent"].binding == self.owner.transport.binding()
            except SessionError:
                same_owner = False
            if not same_owner:
                self.hide(reset=True)
        if self.request is not None and not self.valid(self.request):
            self.hide()

    def hide(self, *, reset=False):
        self.serial += 1
        self.request = None
        self.confirmation = None
        if reset:
            self.pending = None
            self.blocked = False
            self.recovery = None
            self._recovery_timer.stop()
        self.status = "uncertain" if self.blocked else ""

    def set_visible(self, visible):
        self.visible = bool(visible)
        if not self.visible:
            self.recovery = None
            self._recovery_timer.stop()
            self.hide()

    def snapshot(self):
        self.sync()
        return {"available": self.basis() is not None, "bulk_available": self.basis("bulk") is not None,
                "kind": self.kind, "attempted": bool(self.pending and self.pending["posted"]), "status_available": self.basis("status") is not None,
                "count": self.confirmation["snapshot"].count if self.confirmation and self.confirmation.get("snapshot") else 0,
                "running": self.running,
                "blocked": self.blocked, "status": self.status,
                "lease": self.confirmation["serial"] if self.confirmation else 0}

    def idle(self):
        owner = self.owner
        return not (self.running or owner._running or owner._question_running
                    or owner._artwork_prepare.running or owner._playback_control.running)

    def read(self, session_id):
        basis = self.basis()
        if basis is None or basis[3] != session_id or not self.idle() or self.blocked:
            return False
        self.serial += 1
        request = {"basis": basis, "serial": self.serial, "send": False, "posted": False}
        self.confirmation = None
        self._launch(request)
        return True

    def read_bulk(self):
        basis = self.basis("bulk")
        if basis is None or not self.idle() or self.blocked:
            return False
        self.serial += 1
        self.confirmation = None
        self._launch({"basis": basis, "kind": "bulk", "serial": self.serial, "send": False, "posted": False})
        return True

    def confirm(self, lease):
        request = self.confirmation
        if (type(lease) is not int or request is None or lease != request["serial"]
                or not self.idle() or self.blocked or not self.valid(request)):
            return False
        binding, epoch, *_ = request["basis"]
        try:
            if request.get("kind") == "bulk":
                intent = BulkDeleteIntent.confirmed(binding, epoch, request["snapshot"], request["caps"],
                    now=self.owner._clock.now(), confirmed=True)
            else:
                _, _, _, sid, _, deadline = request["basis"]
                intent = SingleDeleteIntent.confirmed(binding, epoch, request["detail"], request["caps"],
                    session_id=sid, admitted_until=deadline, now=self.owner._clock.now(), confirmed=True)
        except SessionError:
            self.hide()
            self.owner.changed.emit()
            return False
        self.serial += 1
        self.confirmation = None
        self.blocked = True  # No second mutation while the one send ticket is unresolved.
        self.pending = {"intent": intent, "kind": request.get("kind", "single"), "posted": False}
        self._launch({**request, "serial": self.serial, "send": True, "intent": intent, "attempt": self.pending})
        return True

    def read_status(self):
        basis = self.basis("status")
        if basis is None or not self.idle() or not self.blocked:
            return False
        self.serial += 1
        self.confirmation = None
        self._launch({"basis": basis, "kind": self.pending["kind"], "status_read": True,
                      "attempt": self.pending, "serial": self.serial, "send": False, "posted": False})
        return True

    def _fresh(self, request):
        def check():
            if not self.valid(request):
                raise SessionError("context_changed")
        check()
        binding, _, current, *_ = request["basis"]
        bulk = request.get("kind") == "bulk"
        status_read = request.get("status_read", False)
        sid = None if bulk or status_read else request["basis"][3]
        fresh = active_session(self.owner.transport.active(binding, isolated=True))
        check()
        if fresh.get("session_id", "") != current or (not bulk and not status_read and sid == fresh.get("session_id")):
            raise SessionError("context_changed")
        caps = self.owner.transport.capabilities(binding, isolated=True)
        check()
        if status_read:
            if not archive_status_supported(caps):
                raise SessionError("unavailable")
            return None, caps
        if not (bulk_delete_supported(caps) if bulk else single_delete_supported(caps)):
            raise SessionError("unavailable")
        if bulk:
            # Never prepare a replacement set under an existing confirmation.
            if request["send"]:
                return request["snapshot"], caps
            snapshot = ArchiveDeleteSnapshot.parse(self.owner.transport.history_delete_snapshot(binding),
                                                   binding, now=self.owner._clock.now())
            check()
            return snapshot, caps
        revision = request["basis"][4]
        page = history_page(self.owner.transport.timeline(binding, sid, isolated=True),
                            session_id=sid, now=self.owner._clock.now())
        check()
        header = page["session"]
        if header.get("revision") != revision or header.get("lifecycle_status") not in ("ENDED", "INTERRUPTED"):
            raise SessionError("conflict")
        # Keep no entries or display bodies in the confirmation, only original CAS metadata.
        return ({"success": True, "schema_version": 2, "history_contract_version": 2,
                 "session": {key: header[key] for key in ("session_id", "revision", "lifecycle_status")}},
                {"capabilities": {"session_history_delete": True},
                 "contract_versions": {"session_history_delete": 1}})

    def _launch(self, request):
        self.request = request
        self.kind = request.get("kind", "single")
        self.running = True
        self.status = "sending" if request["send"] else "reading"
        self.owner.changed.emit()

        def worker():
            result = {"request": request}
            try:
                detail, caps = self._fresh(request)
                if request.get("status_read"):
                    binding = request["basis"][0]
                    intent = request["attempt"]["intent"]
                    outcome = self.owner.transport.history_delete_status(binding, **original_archive_status(intent))
                    if not self.valid(request):
                        raise SessionError("context_changed")
                    # Status can report expiry, but cannot extend the original
                    # UUID journal or turn a late cached receipt into completion.
                    created = (UUID(intent.operation).int >> 80) / 1000
                    now = self.owner._clock.now()
                    if outcome["state"] == "completed" and not created - 30 <= now < created + 300:
                        raise SessionError("uncertain")
                    result["outcome"] = outcome["state"]
                elif request["send"]:
                    binding, epoch, *_ = request["basis"]
                    values = request["intent"].claim(binding, epoch, caps, now=self.owner._clock.now())
                    if not self.valid(request):
                        raise SessionError("context_changed")
                    request["posted"] = True  # Started HTTP may finish after withdrawal; never pretend cancellation.
                    request["attempt"]["posted"] = True
                    if request.get("kind") == "bulk":
                        self.owner.transport.delete_all_history(binding, **values)
                    else:
                        self.owner.transport.delete_history(binding, **values)
                    if not self.valid(request):
                        raise SessionError("context_changed")
                    result["deleted"] = True
                else:
                    result.update(detail=detail, caps=caps)
                    if request.get("kind") == "bulk":
                        result["snapshot"] = detail
            except SessionError as exc:
                result["error"] = exc.category
                result["code"] = exc.code
            except Exception:  # noqa: BLE001 - one failed effect never causes a replay.
                result["error"] = "uncertain" if request["posted"] else "unavailable"
            self._publish(result)
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pi-archive-delete")
        self.executor.submit(worker)

    def _publish(self, result):
        # shutdown must finish before a caller destroys this QObject. Serialize
        # the last closed-check and native emission; never hold across HTTP.
        # RLock permits a same-thread signal handler to shut down reentrantly.
        with self._completion_lock:
            if not self.closed:
                try:
                    self.ready.emit(result)
                except RuntimeError:
                    pass

    @Slot(object)
    def finish(self, result):
        self.running = False
        request = result["request"]
        if not self.valid(request):
            # A late receipt cannot replace a successor view. A possibly started
            # write stays blocked until the user explicitly refreshes the archive.
            try:
                same_owner = request["basis"][0] == self.owner.transport.binding()
            except SessionError:
                same_owner = False
            if request["posted"] and same_owner:
                self.blocked = True
                self.status = "uncertain"
            self.owner.changed.emit()
            return
        error = result.get("error")
        if error in {"denied", "unpaired"}:
            self.owner.invalidate()
            self.owner._error = error
        elif request.get("status_read") and result.get("outcome") != "completed":
            self.request = None
            self.confirmation = None
            self.blocked = True
            self.status = result.get("outcome", "uncertain")
        elif result.get("deleted") or result.get("outcome") == "completed":
            self.request = None
            self.confirmation = None
            self.blocked = False
            self.pending = None
            self.owner.invalidateArchive()
            self.status = "deleted"
            # The receipt is never a Runtime projection. An independent owner
            # read resolves any server-withdrawn dependent Flow contributions.
            self.owner.refresh()
        elif error:
            self.confirmation = None
            self.blocked = bool(request["posted"] and error in {"uncertain", "context_changed"})
            self.status = "uncertain" if self.blocked else "snapshot_conflict" if result.get("code") == "history_delete_snapshot_conflict" else "failed"
            self.request = None
            if not self.blocked:
                self.pending = None
        else:
            request.update(detail=result["detail"], caps=result["caps"])
            if request.get("kind") == "bulk":
                request["snapshot"] = result["snapshot"]
            self.confirmation = request
            self.status = "empty" if request.get("snapshot") and request["snapshot"].count == 0 else "confirm"
        self.owner.changed.emit()

    def recover(self):
        if not self.visible or not self.owner._foreground or not self.idle() or self.recovery is not None:
            return False
        try:
            binding = self.owner.transport.binding()
        except SessionError:
            return False
        current = self.owner._session.get("session_id", "")
        # An independent archive reload cannot settle an ambiguous old POST.
        pending = self.pending if self.pending and self.pending["posted"] else None
        self.hide(reset=True)
        self.pending = pending
        self.blocked = pending is not None
        if pending:
            self.kind = pending["kind"]
            self.status = "uncertain"
        self.owner.invalidateArchive()
        # QML's derived search target changes while detail is withdrawn. Let its
        # existing clearSearch/view-epoch fence settle before capturing the new
        # explicit read's epoch. There is one bounded callback, never a POST retry.
        self.recovery = (binding, current)
        self._recovery_timer.start()
        return True

    @Slot()
    def _read_recovery(self):
        context = self.recovery
        self.recovery = None
        if context is None:
            return
        binding, current = context
        try:
            valid = binding == self.owner.transport.binding()
        except SessionError:
            valid = False
        if (valid and self.visible and not self.closed and self.owner._foreground and self.idle()
                and not self.owner._timeline and self.owner._session.get("session_id", "") == current):
            self.owner.loadHistory()

    def notify(self):
        if not self.closed:
            self._notify_timer.start()

    def shutdown(self):
        with self._completion_lock:
            self.closed = True
        self._notify_timer.stop()
        self.hide(reset=True)
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
