"""Explicit Profile playback intent; one HTTP attempt, no optimistic Runtime."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256

from PySide6.QtCore import QObject, Signal, Slot

from .session_projection import active_session, session_playback
from .session_transport import SessionError

COMMANDS = frozenset({"play", "pause", "previous", "next", "save_current_track"})


VOLUME_COMMANDS = frozenset({"volume_read", "set_volume"})


def volume_observation(status, backend):
    """Raw current-output observation; missing/zero values are never defaults."""
    caps = status.get("music_backend_capabilities")
    playback = status.get("playback")
    device = playback.get("device") if isinstance(playback, dict) else None
    if (not isinstance(caps, dict) or caps.get("supports_volume") is not True
            or not isinstance(device, dict)):
        raise SessionError("unavailable")
    output = device.get("id")
    if (not isinstance(output, str) or not 1 <= len(output) <= 512 or output != output.strip()
            or any(ord(char) < 32 or ord(char) == 127 for char in output)):
        raise SessionError("unavailable")
    if backend == "spotify_direct":
        if (device.get("supports_volume") is not True or device.get("is_restricted") is not False
                or device.get("active") is not True):
            raise SessionError("unavailable")
    elif backend != "music_assistant" or device.get("entity_id", output) != output:
        raise SessionError("unavailable")
    values = [value for value in (playback.get("volume_percent"), playback.get("volume"),
                                 device.get("volume_percent")) if value is not None]
    if (not values or any(type(value) is not int or not 0 <= value <= 100 for value in values)
            or any(value != values[0] for value in values)):
        raise SessionError("unavailable")
    name = device.get("name")
    return {"output_id": output, "percent": values[0],
            "output_name": name if isinstance(name, str) and len(name) <= 256 else ""}


def reference(owner):
    cfg = owner.backend.cfg
    playback = session_playback(owner._session)
    if (not owner._foreground or owner.backend.demoMode
            or not cfg.explicit_profile_id or cfg.explicit_profile_id != cfg.active_profile_id
            or cfg.private_session or cfg.active_profile_type not in {"personal", "household"}
            or cfg.active_profile_privacy_mode != "private"
            or getattr(cfg, "music_backend", "") not in {"spotify_direct", "music_assistant"}
            or getattr(cfg, "music_backend_available", False) is not True
            or not playback):
        return None
    return (owner._session["session_id"], playback["item_id"], playback["state"], playback["source_url"],
            cfg.music_backend, getattr(cfg, "music_backend_revision", 0))


class PlaybackControl(QObject):
    ready = Signal(object)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.visible = False
        self.running = False
        self.closed = False
        self.request = None
        self.status = ""
        self.blocked = False
        self.executor = None
        self.volume = None
        self.volume_serial = 0
        self.volume_status = ""
        self.ready.connect(self.finish)

    def valid(self):
        try:
            request = self.request
            return (not self.closed and self.visible and request is not None
                    and self.owner._running_action not in {"start", "end"}
                    and request["binding"] == self.owner.transport.binding()
                    and request["reference"] == reference(self.owner)
                    and (request["command"] != "save_current_track" or self.favorite_supported())
                    and (request["command"] not in VOLUME_COMMANDS or self.volume_supported()))
        except (SessionError, AttributeError, KeyError, TypeError, ValueError, RuntimeError):
            return False

    def favorite_supported(self):
        caps = getattr(self.owner.backend.cfg, "music_backend_capabilities", {})
        return isinstance(caps, dict) and caps.get("supports_favorites") is True

    def volume_supported(self):
        caps = getattr(self.owner.backend.cfg, "music_backend_capabilities", {})
        return isinstance(caps, dict) and caps.get("supports_volume") is True

    def volume_valid(self):
        try:
            return (self.volume is not None and not self.closed and self.visible and self.volume_supported()
                    and self.owner._running_action not in {"start", "end"}
                    and self.volume["binding"] == self.owner.transport.binding()
                    and self.volume["reference"] == reference(self.owner))
        except (SessionError, AttributeError, KeyError, TypeError, ValueError, RuntimeError):
            return False

    def sync(self):
        if self.volume and not self.volume_valid():
            self.volume = None
            self.volume_status = ""
        if self.request and not self.valid():
            self.request = None
            self.status = ""

    def hide(self, *, reset=False):
        self.volume = None
        self.volume_status = ""
        self.request = None
        if reset:
            self.blocked = False
        self.status = "uncertain" if self.blocked else ""

    def set_visible(self, value):
        self.visible = bool(value)
        if not self.visible:
            self.hide()

    def snapshot(self):
        self.sync()
        available = False
        try:
            available = bool(self.visible and reference(self.owner) and self.owner.transport.binding())
        except SessionError:
            pass
        busy = bool(self.running or self.owner._running or self.owner._question_running or self.owner._artwork_prepare.running)
        return {"available": available, "enabled": available and not busy and not self.blocked,
                "favorite": self.favorite_supported(), "running": self.running,
                "volume_supported": self.volume_supported(),
                "volume": {**self.volume["observation"], "lease": self.volume["serial"]} if self.volume_valid() else {},
                "volume_status": self.volume_status,
                "reading_volume": bool(self.running and self.request and self.request["command"] == "volume_read"),
                "status": "sending" if self.running and self.valid() else "uncertain" if self.blocked else self.status}

    def start(self, session_id, item_id, command):
        if not isinstance(command, str) or command not in COMMANDS:
            return False
        return self._start(session_id, item_id, command)

    def read_volume(self, session_id, item_id):
        if not self.volume_supported():
            return False
        return self._start(session_id, item_id, "volume_read")

    def set_volume(self, session_id, item_id, lease, value):
        if (type(value) is not int or not 0 <= value <= 60 or type(lease) is not int
                or not self.volume_valid() or self.volume["serial"] != lease
                or value == self.volume["observation"]["percent"]):
            return False
        return self._start(session_id, item_id, "set_volume", value=value)

    def _start(self, session_id, item_id, command, *, value=None):
        if self.closed or not self.snapshot()["enabled"]:
            return False
        current = reference(self.owner)
        if (current is None or current[:2] != (session_id, item_id)
                or command == "save_current_track" and not self.favorite_supported()
                or command == "play" and current[2] != "paused"
                or command == "pause" and current[2] != "playing"):
            return False
        try:
            binding = self.owner.transport.binding()
        except SessionError:
            return False
        self.request = {"binding": binding, "reference": current, "command": command}
        if command == "set_volume":
            self.request.update(value=value, volume=deepcopy(self.volume["observation"]))
        self.volume = None
        self.volume_status = ""
        request = deepcopy(self.request)
        self.running = True
        self.status = ""
        self.owner.changed.emit()

        def worker():
            result = {}
            try:
                if not self.valid() or self.request != request:
                    raise SessionError("context_changed")
                fresh = active_session(self.owner.transport.active(binding, isolated=True))
                if not self.valid() or self.request != request:
                    raise SessionError("context_changed")
                if fresh.get("session_id") != request["reference"][0] or fresh.get("runtime_state") != "active":
                    result["withdraw_session"] = True
                    raise SessionError("context_changed")
                playback = session_playback(fresh)
                if (playback.get("item_id"), playback.get("state"), playback.get("source_url")) != request["reference"][1:4]:
                    raise SessionError("context_changed")
                # Resolve current owner backend/capabilities; persisted UI metadata grants no write.
                status = self.owner.transport.playback_status(binding)
                if not self.valid() or self.request != request:
                    raise SessionError("context_changed")
                caps = status.get("music_backend_capabilities")
                observed = status.get("playback")
                identity = observed.get("uri") if isinstance(observed, dict) else None
                if (not isinstance(identity, str) or not 1 <= len(identity) <= 2048
                        or observed.get("has_playback") is not True
                        or type(observed.get("is_playing")) is not bool
                        or observed["is_playing"] != (request["reference"][2] == "playing")
                        or sha256(identity.strip().encode()).hexdigest()[:24] != request["reference"][1]):
                    raise SessionError("context_changed")
                if (status.get("music_backend") != request["reference"][4]
                        or type(status.get("music_backend_revision")) is not int
                        or status["music_backend_revision"] != request["reference"][5]
                        or status.get("music_backend_available") is not True
                        or status.get("backend_available") is not True
                        or command == "save_current_track" and (not isinstance(caps, dict) or caps.get("supports_favorites") is not True)):
                    raise SessionError("unavailable")
                # Existing global command semantics: no invented Session/item/output CAS fields.
                if command in VOLUME_COMMANDS:
                    observation = volume_observation(status, request["reference"][4])
                    if command == "volume_read":
                        result["volume"] = observation
                    else:
                        previous = request["volume"]
                        if any(observation[key] != previous[key] for key in ("output_id", "percent")):
                            raise SessionError("context_changed")
                        if not self.valid() or self.request != request:
                            raise SessionError("context_changed")
                        self.owner.transport.playback_volume(binding, request["value"], request["reference"][4])
                else:
                    self.owner.transport.playback_command(binding, command)
            except SessionError as exc:
                result["error"] = exc.category
            except Exception:  # noqa: BLE001 - a failed write callback cannot be retried or report success.
                result["error"] = "uncertain"
            try:
                self.ready.emit(result)
            except RuntimeError:
                pass
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="djconnect-playback-intent")
        self.executor.submit(worker)
        return True

    @Slot(object)
    def finish(self, result):
        valid = self.valid()
        command = self.request["command"] if self.request else ""
        self.running = False
        if not valid:
            self.request = None
            self.status = ""
        elif result.get("error") == "denied" or result.get("withdraw_session"):
            self.owner.invalidate()
            self.owner._error = "denied" if result.get("error") == "denied" else "context_changed"
        elif command == "volume_read":
            self.status = ""
            self.volume_status = "unavailable" if result.get("error") else ""
            if not result.get("error"):
                self.volume_serial += 1
                self.volume = {"binding": self.request["binding"], "reference": self.request["reference"],
                               "serial": self.volume_serial, "observation": result["volume"]}
        elif result.get("error"):
            self.blocked = True
            self.status = "uncertain"
        else:
            self.status = "accepted"
        self.owner.changed.emit()
        # An independent owner read owns playback; never project the command response.
        if valid and not result.get("error") and command != "volume_read":
            self.owner.refresh()

    def refresh(self):
        if self.running or self.owner.busy:
            return
        self.owner.refresh()
        if self.owner._running_action == "refresh":
            self.blocked = False
            self.status = ""
            self.request = None
            self.volume = None
            self.volume_status = ""
            self.owner.changed.emit()

    def shutdown(self):
        self.closed = True
        self.hide(reset=True)
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
