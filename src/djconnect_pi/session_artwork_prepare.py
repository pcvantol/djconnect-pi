"""Explicit single-Moment preparation, never automatic provider work or replay."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from PySide6.QtCore import QObject, Signal, Slot

from .session_artwork import artwork_lease
from .session_current_reply import moment_reference
from .session_projection import active_session
from .session_transport import SessionError, private_scope_allowed


def prepare_reference(owner, moment_id):
    caps = owner._caps
    if (not owner._foreground or not owner._moment_images.visible
            or owner._session.get("runtime_state") != "active"
            or not private_scope_allowed(owner)
            or caps.get("capabilities", {}).get("session_artwork") is not True
            or type(caps.get("contract_versions", {}).get("session_artwork")) is not int
            or caps["contract_versions"]["session_artwork"] != 1
            or owner._session.get("broadcast", {}).get("native_delivery", {}).get("current_moment_id") != moment_id):
        return {}
    sid = owner._session.get("session_id")
    selected = {"kind": "selected_moment", "session_id": sid, "moment_id": moment_id}
    return moment_reference(owner._session, selected, now=owner._clock.now())


class ArtworkPreparation(QObject):
    ready = Signal(object)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.running = False
        self.request = None
        self.revoked = False
        self.status = ""
        self.closed = False
        self.executor = None
        self.ready.connect(self.finish)

    def valid(self):
        try:
            r = self.request
            return (not self.closed and not self.revoked and r is not None
                    and self.owner._running_action not in {"start", "end"}
                    and self.owner.transport.binding() == r["binding"]
                    and prepare_reference(self.owner, r["moment_id"]) == r["reference"])
        except (SessionError, AttributeError, KeyError, TypeError, ValueError, RuntimeError):
            return False

    def sync(self):
        if self.request and not self.valid():
            self.revoked = True
            self.status = ""
            self.request = None

    def hide(self):
        # A hide/show round trip cannot revive an already queued POST intent.
        self.revoked = True
        self.status = ""
        self.request = None

    def snapshot(self):
        self.sync()
        sid = self.owner._session.get("session_id", "")
        mid = self.owner._session.get("broadcast", {}).get("native_delivery", {}).get("current_moment_id", "")
        try:
            reference = prepare_reference(self.owner, mid)
            existing = artwork_lease(self.owner._session, self.owner._caps, self.owner.transport.binding(), self.owner._clock.now()) if reference else None
        except (SessionError, AttributeError, KeyError, TypeError, ValueError):
            reference = existing = None
        return {"moment_id": mid, "available": bool(sid and reference and not existing),
                "status": "loading" if self.running and self.valid() else self.status if self.valid() else ""}

    def start(self, session_id, moment_id):
        if (self.closed or self.running or self.owner._running or self.owner._question_running
                or session_id != self.owner._session.get("session_id") or self.owner.backend.demoMode or self.owner._playback_control.running):
            return False
        state = self.snapshot()
        if not state["available"] or moment_id != state["moment_id"]:
            return False
        try:
            binding = self.owner.transport.binding()
        except SessionError:
            return False
        self.request = {"binding": binding, "session_id": session_id, "moment_id": moment_id,
                        "reference": prepare_reference(self.owner, moment_id)}
        self.revoked = False
        self.status = ""
        self.running = True
        self.owner.changed.emit()
        request = deepcopy(self.request)

        def check():
            if not self.valid():
                raise SessionError("context_changed")

        def worker():
            result = {}
            try:
                check()
                response = self.owner.transport.prepare_artwork(binding, session_id, moment_id)
                check()
                rows = response.get("session_media")
                if (response.get("success") is not True or type(response.get("contract_version")) is not int
                        or response["contract_version"] != 1 or not isinstance(rows, list) or len(rows) != 1
                        or not isinstance(rows[0], dict) or rows[0].get("session_id") != session_id
                        or rows[0].get("moment_id") != moment_id or "entry_id" in rows[0]):
                    raise SessionError("invalid")
                # POST metadata is never published. Read a fresh owner snapshot.
                check()
                fresh = active_session(self.owner.transport.active(binding))
                check()
                reference = moment_reference(fresh, request["reference"]["selected"], now=self.owner._clock.now())
                if (fresh.get("session_id") != session_id or fresh.get("runtime_state") != "active"
                        or fresh.get("broadcast", {}).get("session", {}).get("session_id") != session_id
                        or fresh.get("broadcast", {}).get("native_delivery", {}).get("current_moment_id") != moment_id
                        or reference != request["reference"]):
                    result["withdraw_current"] = True
                    raise SessionError("context_changed")
                media = fresh.get("broadcast", {}).get("session_media", [])
                if not isinstance(media, list) or len(media) > 64:
                    raise SessionError("invalid")
                result["media"] = deepcopy(media)
            except SessionError as exc:
                result["error"] = exc.category
            except (AttributeError, KeyError, OverflowError, TypeError, ValueError):
                result["error"] = "invalid"
            try:
                self.ready.emit(result)
            except RuntimeError:
                pass
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="djconnect-artwork-prepare")
        self.executor.submit(worker)
        return True

    @Slot(object)
    def finish(self, result):
        valid = self.valid()
        self.running = False
        if not valid:
            self.status = ""
            self.request = None
            self.owner.changed.emit()
            return
        if result.get("error") == "denied" or result.get("withdraw_current"):
            self.owner.invalidate()
            self.owner._error = "denied" if result.get("error") == "denied" else "context_changed"
            self.owner.changed.emit()
            return
        if "media" in result:
            # Do not replace Runtime, conversation, selection or settings with a
            # preparation worker's snapshot. Merge only its independently reread media.
            self.owner._session["broadcast"]["session_media"] = result["media"]
            self.status = "" if artwork_lease(self.owner._session, self.owner._caps, self.request["binding"], self.owner._clock.now()) else "unavailable"
            if not self.status:
                self.request = None
        else:
            self.status = "uncertain" if result.get("error") in {"offline", "uncertain"} else "unavailable"
        self.owner.changed.emit()

    def shutdown(self):
        self.closed = True
        self.revoked = True
        self.status = ""
        self.request = None
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
