"""Qt adapter for Profile-bound Session state; all private data stays in RAM."""
from __future__ import annotations

from copy import deepcopy

from PySide6.QtCore import (
    Property,
    QDateTime,
    QLocale,
    QObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)

from .config import save_config
from .expiry_clock import ExpiryClock
from .i18n import locale_for_language, translate
from .session_history_view import (
    live_presentations,
    opened_entry,
    page_cursor,
    presented_history,
    search_page,
)
from .session_projection import active_session, history_page, timestamp
from .session_transport import SessionError, SessionTransport


class SessionController(QObject):
    changed = Signal()
    entryOpened = Signal()
    timelineUpdated = Signal(str)
    contextCleared = Signal()
    _ready = Signal(object)

    def __init__(self, backend):
        super().__init__(backend)
        self.backend = backend
        self.transport = SessionTransport(lambda: backend.cfg)
        self._clock = ExpiryClock()
        self._foreground = True
        self._session = {}
        self._moments = []
        self._sessions = []
        self._timeline = {}
        self._error = ""
        self._serial = 0
        self._running = 0
        self._caps = {}
        self._loaded = False
        self._history_loaded = False
        self._history_cursor = ""
        self._search = {}
        self._view_epoch = getattr(self, "_view_epoch", 0) + 1
        self._ready.connect(self._apply)
        backend.demoModeChanged.connect(self._demo_changed)
        self._deadline_timer = QTimer(self)
        self._deadline_timer.setInterval(1000)
        self._deadline_timer.timeout.connect(self._expire)
        self._deadline_timer.start()

    @Property("QVariantMap", notify=changed)
    def state(self):
        return {"session_id": self._session.get("session_id", ""),
            "runtime_state": self._session.get("runtime_state", ""),
            "mood": self._session.get("selected_mood", ""),
            "presence": self._session.get("selected_presence", ""),
            "persona": self._session.get("dj_persona", ""),
            "moments": deepcopy(self._moments), "sessions": deepcopy(self._sessions),
            "timeline": deepcopy(self._timeline), "search": deepcopy(self._search), "error": self._error,
            "profile_confirmation_required": not bool(self.backend.cfg.explicit_profile_id),
            "history_available": self._history_supported(), "search_available": self._search_supported(),
            "loaded": self._loaded, "history_loaded": self._history_loaded,
            "has_more_sessions": bool(self._history_cursor)}

    @Slot(str, result=str)
    def formatTimestamp(self, value):
        if timestamp(value) is None:
            return ""
        parsed = QDateTime.fromString(value, Qt.DateFormat.ISODateWithMs)
        if not parsed.isValid():
            parsed = QDateTime.fromString(value, Qt.DateFormat.ISODate)
        if not parsed.isValid():
            return ""
        language = self.backend.cfg.language
        return QLocale(locale_for_language(language)).toString(parsed.toLocalTime(), translate(language, "session_datetime_format"))

    @Property(bool, notify=changed)
    def busy(self):
        return bool(self._running)

    def invalidate(self):
        self._serial += 1
        self._running = 0
        self._session = {}
        self._moments = []
        self._sessions = []
        self._timeline = {}
        self._caps = {}
        self._loaded = False
        self._history_loaded = False
        self._history_cursor = ""
        self._search = {}
        self._view_epoch = getattr(self, "_view_epoch", 0) + 1
        self._error = ""
        self.changed.emit()
        self.contextCleared.emit()

    @Slot(bool)
    def setForeground(self, foreground):
        if foreground == self._foreground:
            return
        self._foreground = foreground
        # Unfocused/background app loses ephemeral display authority, not the server Session.
        self.invalidate()
        if foreground:
            self.refresh()

    def _demo_changed(self):
        self.invalidate()
        if self.backend.demoMode:
            self._demo_action("start", "groove")

    def _demo_action(self, action, value):
        # Product demo is visibly labelled and never enters the native grant decoder.
        if action == "start":
            if value not in {"chill", "groove", "energy", "party"}:
                return
            self._session = {"session_id": "demo-session", "runtime_state": "active",
                             "selected_mood": value, "broadcast": {}}
        elif action == "end":
            self._session = {}
        elif action in {"history", "history_more"}:
            self._history_loaded = True
        self._loaded = True
        self.changed.emit()

    def _expire(self):
        now = self._clock.now()
        projected = live_presentations(self._session, now=now)
        changed = projected != self._moments
        self._moments = projected
        if self._timeline:
            retained = [row for row in self._timeline.get("entries", [])
                        if (timestamp(row.get("retained_until")) or 0) > now]
            if retained != self._timeline.get("entries", []):
                self._timeline = {**self._timeline, "entries": retained}
                changed = True
        if self._search:
            retained_matches = [row for row in self._search.get("matches", [])
                                if (timestamp(row.get("retained_until")) or 0) > now]
            if retained_matches != self._search.get("matches", []):
                self._search = {}
                self._error = "unavailable"
                changed = True
        if changed:
            self.changed.emit()

    def _search_supported(self):
        features = self._caps.get("capabilities", {})
        versions = self._caps.get("contract_versions", {})
        return (self._history_supported() and isinstance(features, dict) and isinstance(versions, dict)
                and features.get("session_flow_text_search") is True
                and type(versions.get("session_flow_text_search")) is int
                and versions["session_flow_text_search"] == 1)

    def _history_supported(self):
        features = self._caps.get("capabilities", {})
        versions = self._caps.get("contract_versions", {})
        return (isinstance(features, dict) and isinstance(versions, dict)
                and features.get("session_conversation_history") is True
                and type(versions.get("session_history_entries")) is int
                and versions["session_history_entries"] == 2)

    @Slot(str)
    def confirmProfile(self, expected_profile_id):
        cfg = self.backend.cfg
        if not cfg.paired or not cfg.device_token or not expected_profile_id or expected_profile_id != cfg.active_profile_id:
            self._error = "context_changed"
            self.changed.emit()
            return
        # Explicit user selection of the current server-resolved mapping; never a name match.
        cfg.explicit_profile_id = expected_profile_id
        save_config(self.backend.config_path, cfg)
        self.backend._clear_profile_scoped_caches()
        self.backend.settingsChanged.emit()
        self.refresh()

    @Slot()
    def refresh(self):
        self._launch("refresh")

    @Slot(str)
    def start(self, mood):
        self._launch("start", mood)

    @Slot(str)
    def end(self, expected_session_id):
        if expected_session_id != self._session.get("session_id") or not expected_session_id:
            self._error = "context_changed"
            self.changed.emit()
            return
        self._launch("end", expected_session_id)

    @Slot()
    def loadHistory(self):
        self._launch("history")

    @Slot()
    def moreHistory(self):
        if self._history_cursor:
            self._launch("history_more", self._history_cursor)

    @Slot(str)
    def openSaved(self, session_id):
        if self._running:
            return
        self._view_epoch += 1
        self._search = {}
        self._launch("timeline", session_id)

    @Slot(str)
    def refreshSaved(self, anchor_entry_id=""):
        sid = self._timeline.get("session", {}).get("session_id")
        if sid:
            self._launch("timeline_refresh", {"session_id": sid, "entry_id": anchor_entry_id,
                "page_cursor": self._timeline.get("_page_cursor")})

    @Slot()
    def firstEntries(self):
        sid = self._timeline.get("session", {}).get("session_id")
        if sid:
            self._launch("timeline_page", {"session_id": sid, "cursor": ""})

    @Slot()
    def nextEntries(self):
        sid = self._timeline.get("session", {}).get("session_id")
        cursor = self._timeline.get("next_cursor")
        if sid and cursor:
            self._launch("timeline_page", {"session_id": sid, "cursor": cursor,
                "revision": self._timeline["revision"]})

    @Slot()
    def closeSaved(self):
        self._view_epoch += 1
        self._timeline = {}
        self._search = {}
        self.changed.emit()

    @Slot()
    def clearSearch(self):
        self._view_epoch += 1
        self._search = {}
        self.changed.emit()

    @Slot(str, str)
    def search(self, session_id, query):
        if self._running:
            return
        query = query.strip()
        if not session_id or not 1 <= len(query) <= 200:
            return
        self._view_epoch += 1
        self._search = {}
        self._launch("search", {"session_id": session_id, "query": query, "cursor": ""})

    @Slot()
    def moreSearch(self):
        if self._search.get("next_cursor"):
            self._launch("search_more", {"session_id": self._search["session_id"],
                "query": self._search["query"], "cursor": self._search["next_cursor"],
                "revision": self._search["revision"]})

    @Slot(str, str)
    def openEntry(self, session_id, entry_id):
        if self._running:
            return
        self._view_epoch += 1
        self._launch("open_entry", {"session_id": session_id, "entry_id": entry_id})

    def _launch(self, action, value=""):
        if not self._foreground or self._running:
            return
        if self.backend.demoMode:
            self._demo_action(action, value)
            return
        if not self.backend.cfg.explicit_profile_id:
            self._error = "profile_required"
            self.changed.emit()
            return
        try:
            binding = self.transport.binding()
        except SessionError as exc:
            self.invalidate()
            self._error = exc.category
            self.changed.emit()
            return
        if action in {"history", "history_more", "timeline", "timeline_refresh", "timeline_page", "open_entry", "search", "search_more"} and not self._history_supported():
            self._error = "unsupported"
            self.changed.emit()
            return
        if action in {"search", "search_more"} and not self._search_supported():
            self._error = "unsupported"
            self.changed.emit()
            return
        view_epoch = self._view_epoch
        self._serial += 1
        serial = self._serial
        self._running = serial
        self._error = ""
        self.changed.emit()

        def worker():
            result = {"serial": serial, "binding": binding, "action": action, "view_epoch": view_epoch}
            try:
                if action in {"history", "history_more"}:
                    result["history"] = history_page(self.transport.history(binding, cursor=value), now=self._clock.now())
                    page_cursor(result["history"].get("next_cursor"))
                elif action == "timeline":
                    result["timeline"] = presented_history(history_page(self.transport.timeline(binding, value), session_id=value, now=self._clock.now()))
                elif action in {"timeline_refresh", "timeline_page"}:
                    sid = value["session_id"]
                    if action == "timeline_page":
                        response = self.transport.timeline(binding, sid, window=None, cursor=value["cursor"])
                    elif value.get("page_cursor") is not None:
                        try:
                            response = self.transport.timeline(binding, sid, window=None, cursor=value["page_cursor"])
                            response = {**response, "_page_cursor": value["page_cursor"]}
                        except SessionError as exc:
                            if exc.category != "conflict":
                                raise
                            # Changed grant/revision invalidates the cursor: re-read only the visible anchor.
                            response = self.transport.timeline(binding, sid, window="anchor", anchor_entry_id=value["entry_id"]) if value["entry_id"] else self.transport.timeline(binding, sid)
                    elif value["entry_id"]:
                        response = self.transport.timeline(binding, sid, window="anchor", anchor_entry_id=value["entry_id"])
                    else:
                        response = self.transport.timeline(binding, sid)
                    result["timeline"] = presented_history(history_page(response, session_id=sid, now=self._clock.now()))
                    if action == "timeline_page" and value.get("revision") and response["revision"] != value["revision"]:
                        raise SessionError("conflict")
                    if action == "timeline_page":
                        result["timeline"]["_page_cursor"] = value["cursor"]
                    result["reading_anchor"] = value.get("entry_id", "")
                elif action in {"search", "search_more"}:
                    result["search"] = search_page(self.transport.search(binding, value["session_id"], value["query"], cursor=value["cursor"]), value["session_id"], value["query"], now=self._clock.now())
                    if action == "search_more" and result["search"]["revision"] != value["revision"]:
                        raise SessionError("conflict")
                elif action == "open_entry":
                    sid, eid = value["session_id"], value["entry_id"]
                    opened_entry(self.transport.open_entry(binding, sid, eid), sid, eid, now=self._clock.now())
                    result["timeline"] = presented_history(history_page(self.transport.timeline(binding, sid, window="anchor", anchor_entry_id=eid), session_id=sid, now=self._clock.now()))
                    if not any(row["entry_id"] == eid for row in result["timeline"]["entries"]):
                        raise SessionError("unavailable")
                    result["timeline"]["selected_entry_id"] = eid
                else:
                    if action == "start":
                        self.transport.start(binding, value)
                    elif action == "end":
                        self.transport.end(binding, value)
                    # A pure current read, never a write replay or optimistic local Session.
                    result["session"] = active_session(self.transport.active(binding))
                    try:
                        result["capabilities"] = self.transport.capabilities(binding)
                    except SessionError:
                        result["capabilities"] = {}
            except SessionError as exc:
                result["error"] = exc.category
            except (AttributeError, KeyError, OverflowError, TypeError, ValueError):
                result["error"] = "invalid"
            self._ready.emit(result)

        self.backend._executor.submit(worker)

    @Slot(object)
    def _apply(self, result):
        if result["serial"] != self._running:
            return
        self._running = 0
        try:
            if result["binding"] != self.transport.binding():
                self.invalidate()
                return
        except SessionError:
            self.invalidate()
            return
        history_action = result["action"] in {"history", "history_more", "timeline", "timeline_refresh", "timeline_page", "search", "search_more", "open_entry"}
        if history_action and result.get("view_epoch") != self._view_epoch:
            self.changed.emit()
            return
        if "error" in result and history_action and result["error"] not in {"denied", "context_changed", "unpaired"}:
            self._search = {}
            self._timeline = {}
            self._error = result["error"]
            self.changed.emit()
            return
        if "error" in result:
            self._search = {}
            self._session = {}
            self._moments = []
            self._timeline = {}
            self._sessions = []
            self._loaded = False
            self._history_loaded = False
            self._error = result["error"]
        else:
            if "session" in result:
                self._loaded = True
                self._session = result["session"]
                self._moments = live_presentations(self._session, now=self._clock.now())
                self._caps = result.get("capabilities", {})
                if not self._history_supported():
                    self._timeline = {}
                    self._sessions = []
                    self._history_cursor = ""
                    self._history_loaded = False
                    self._search = {}
                elif not self._search_supported():
                    self._search = {}
            if "history" in result:
                self._history_loaded = True
                rows = result["history"]["sessions"]
                # Cursor pages remain server-ordered; duplicate identity is replaced, not appended twice.
                if result["action"] == "history_more":
                    incoming_ids = {row["session_id"] for row in rows}
                    self._sessions = [row for row in self._sessions if row["session_id"] not in incoming_ids] + rows
                else:
                    self._sessions = rows
                self._history_cursor = page_cursor(result["history"].get("next_cursor"))
            if "search" in result:
                incoming = result["search"]
                if result["action"] == "search_more":
                    incoming_ids = {row["entry_id"] for row in incoming["matches"]}
                    incoming["matches"] = [row for row in self._search.get("matches", []) if row["entry_id"] not in incoming_ids] + incoming["matches"]
                self._search = incoming
            if "timeline" in result:
                self._timeline = result["timeline"]
                # A fresh projection replaces the whole window, including withdrawn prose.
                self._search = {}
        # Worker results may have waited on the GUI queue beyond their original deadline.
        self._expire()
        self.changed.emit()
        if "timeline" in result and "error" not in result:
            self.timelineUpdated.emit(result.get("reading_anchor", self._timeline.get("selected_entry_id", "")))
        if result["action"] == "open_entry" and "error" not in result:
            self.entryOpened.emit()
