"""Qt adapter for Profile-bound Session state; all private data stays in RAM."""
from __future__ import annotations

from copy import deepcopy
from math import isfinite
from uuid import uuid4

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
from .session_artwork import MomentImages
from .session_artwork_prepare import ArtworkPreparation
from .session_current_reply import current_reply, moment_reference, reply_valid
from .session_forecast import ForecastReceiver, forecast_supported
from .session_forecast_image import ForecastImages
from .session_history_view import (
    accepted_question,
    confirmed_question_entry,
    conversation_entries,
    live_presentations,
    opened_entry,
    page_cursor,
    presented_history,
    search_page,
)
from .session_playback_control import PlaybackControl
from .session_projection import (
    active_session,
    history_page,
    session_playback,
    timestamp,
)
from .session_transport import SessionError, SessionTransport


class SessionController(QObject):
    changed = Signal()
    forecastImageChanged = Signal()
    forecastImageAboutToChange = Signal()
    artworkChanged = Signal()
    artworkAboutToChange = Signal()
    entryOpened = Signal()
    questionConfirmed = Signal(str)
    currentReplyReady = Signal()
    pendingQuestionReady = Signal()
    searchUpdated = Signal()
    historyUpdated = Signal()
    archivePositioned = Signal(str, float)
    timelineUpdated = Signal(str)
    timelinePositioned = Signal(str, float)
    selectionInvalidated = Signal()
    contextCleared = Signal()
    _ready = Signal(object)

    def __init__(self, backend):
        super().__init__(backend)
        self.backend = backend
        self.transport = SessionTransport(lambda: backend.cfg)
        self._clock = ExpiryClock()
        self._foreground = True
        self._session = {}
        self._forecast = ForecastReceiver()
        self._forecast_dirty = False
        self._moments = []
        self._conversation = []
        self._retained_flow = []
        self._pending_question = {}
        self._pending_question_binding = None
        self._current_reply = {}
        self._current_reply_binding = None
        self._current_reply_dirty = False
        self._question_reference = {}
        self._selection = {}
        self._selection_source = "timeline"
        self._question_status = ""
        self._question_receipt = {}
        self._sessions = []
        self._history_dirty = False
        self._history_selection_dirty = False
        self._timeline = {}
        self._timeline_trail = []
        self._error = ""
        self._serial = 0
        self._running = 0
        self._running_action = ""
        self._question_running = 0
        self._question_epoch = 0
        self._last_current_read = 0
        self._reconcile_question = False
        self._caps = {}
        self._loaded = False
        self._history_loaded = False
        self._history_cursor = ""
        self._history_pages = 1
        self._history_start = ""
        self._history_scope = None
        self._history_before = None
        self._history_trail = []
        self._history_reset = False
        self._search = {}
        self._view_epoch = getattr(self, "_view_epoch", 0) + 1
        self._forecast_images = ForecastImages(self)
        self._forecast_images.changed.connect(self.forecastImageChanged.emit)
        self._forecast_images.aboutToChange.connect(self.forecastImageAboutToChange.emit)
        self.changed.connect(self._forecast_images.sync)
        self._moment_images = MomentImages(self)
        self._moment_images.changed.connect(self.artworkChanged.emit)
        self._moment_images.aboutToChange.connect(self.artworkAboutToChange.emit)
        self.changed.connect(self._moment_images.sync)
        self._artwork_prepare = ArtworkPreparation(self)
        self.changed.connect(self._artwork_prepare.sync)
        self._playback_control = PlaybackControl(self)
        self.changed.connect(self._playback_control.sync)
        self._ready.connect(self._apply)
        backend.demoModeChanged.connect(self._demo_changed)
        self._deadline_timer = QTimer(self)
        self._deadline_timer.setInterval(1000)
        self._deadline_timer.timeout.connect(self._expire)
        self._deadline_timer.start()

    @Property("QVariantMap", notify=changed)
    def state(self):
        if self._expire_history_headers(self._clock.now()):
            self._history_dirty = True
        if self._pending_question and not self._pending_question_valid():
            self._withdraw_question()
            self._current_reply_dirty = True
            self._question_status = "reference_unavailable"
        if self._current_reply and not self._current_reply_valid():
            self._current_reply = {}
            self._current_reply_binding = None
            self._current_reply_dirty = True
            self._question_status = "reference_unavailable"
        if self._forecast.expire(self._clock.now()):
            self._forecast_dirty = True
        return {"session_id": self._session.get("session_id", ""),
            "runtime_state": self._session.get("runtime_state", ""),
            "playback": session_playback(self._session),
            "artwork_prepare": self._artwork_prepare.snapshot(),
            "playback_control": self._playback_control.snapshot(),
            "forecast_supported": forecast_supported(self._session, self._caps),
            "forecast": self._forecast.snapshot(),
            "mood": self._session.get("selected_mood", ""),
            "presence": self._session.get("selected_presence", ""),
            "persona": self._session.get("dj_persona", ""),
            "composer_available": self._composer_supported(), "pending_question": deepcopy(self._pending_question), "current_reply": deepcopy(self._current_reply), "conversation": deepcopy(self._conversation), "retained_flow": deepcopy(self._retained_flow),
            "selection": deepcopy(self._selection), "question_status": self._question_status,
            "moments": deepcopy(self._moments), "sessions": deepcopy(self._sessions),
            "timeline": deepcopy(self._timeline), "search": deepcopy(self._search), "error": self._error,
            "profile_confirmation_required": not bool(self.backend.cfg.explicit_profile_id),
            "history_available": self._history_supported(), "search_available": self._search_supported(),
            "loaded": self._loaded, "history_loaded": self._history_loaded,
            "has_previous_entries": bool(self._timeline_trail),
            "search_limit_reached": bool(self._search.get("next_cursor")) and self._search.get("_pages", 1) >= 5,
            "history_limit_reached": bool(self._history_cursor) and self._history_pages >= 5,
            "has_older_sessions": bool(self._history_cursor) and self._history_pages >= 5,
            "has_newer_sessions": bool(self._history_trail), "archive_older_window": bool(self._history_start),
            "archive_window_reset": self._history_reset,
            "has_more_sessions": bool(self._history_cursor) and self._history_pages < 5}

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

    @Property("QVariantMap", notify=forecastImageChanged)
    def forecastImage(self):
        return self._forecast_images.snapshot()

    @Slot(bool)
    def setForecastImagesVisible(self, visible):
        self._forecast_images.set_visible(visible)

    @Property("QVariantMap", notify=artworkChanged)
    def momentArtwork(self):
        return self._moment_images.snapshot()

    @Slot(bool)
    def setMomentArtworkVisible(self, visible):
        if not visible:
            self._artwork_prepare.hide()
        self._moment_images.set_visible(visible)

    @Slot(bool)
    def setPlaybackControlsVisible(self, visible):
        changed = self._playback_control.visible != bool(visible)
        self._playback_control.set_visible(visible)
        if changed:
            QTimer.singleShot(0, self.changed.emit)

    @Slot(str, str, str, result=bool)
    def playbackCommand(self, session_id, item_id, command):
        return self._playback_control.start(session_id, item_id, command)

    @Slot(str, str, result=bool)
    def readPlaybackVolume(self, session_id, item_id):
        return self._playback_control.read_volume(session_id, item_id)

    @Slot(str, str, int, int, result=bool)
    def setPlaybackVolume(self, session_id, item_id, lease, value):
        return self._playback_control.set_volume(session_id, item_id, lease, value)

    @Slot(str, str, result=bool)
    def readPlaybackFavorite(self, session_id, item_id):
        return self._playback_control.read_favorite(session_id, item_id)

    @Slot(str, str, int, bool, result=bool)
    def setPlaybackFavorite(self, session_id, item_id, lease, value):
        return self._playback_control.set_favorite(session_id, item_id, lease, value)

    @Slot()
    def cancelPlaybackIntent(self):
        # Revocation is immediate; notification must not re-enter a QML state binding.
        self._playback_control.hide()
        QTimer.singleShot(0, self.changed.emit)

    @Slot()
    def refreshPlayback(self):
        self._playback_control.refresh()

    @Slot(str, str, result=bool)
    def prepareArtwork(self, session_id, moment_id):
        return self._artwork_prepare.start(session_id, moment_id)

    @Slot()
    def shutdownImages(self):
        self._forecast_images.shutdown()
        self._moment_images.shutdown()
        self._artwork_prepare.shutdown()
        self._playback_control.shutdown()

    @Property(bool, notify=changed)
    def busy(self):
        return bool(self._running or self._artwork_prepare.running or self._playback_control.running)

    @Property(bool, notify=changed)
    def lifecycleBusy(self):
        return bool(self._running and self._running_action in {"start", "end"})

    @Property(bool, notify=changed)
    def questionBusy(self):
        return bool(self._question_running)

    def _withdraw_question(self):
        self._history_selection_dirty = False
        self._pending_question = {}
        self._pending_question_binding = None
        self._question_reference = {}
        self._current_reply = {}
        self._current_reply_binding = None
        # Revoke display authority without pretending that an in-flight POST was cancelled.
        self._question_epoch += 1
        self._question_receipt = {}
        self._question_status = ""
        self._selection = {}
        self._reconcile_question = False

    def invalidate(self):
        self._playback_control.hide(reset=True)
        self._forecast.reset()
        self._forecast_dirty = False
        self._serial += 1
        self._running = 0
        self._running_action = ""
        self._question_running = 0
        self._withdraw_question()
        self._session = {}
        self._moments = []
        self._conversation = []
        self._retained_flow = []
        self._selection = {}
        self._selection_source = "timeline"
        self._question_status = ""
        self._sessions = []
        self._timeline = {}
        self._timeline_trail = []
        self._caps = {}
        self._loaded = False
        self._history_loaded = False
        self._history_cursor = ""
        self._history_pages = 1
        self._history_start = ""
        self._history_scope = None
        self._history_before = None
        self._history_trail = []
        self._history_reset = False
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
        elif action in {"history", "history_more", "history_refresh"}:
            self._history_loaded = True
        self._loaded = True
        self.changed.emit()

    def _expire_history_headers(self, now):
        expired = {row["session_id"] for row in self._sessions
            if row.get("_history_deadline") is not None and row["_history_deadline"] <= now}
        deadline = self._timeline.get("_session_deadline")
        if deadline is not None and deadline <= now:
            expired.add(self._timeline.get("session", {}).get("session_id"))
        if not expired:
            return False
        self._sessions = [row for row in self._sessions if row["session_id"] not in expired]
        self._history_cursor = ""
        # Keep the displayed-page budget so the next fresh traversal need not collapse.

        if self._timeline.get("session", {}).get("session_id") in expired:
            self._timeline = {}
            self._timeline_trail = []
        if self._search.get("session_id") in expired:
            self._search = {}
        if self._selection.get("kind") == "selected_entry" and self._selection.get("session_id") in expired:
            self._withdraw_question()
            self._history_selection_dirty = True
        return True

    def _expire(self):
        now = self._clock.now()
        headers_expired = self._expire_history_headers(now) or self._history_dirty
        self._history_dirty = False
        if self._history_selection_dirty:
            self._history_selection_dirty = False
            self.selectionInvalidated.emit()
        receipt_expired = self._question_receipt.get("retained_until", float("inf")) <= now
        if receipt_expired:
            self._question_receipt = {}
            self._question_status = ""
        projected = live_presentations(self._session, now=now)
        forecast_changed = self._forecast.expire(now) or self._forecast_dirty
        self._forecast_dirty = False
        changed = headers_expired or forecast_changed or receipt_expired or projected != self._moments or self._current_reply_dirty
        self._current_reply_dirty = False
        if self._pending_question and not self._pending_question_valid():
            self._withdraw_question()
            self._question_status = "reference_unavailable"
            changed = True
        if self._question_reference and self._question_reference != moment_reference(self._session, self._question_reference["selected"], now=now):
            self._withdraw_question()
            changed = True
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
        retained_flow = [row for row in self._retained_flow if (timestamp(row.get("retained_until")) or 0) > now]
        if retained_flow != self._retained_flow:
            self._retained_flow = retained_flow
            changed = True
        retained_conversation = [row for row in self._conversation if (timestamp(row.get("retained_until")) or 0) > now]
        if retained_conversation != self._conversation:
            self._conversation = retained_conversation
            changed = True
        if not self._selection_valid():
            self._withdraw_question()
            self._question_status = "reference_unavailable"
            self.selectionInvalidated.emit()
            changed = True
        if self._current_reply and not self._current_reply_valid():
            self._current_reply = {}
            self._current_reply_binding = None
            self._question_status = "reference_unavailable"
            changed = True
        if changed:
            self.changed.emit()

    def _pending_question_valid(self):
        try:
            return (bool(self._question_running) and self._foreground and self._composer_supported()
                and self._pending_question_binding == self.transport.binding()
                and self._pending_question.get("session_id") == self._session.get("session_id")
                and self._selection_valid()
                and (not self._question_reference or self._question_reference == moment_reference(
                    self._session, self._question_reference["selected"], now=self._clock.now())))
        except SessionError:
            return False

    def _current_reply_valid(self):
        try:
            return (self._composer_supported() and self._foreground
                and self._current_reply_binding == self.transport.binding()
                and reply_valid(self._current_reply, self._session, now=self._clock.now()))
        except SessionError:
            return False

    def _composer_supported(self):
        cfg = self.backend.cfg
        return (self._history_supported() and self._caps.get("capabilities", {}).get("ask_dj_contextual_dialogue") is True
                and type(self._caps.get("contract_versions", {}).get("ask_dj_contextual_dialogue")) is int
                and self._caps["contract_versions"]["ask_dj_contextual_dialogue"] == 1
                and self._session.get("runtime_state") == "active"
                and cfg.explicit_profile_id == cfg.active_profile_id and bool(cfg.explicit_profile_id)
                and not cfg.private_session and cfg.active_profile_type in {"personal", "household"}
                and cfg.active_profile_privacy_mode == "private")

    def _selection_valid(self):
        if not self._selection:
            return True
        selected = self._selection
        if selected["kind"] == "selected_moment":
            return selected["session_id"] == self._session.get("session_id") and any(row["moment_id"] == selected["moment_id"] for row in live_presentations(self._session, now=self._clock.now()))
        return self._entry_selection_valid(selected, self._selection_source)

    def _entry_selection_valid(self, selected, source):
        if source == "flow":
            session_id, rows = self._session.get("session_id"), self._retained_flow
        else:
            session_id, rows = self._timeline.get("session", {}).get("session_id"), self._timeline.get("entries", [])
        return (selected["session_id"] == session_id
                and any(row["session_id"] == selected["session_id"] and row["entry_id"] == selected["entry_id"]
                        and (timestamp(row.get("retained_until")) or 0) > self._clock.now() for row in rows))

    @Slot()
    def clearSelection(self):
        if self._selection:
            self._selection = {}
            self.changed.emit()

    @Slot(str, str, result=bool)
    def selectMoment(self, session_id, moment_id):
        self._history_selection_dirty = False
        self._selection = {"kind": "selected_moment", "session_id": session_id, "moment_id": moment_id}
        valid = self._selection_valid()
        if not valid:
            self._selection = {}
        self.changed.emit()
        return valid

    @Slot(str, str, result=bool)
    def selectEntry(self, session_id, entry_id):
        self._selection_source = "timeline"
        self._history_selection_dirty = False
        self._selection = {"kind": "selected_entry", "session_id": session_id, "entry_id": entry_id}
        valid = self._selection_valid()
        if not valid:
            self._selection = {}
        self.changed.emit()
        return valid

    @Slot(str, str, result=bool)
    def selectFlowEntry(self, session_id, entry_id):
        # A Flow click cannot borrow authority from a separately retained detail page.
        if not self._foreground or self._running or self._question_running or not self._composer_supported():
            return False
        selected = {"kind": "selected_entry", "session_id": session_id, "entry_id": entry_id}
        if not self._entry_selection_valid(selected, "flow"):
            return False
        self._history_selection_dirty = False
        self._selection_source = "flow"
        self._selection = selected
        self.changed.emit()
        return True

    @Slot(str, result=bool)
    def sendQuestion(self, body):
        if self.busy or self._question_running or not self._foreground or not self._composer_supported() or not isinstance(body, str) or not 1 <= len(body.strip()) <= 4000:
            return False
        if not self._selection_valid():
            self._selection = {}
            self._error = "context_changed"
            self.selectionInvalidated.emit()
            self.changed.emit()
            return False
        request = {"text": body.strip(), "client_message_id": "pi-turn-" + uuid4().hex,
            "session_id": self._session["session_id"], "selected": deepcopy(self._selection)}
        request["live_reference"] = moment_reference(self._session, request["selected"], now=self._clock.now())
        self._launch("question", request)
        return bool(self._question_running)

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
    def clearArchive(self):
        had = bool(self._sessions or self._history_loaded or self._history_cursor or self._history_trail)
        self._view_epoch += 1
        self._sessions = []
        self._history_loaded = False
        self._history_cursor = ""
        self._history_pages = 1
        self._history_start = ""
        self._history_scope = None
        self._history_before = None
        self._history_trail = []
        self._history_reset = False
        if had:
            self.changed.emit()

    def _archive_request(self, pages=None):
        return {"pages": self._history_pages if pages is None else pages, "start": self._history_start,
            "scope": self._history_scope, "before": self._history_before, "trail": deepcopy(self._history_trail)}

    @Slot()
    def loadHistory(self):
        self._launch("history", {"pages": 1, "window_change": True})

    @Slot()
    def moreHistory(self):
        if self._history_cursor and self._history_pages < 5:
            self._launch("history_more", self._archive_request(self._history_pages + 1))

    @Slot()
    def refreshArchive(self):
        if self._history_loaded and not self._timeline:
            self._launch("history_refresh", self._archive_request())

    @Slot(str, float)
    def olderSessions(self, session_id="", offset=0):
        if self._timeline or not self._history_cursor or self._history_pages < 5:
            return
        previous = self._archive_request()
        previous.pop("trail")
        if (any(row["session_id"] == session_id for row in self._sessions)
                and type(offset) in (int, float) and isfinite(offset) and abs(offset) <= 1_000_000):
            previous["reading"] = {"session_id": session_id, "offset": float(offset)}
        last = self._sessions[-1] if self._sessions else None
        before = (timestamp(last["created_at"]), last["session_id"]) if last else None
        self._launch("history_more", {"pages": 1, "start": self._history_cursor,
            "scope": self._history_scope, "before": before,
            "trail": (self._history_trail + [previous])[-32:], "window_change": True})

    @Slot()
    def newerSessions(self):
        if self._timeline or not self._history_trail:
            return
        self._launch("history_more", {**deepcopy(self._history_trail[-1]),
            "trail": deepcopy(self._history_trail[:-1]), "window_change": True})

    @Slot()
    def readCurrentHistory(self):
        sid = self._session.get("session_id")
        if not sid or self._running:
            return
        self._view_epoch += 1
        self._search = {}
        self._launch("timeline_page", {"session_id": sid, "cursor": ""})

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
        if sid and self._timeline.get("_prefix_pages"):
            self._launch("timeline_extend", {"session_id": sid, "pages": self._timeline["_prefix_pages"],
                "reading_anchor": anchor_entry_id})
        elif sid:
            self._launch("timeline_refresh", {"session_id": sid, "entry_id": anchor_entry_id,
                "page_cursor": self._timeline.get("_page_cursor")})

    @Slot(str, float)
    def extendEntries(self, anchor_entry_id="", offset=0):
        sid = self._timeline.get("session", {}).get("session_id")
        pages = self._timeline.get("_prefix_pages", 1)
        if (sid and self._timeline.get("_page_cursor") == "" and self._timeline.get("next_cursor")
                and type(pages) is int and 1 <= pages < 5):
            value = {"session_id": sid, "pages": pages + 1}
            if (any(row["entry_id"] == anchor_entry_id for row in self._timeline.get("entries", []))
                    and type(offset) in (int, float) and isfinite(offset) and abs(offset) <= 1_000_000):
                value["reading"] = {"entry_id": anchor_entry_id, "offset": float(offset)}
            self._launch("timeline_extend", value)

    def _read_timeline_prefix(self, binding, session_id, pages, view_epoch, serial):
        if type(pages) is not int or not 1 <= pages <= 5:
            raise SessionError("invalid")
        cursor, revision, rows, seen_ids, seen_cursors = "", None, [], set(), set()
        def check():
            if (not self._foreground or self._view_epoch != view_epoch or self._running != serial
                    or self.transport.binding() != binding):
                raise SessionError("context_changed")
        for number in range(pages):
            check()
            page = history_page(self.transport.timeline(binding, session_id, window=None, cursor=cursor),
                session_id=session_id, now=self._clock.now())
            check()
            if len(page["entries"]) > 20 or (revision is not None and page["revision"] != revision):
                raise SessionError("invalid")
            revision = page["revision"]
            for row in page["entries"]:
                if row["entry_id"] in seen_ids or (rows and rows[-1]["order"] >= row["order"]):
                    raise SessionError("invalid")
                seen_ids.add(row["entry_id"])
                rows.append(row)
            cursor = page.get("next_cursor")
            if cursor and cursor in seen_cursors:
                raise SessionError("invalid")
            if cursor: seen_cursors.add(cursor)
            if not cursor: break
        return presented_history({**page, "entries": rows, "_page_cursor": "", "_prefix_pages": number + 1})

    @Slot()
    def firstEntries(self):
        sid = self._timeline.get("session", {}).get("session_id")
        if sid:
            self._launch("timeline_page", {"session_id": sid, "cursor": ""})

    @Slot()
    @Slot(str, float)
    def nextEntries(self, anchor_entry_id="", offset=0):
        sid = self._timeline.get("session", {}).get("session_id")
        cursor = self._timeline.get("next_cursor")
        if sid and cursor:
            self._launch("timeline_page", {"session_id": sid, "cursor": cursor,
                "revision": self._timeline["revision"],
                "trail": (self._timeline_trail + [self._timeline_descriptor(anchor_entry_id, offset)])[-32:]})

    def _timeline_descriptor(self, anchor_entry_id="", offset=0):
        if self._timeline.get("_prefix_pages"):
            target = {"prefix_pages": self._timeline["_prefix_pages"]}
        elif "_page_cursor" in self._timeline:
            target = {"window": None, "cursor": self._timeline["_page_cursor"]}
        elif self._timeline.get("window") == "anchor":
            target = {"window": "anchor", "anchor_entry_id": self._timeline["anchor_entry_id"]}
        else:
            target = {"window": "tail"}
        if (any(row["entry_id"] == anchor_entry_id for row in self._timeline.get("entries", []))
                and type(offset) in (int, float) and isfinite(offset) and abs(offset) <= 1_000_000):
            target["reading"] = {"entry_id": anchor_entry_id, "offset": float(offset)}
        return target

    @Slot()
    @Slot(str)
    def previousEntries(self, anchor_entry_id=""):
        sid = self._timeline.get("session", {}).get("session_id")
        if sid and self._timeline_trail:
            self._launch("timeline_previous", {"session_id": sid, "target": deepcopy(self._timeline_trail[-1]),
                "trail": deepcopy(self._timeline_trail[:-1]), "revision": self._timeline["revision"],
                "visible_anchor": anchor_entry_id if any(row["entry_id"] == anchor_entry_id for row in self._timeline.get("entries", []))
                    else next((row["entry_id"] for row in self._timeline.get("entries", [])), "")})

    @Slot()
    def closeSaved(self):
        self._view_epoch += 1
        self._timeline = {}
        self._timeline_trail = []
        self._search = {}
        self.changed.emit()

    @Slot()
    def clearSearch(self):
        self._view_epoch += 1
        had_search = bool(self._search)
        self._search = {}
        if had_search:
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
        if self._search.get("next_cursor") and self._search.get("_pages", 1) < 5:
            self._launch("search_more", {"session_id": self._search["session_id"],
                "query": self._search["query"], "pages": self._search.get("_pages", 1) + 1})

    @Slot()
    def refreshSearch(self):
        if self._search.get("query"):
            self._launch("search_refresh", {"session_id": self._search["session_id"],
                "query": self._search["query"], "pages": self._search.get("_pages", 1)})

    def _read_history(self, binding, value, view_epoch):
        try:
            return self._read_history_window(binding, value, view_epoch)
        except SessionError as exc:
            if not value.get("start") or exc.category != "conflict":
                raise
            # No session-list anchor endpoint exists. A revoked window cursor returns to newest.
            fresh = self._read_history_window(binding, {"pages": 1, "window_change": True}, view_epoch)
            fresh["_window_reset"] = True
            return fresh

    def _read_history_window(self, binding, value, view_epoch):
        start = page_cursor(value.get("start"))
        cursor, rows, cursors, scope = start, [], {start} if start else set(), None
        previous = value.get("before")
        for number in range(min(5, max(1, value.get("pages", 1)))):
            if not self._foreground or self._view_epoch != view_epoch:
                raise SessionError("context_changed")
            if self.transport.binding() != binding:
                raise SessionError("context_changed")
            page = history_page(self.transport.history(binding, cursor=cursor), now=self._clock.now())
            if len(page["sessions"]) > 20:
                raise SessionError("invalid")
            revision = page.get("revision")
            policy = page.get("retention_revision")
            if (page["sessions"] or page.get("next_cursor")) and (not isinstance(revision, str) or not revision or type(policy) is not int or policy < 0):
                raise SessionError("invalid")
            current = (revision, page.get("retention_days"), policy)
            if (scope is not None and current != scope) or (start and current != value.get("scope")):
                raise SessionError("conflict")
            scope = current
            for row in page["sessions"]:
                stamp = timestamp(row.get("created_at"))
                key = (stamp, row["session_id"]) if stamp is not None else None
                if key is None or (previous is not None and key >= previous) or any(old["session_id"] == row["session_id"] for old in rows):
                    raise SessionError("invalid")
                rows.append(row)
                previous = key
            cursor = page_cursor(page.get("next_cursor"))
            if cursor and cursor in cursors:
                raise SessionError("invalid")
            if cursor:
                cursors.add(cursor)
            if not cursor:
                break
        return {**page, "sessions": rows, "_pages": number + 1, "_start": start, "_scope": scope,
            "_trail": deepcopy(value.get("trail", [])), "_window_change": value.get("window_change", False),
            "_reading": deepcopy(value.get("reading", {})), "_before": value.get("before")}

    def _read_search(self, binding, value, view_epoch):
        # Re-read all displayed pages: no old body survives solely through pagination.
        cursor, rows, seen_cursors, revision = "", [], set(), None
        for number in range(min(5, max(1, value.get("pages", 1)))):
            if not self._foreground or self._view_epoch != view_epoch:
                raise SessionError("context_changed")
            page = search_page(self.transport.search(binding, value["session_id"], value["query"], cursor=cursor),
                value["session_id"], value["query"], now=self._clock.now())
            if revision is not None and page["revision"] != revision:
                raise SessionError("conflict")
            revision = page["revision"]
            # Core's search traversal is canonical, increasing and non-overlapping.
            for row in page["matches"]:
                if any(old["entry_id"] == row["entry_id"] or old["order"] >= row["order"] for old in rows):
                    raise SessionError("invalid")
                rows.append(row)
            cursor = page.get("next_cursor")
            if cursor and cursor in seen_cursors:
                raise SessionError("invalid")
            if cursor:
                seen_cursors.add(cursor)
            if not cursor:
                break
        return {**page, "matches": rows, "returned_count": len(rows), "_pages": number + 1}

    @Slot(str, str)
    def openEntry(self, session_id, entry_id):
        if self._running:
            return
        self._view_epoch += 1
        self._launch("open_entry", {"session_id": session_id, "entry_id": entry_id})

    def _launch(self, action, value=""):
        if not self._foreground:
            return
        if (self._artwork_prepare.running or self._playback_control.running) and action != "end":
            return
        # End supersedes reads, but never another lifecycle write. Late read results lose their ticket.
        if self._running and (action != "end" or self._running_action in {"start", "end"}):
            return
        if action == "question" and self._question_running:
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
        if action in {"history", "history_more", "history_refresh", "timeline", "timeline_refresh", "timeline_page", "timeline_previous", "timeline_extend", "open_entry", "search", "search_more", "search_refresh"} and not self._history_supported():
            self._error = "unsupported"
            self.changed.emit()
            return
        if action == "question" and not self._composer_supported():
            return
        if action in {"search", "search_more", "search_refresh"} and not self._search_supported():
            self._error = "unsupported"
            self.changed.emit()
            return
        view_epoch = self._view_epoch
        receipt_snapshot = deepcopy(self._question_receipt)
        selection_source = self._selection_source
        self._serial += 1
        serial = self._serial
        if action == "question":
            self._question_running = serial
        else:
            self._running = serial
            self._running_action = action
        if action in {"refresh", "start", "end"}:
            self._last_current_read = serial
        if action == "end":
            self._withdraw_question()
            self.contextCleared.emit()
        question_epoch = self._question_epoch
        self._error = ""
        if action == "question":
            self._pending_question = {"text": value["text"], "session_id": value["session_id"], "client_message_id": value["client_message_id"]}
            self._pending_question_binding = binding
            self._question_reference = deepcopy(value.get("live_reference", {}))
            self._current_reply = {}
            self._current_reply_binding = None
            self._question_receipt = {}
            self._question_status = "sending"
        self.changed.emit()
        if action == "question":
            self.pendingQuestionReady.emit()

        def check_conversation_read():
            running = self._question_running if action == "question" else self._running
            if (not self._foreground or serial != running or self.transport.binding() != binding
                    or (action == "question" and question_epoch != self._question_epoch)):
                raise SessionError("context_changed")

        def worker():
            result = {"serial": serial, "binding": binding, "action": action, "view_epoch": view_epoch, "question_epoch": question_epoch}
            try:
                if action == "question":
                    # Queued work must validate the original intent without a GUI getter/tick.
                    check_conversation_read()
                    expected_pending = {key: value[key] for key in ("text", "session_id", "client_message_id")}
                    if (not self._pending_question_valid() or self._pending_question != expected_pending
                            or self._question_reference != value.get("live_reference", {})):
                        raise SessionError("context_changed")
                    if (value.get("selected", {}).get("kind") == "selected_entry"
                            and not self._entry_selection_valid(value["selected"], selection_source)):
                        raise SessionError("context_changed")
                    response = self.transport.question(binding, value)
                    receipt = accepted_question(response, binding, value)
                    result["question_accepted"] = True
                    result["question_receipt"] = {"session_id": value["session_id"],
                        "client_message_id": value["client_message_id"], "turn_id": receipt["turn_id"],
                        "entry_ids": receipt["entry_ids"]}
                    result["expected_session_id"] = value["session_id"]
                    if question_epoch != self._question_epoch or not self._foreground:
                        raise SessionError("context_changed")
                    check_conversation_read()
                    fresh = active_session(self.transport.active(binding))
                    if fresh.get("session_id") != value["session_id"]:
                        raise SessionError("context_changed")
                    result["session"] = fresh
                    if receipt.get("history_scope") == "private_ephemeral":
                        result["private_response"] = True
                        result["current_reply"] = current_reply(response, binding, value, fresh, now=self._clock.now())
                    else:
                        result.update(self._read_conversation(binding, value["session_id"], result["question_receipt"], check_conversation_read))
                elif action in {"history", "history_more", "history_refresh"}:
                    result["history"] = self._read_history(binding, value, view_epoch)
                elif action == "timeline":
                    result["timeline"] = presented_history(history_page(self.transport.timeline(binding, value), session_id=value, now=self._clock.now()))
                elif action == "timeline_extend":
                    result["timeline"] = self._read_timeline_prefix(binding, value["session_id"], value["pages"], view_epoch, serial)
                    result["timeline_trail"] = []
                    result["timeline_prefix"] = True
                    if value.get("reading"):
                        result["reading_restore"] = value["reading"]
                    elif value.get("reading_anchor"):
                        result["reading_anchor"] = value["reading_anchor"]
                elif action == "timeline_previous":
                    sid, target = value["session_id"], value["target"]
                    try:
                        if target.get("prefix_pages"):
                            decoded = self._read_timeline_prefix(binding, sid, target["prefix_pages"], view_epoch, serial)
                        else:
                            request = {key: value for key, value in target.items() if key != "reading"}
                            response = self.transport.timeline(binding, sid, **request)
                            decoded = history_page(response, session_id=sid, now=self._clock.now())
                        if target.get("window") == "anchor" and not any(row["entry_id"] == target["anchor_entry_id"] for row in decoded["entries"]):
                            raise SessionError("unavailable")
                        if decoded["revision"] != value["revision"]:
                            raise SessionError("conflict")
                        result["timeline"] = presented_history(decoded)
                        result["timeline_prefix"] = bool(target.get("prefix_pages"))
                        if "prefix_pages" not in target and target.get("window") is None:
                            result["timeline"]["_page_cursor"] = target["cursor"]
                        result["timeline_trail"] = value["trail"]
                        if target.get("reading"):
                            result["reading_restore"] = target["reading"]
                    except SessionError as exc:
                        if exc.category != "conflict":
                            raise
                        # An old cursor/revision is not a grant. Re-read only a currently visible entry.
                        anchor = value["visible_anchor"]
                        response = self.transport.timeline(binding, sid, window="anchor", anchor_entry_id=anchor) if anchor else self.transport.timeline(binding, sid)
                        decoded = history_page(response, session_id=sid, now=self._clock.now())
                        if anchor and not any(row["entry_id"] == anchor for row in decoded["entries"]):
                            raise SessionError("unavailable")
                        result["timeline"] = presented_history(decoded)
                        result["timeline_trail"] = []
                        result["reading_anchor"] = anchor
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
                        result["timeline_trail"] = value.get("trail", [])
                    result["reading_anchor"] = value.get("entry_id", "")
                elif action in {"search", "search_more", "search_refresh"}:
                    result["search"] = self._read_search(binding, value, view_epoch)
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
                    caps = result["capabilities"]
                    sid = result["session"].get("session_id")
                    if sid and caps.get("capabilities", {}).get("session_conversation_history") is True and caps.get("contract_versions", {}).get("session_history_entries") == 2:
                        result["receipt_update"] = receipt_snapshot
                        try:
                            result.update(self._read_conversation(binding, sid, receipt_snapshot, check_conversation_read))
                        except SessionError as exc:
                            if exc.category in {"denied", "unpaired", "context_changed"}:
                                raise
                            result["conversation"] = []
            except SessionError as exc:
                result["error"] = exc.category
            except (AttributeError, KeyError, OverflowError, TypeError, ValueError):
                result["error"] = "invalid"
            self._ready.emit(result)

        executor = self.backend._question_executor if action == "question" else self.backend._session_executor
        executor.submit(worker)

    @Slot(object)
    def _apply(self, result):
        question = result["action"] == "question"
        if result["serial"] != (self._question_running if question else self._running):
            return
        if question:
            self._question_running = 0
            self._pending_question = {}
            self._pending_question_binding = None
            if result["question_epoch"] != self._question_epoch:
                self.changed.emit()
                return
        else:
            self._running = 0
            self._running_action = ""
        try:
            if result["binding"] != self.transport.binding():
                self.invalidate()
                return
        except SessionError:
            self.invalidate()
            return
        if (result.get("receipt_update") and result["question_epoch"] == self._question_epoch
                and result["receipt_update"].get("client_message_id") == self._question_receipt.get("client_message_id")):
            self._question_receipt = result["receipt_update"]
        if question:
            self._question_receipt = result.get("question_receipt", {})
            # A concurrent current read owns Runtime/capability authority. Reconcile with a new
            # read after it, never overwrite it with the question worker's older snapshot.
            if result.get("error") in {"denied", "unpaired"}:
                self.invalidate()
                self._error = result["error"]
                self.changed.emit()
                return
            if result.get("private_response") and "error" not in result:
                self._question_receipt = {}
                self._question_reference = {}
                self._selection = {}
                self._current_reply = result.get("current_reply", {})
                self._current_reply_binding = result["binding"]
                if not self._current_reply_valid():
                    self._current_reply = {}
                    self._current_reply_binding = None
                self._question_status = "current_answer" if self._current_reply else "accepted_unavailable"
                self.changed.emit()
                if self._current_reply:
                    self.currentReplyReady.emit()
                return
            if self._last_current_read > result["serial"]:
                self._question_status = "accepted_unavailable" if result.get("question_accepted") else "uncertain" if result.get("error") == "uncertain" else "failed"
                self._selection = {}
                self._reconcile_question = True
                self.changed.emit()
                self._reconcile_if_idle()
                return
            if "error" in result:
                self._question_status = "accepted_unavailable" if result.get("question_accepted") else "uncertain" if result["error"] == "uncertain" else "failed"
                self._conversation = []
                self._retained_flow = []
                self._selection = {}
                if result["error"] not in {"denied", "context_changed", "unpaired"}:
                    self._error = result["error"]
                    self.changed.emit()
                    return
            else:
                self._question_status = "accepted_unavailable"
                self._selection = {}
                # The question's GET is a receipt check, not a replacement Runtime snapshot.
                self._conversation = result.get("conversation", [])
                self._retained_flow = result.get("retained_flow", [])
                self._expire()
                confirmed = self._confirm_question()
                self.changed.emit()
                if confirmed:
                    self.questionConfirmed.emit(confirmed)
                return
        history_action = result["action"] in {"history", "history_more", "history_refresh", "timeline", "timeline_refresh", "timeline_page", "timeline_previous", "timeline_extend", "search", "search_more", "search_refresh", "open_entry"}
        if history_action and result.get("view_epoch") != self._view_epoch:
            self.changed.emit()
            return
        if "history" in result and "error" not in result:
            try:
                page = result["history"]
                checked = []
                # The aggregate is bounded to100 headers; each wire page stays20.
                for start in range(0, max(1, len(page["sessions"])), 50):
                    checked.extend(history_page({**page, "sessions": page["sessions"][start:start + 50]}, now=self._clock.now())["sessions"])
                result["history"] = {**page, "sessions": checked}
            except SessionError as exc:
                result["error"] = exc.category
        if "error" in result and result["action"] in {"history", "history_more", "history_refresh"}:
            self._sessions = []
            self._history_cursor = ""
            self._history_pages = 1
            self._history_start = ""
            self._history_scope = None
            self._history_before = None
            self._history_trail = []
            self._history_reset = False
        if "error" in result and history_action and result["error"] not in {"denied", "context_changed", "unpaired"}:
            self._search = {}
            self._timeline = {}
            self._timeline_trail = []
            self._error = result["error"]
            self.changed.emit()
            return
        if "error" in result:
            question_status = self._question_status
            self._withdraw_question()
            if question:
                self._question_status = question_status
            self._search = {}
            self._session = {}
            self._forecast.reset()
            self._moments = []
            self._conversation = []
            self._retained_flow = []
            self._selection = {}
            self._timeline = {}
            self._timeline_trail = []
            self._sessions = []
            self._history_cursor = ""
            self._history_pages = 1
            self._history_start = ""
            self._history_scope = None
            self._history_before = None
            self._history_trail = []
            self._history_reset = False
            self._loaded = False
            self._history_loaded = False
            self._error = result["error"]
        else:
            if "session" in result:
                if self._session.get("session_id") != result["session"].get("session_id"):
                    self._withdraw_question()
                self._loaded = True
                self._session = result["session"]
                self._moments = live_presentations(self._session, now=self._clock.now())
                self._caps = result.get("capabilities", self._caps)
                self._forecast.receive(self._session, self._caps, self._clock.now())
                if not self._composer_supported():
                    self._withdraw_question()
                self._conversation = result.get("conversation", [])
                self._retained_flow = result.get("retained_flow", [])
                if not self._history_supported():
                    self._timeline = {}
                    self._timeline_trail = []
                    self._conversation = []
                    self._retained_flow = []
                    self._sessions = []
                    self._history_cursor = ""
                    self._history_pages = 1
                    self._history_start = ""
                    self._history_scope = None
                    self._history_before = None
                    self._history_trail = []
                    self._history_reset = False
                    self._history_loaded = False
                    self._search = {}
                elif not self._search_supported():
                    self._search = {}
            if "history" in result:
                self._history_loaded = True
                rows = result["history"]["sessions"]
                # Atomic replacement from newly read pages, never append cached headers.
                old_deadlines = {row["session_id"]: row.get("_history_deadline") for row in self._sessions}
                for row in rows:
                    old = old_deadlines.get(row["session_id"])
                    if old is not None:
                        row["_history_deadline"] = min(old, row["_history_deadline"]) if row.get("_history_deadline") is not None else old
                self._sessions = rows
                self._history_pages = result["history"].get("_pages", 1)
                self._history_start = result["history"].get("_start", "")
                self._history_scope = result["history"].get("_scope")
                self._history_before = result["history"].get("_before")
                self._history_trail = result["history"].get("_trail", [])
                self._history_reset = result["history"].get("_window_reset", False)
                self._history_cursor = page_cursor(result["history"].get("next_cursor"))
            if "search" in result:
                self._search = result["search"]
            if "timeline" in result:
                incoming = result["timeline"]
                if not result.get("timeline_prefix"):
                    incoming = {key: value for key, value in incoming.items() if key != "_prefix_pages"}
                if "timeline_trail" in result:
                    self._timeline_trail = result["timeline_trail"]
                elif (result["action"] != "timeline_refresh" or incoming["revision"] != self._timeline.get("revision")
                        or "_page_cursor" not in incoming):
                    self._timeline_trail = []
                sid = incoming.get("session", {}).get("session_id")
                deadlines = [row["_history_deadline"] for row in self._sessions
                    if row["session_id"] == sid and row.get("_history_deadline") is not None]
                if self._timeline.get("session", {}).get("session_id") == sid and self._timeline.get("_session_deadline") is not None:
                    deadlines.append(self._timeline["_session_deadline"])
                if deadlines:
                    incoming = {**incoming, "_session_deadline": min(deadlines)}
                self._timeline = incoming
                # A same-scope/revision background page check must not close an active search.
                # Search separately re-reads every displayed page; changed scope/revision withdraws it.
                if not (result["action"] in {"timeline_refresh", "timeline_extend"}
                        and incoming.get("session", {}).get("session_id") == self._search.get("session_id")
                        and incoming["revision"] == self._search.get("revision")):
                    self._search = {}
        # Worker results may have waited on the GUI queue beyond their original deadline.
        self._expire()
        confirmed = self._confirm_question()
        self.changed.emit()
        if confirmed:
            self.questionConfirmed.emit(confirmed)
        if "history" in result and "error" not in result:
            self.historyUpdated.emit()
            if result["history"].get("_window_change"):
                reading = result["history"].get("_reading", {})
                if any(row["session_id"] == reading.get("session_id") for row in self._sessions):
                    self.archivePositioned.emit(reading["session_id"], reading["offset"])
                else:
                    self.archivePositioned.emit("", 0)
        if "search" in result and "error" not in result:
            self.searchUpdated.emit()
        if "timeline" in result and "error" not in result:
            reading = result.get("reading_restore", {})
            if reading and any(row["entry_id"] == reading["entry_id"] for row in self._timeline.get("entries", [])):
                self.timelinePositioned.emit(reading["entry_id"], reading["offset"])
            else:
                self.timelineUpdated.emit(result.get("reading_anchor", self._timeline.get("selected_entry_id", "")))
        if result["action"] == "open_entry" and "error" not in result:
            self.entryOpened.emit()
        self._reconcile_if_idle()

    def _reconcile_if_idle(self):
        if self._reconcile_question and not self._running and self._composer_supported():
            self._reconcile_question = False
            self.refresh()

    def _confirm_question(self):
        receipt = self._question_receipt
        if not receipt or receipt["session_id"] != self._session.get("session_id") or not self._composer_supported():
            return ""
        entry_id = confirmed_question_entry(self._conversation, receipt)
        if not entry_id:
            return ""
        first_confirmation = not receipt.get("confirmed")
        receipt["confirmed"] = True
        receipt["retained_until"] = min(receipt.get("retained_until", float("inf")),
            min(timestamp(row["retained_until"]) for row in self._conversation if row["entry_id"] in receipt["entry_ids"]))
        self._question_status = "accepted"
        return entry_id if first_confirmation else ""

    def _read_conversation(self, binding, session_id, receipt, check):
        check()
        page = history_page(self.transport.timeline(binding, session_id), session_id=session_id, now=self._clock.now())
        check()
        if len(page["entries"]) > 20:
            raise SessionError("invalid")
        retained = presented_history(page)["entries"]
        rows = conversation_entries(page)
        def projection(entries):
            return {"retained_flow": entries, "conversation": conversation_entries({"entries": entries})}
        if (receipt.get("session_id") != session_id or len(receipt.get("entry_ids", [])) != 2
                or confirmed_question_entry(rows, receipt)):
            return projection(retained)
        if receipt.get("confirmed") and receipt.get("anchor_entry_id"):
            anchors = [receipt["anchor_entry_id"]]  # Revalidate the displayed answer window.
        elif receipt.get("anchor_attempted"):
            return projection(retained)
        else:
            anchors = receipt["entry_ids"]  # Receipt order conveys no canonical timeline order.
        receipt["anchor_attempted"] = True
        for entry_id in anchors:
            check()
            anchor = history_page(self.transport.timeline(binding, session_id, window="anchor",
                anchor_entry_id=entry_id), session_id=session_id, now=self._clock.now())
            check()
            lower, upper = anchor.get("scanned_order_min"), anchor.get("scanned_order_max")
            if (anchor.get("window") != "anchor" or anchor.get("anchor_entry_id") != entry_id
                    or anchor.get("coverage") != "bounded_saved_entry_window" or anchor.get("next_cursor") is not None
                    or type(anchor.get("window_limit")) is not int or anchor["window_limit"] != 20
                    or type(anchor.get("scan_complete")) is not bool or len(anchor["entries"]) > 20
                    or type(lower) is not int or type(upper) is not int or not 0 <= lower <= upper
                    or any(not lower <= row["order"] <= upper for row in anchor["entries"])):
                raise SessionError("invalid")
            # Never combine grants from different revision windows or clear unrelated loaded pages.
            if anchor["revision"] != page["revision"]:
                return projection(retained)
            anchored_rows = conversation_entries(anchor)
            if confirmed_question_entry(anchored_rows, receipt):
                receipt["anchor_entry_id"] = entry_id
                anchored = presented_history(anchor)["entries"]
                merged = {row["entry_id"]: row for row in retained}
                if any(row["entry_id"] in merged and merged[row["entry_id"]] != row for row in anchored):
                    raise SessionError("invalid")
                merged.update({row["entry_id"]: row for row in anchored})
                combined = sorted(merged.values(), key=lambda row: row["order"])
                if len({row["order"] for row in combined}) != len(combined):
                    raise SessionError("invalid")
                return projection(combined)
        return projection(retained)
