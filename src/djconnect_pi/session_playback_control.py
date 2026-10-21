"""Explicit Profile playback intent; one HTTP attempt, no optimistic Runtime."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256

from PySide6.QtCore import QObject, Signal, Slot

from .session_projection import active_session, session_playback
from .session_transport import SessionError

COMMANDS = frozenset({"play", "pause", "previous", "next", "save_current_track"})


VOLUME_COMMANDS = frozenset({"volume_read", "set_volume"})
FAVORITE_COMMANDS = frozenset({"favorite_read", "set_favorite"})
OUTPUT_COMMANDS = frozenset({"outputs_read", "set_output"})
OBSERVATION_COMMANDS = frozenset({"volume_read", "favorite_read", "outputs_read"})


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


def favorite_observation(status, backend):
    """Only strict, mutually consistent current-track favorite observations."""
    caps = status.get("music_backend_capabilities")
    playback = status.get("playback")
    if (backend != "spotify_direct" or not isinstance(caps, dict)
            or caps.get("supports_favorites") is not True or not isinstance(playback, dict)
            or type(playback.get("favorite_status")) is not bool
            or "is_liked" in playback and (type(playback["is_liked"]) is not bool
                                          or playback["is_liked"] != playback["favorite_status"])):
        raise SessionError("unavailable")
    return playback["favorite_status"]


def output_supported(caps, backend):
    return (backend == "spotify_direct" and isinstance(caps, dict)
            and caps.get("supports_outputs") is True
            and caps.get("supports_transfer_or_output_selection") is True)


def output_id(value):
    return (isinstance(value, str) and 1 <= len(value) <= 512 and value == value.strip()
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def output_origin(status, backend):
    playback = status.get("playback")
    device = playback.get("device") if isinstance(playback, dict) else None
    if (not output_supported(status.get("music_backend_capabilities"), backend)
            or not isinstance(device, dict) or not output_id(device.get("id"))
            or device.get("active") is not True or device.get("is_restricted") is not False):
        raise SessionError("unavailable")
    return device["id"]


def output_choices(payload, backend, revision, origin):
    """Admit only the server's current selectable IDs, never cached fallbacks."""
    rows = payload.get("devices")
    if (not output_supported(payload.get("music_backend_capabilities"), backend)
            or payload.get("music_backend") != backend
            or type(payload.get("music_backend_revision")) is not int
            or payload["music_backend_revision"] != revision
            or payload.get("music_backend_available") is not True
            or payload.get("backend_available") is not True
            or not isinstance(rows, list) or len(rows) > 100):
        raise SessionError("unavailable")
    seen = set()
    choices = []
    active = []
    for row in rows:
        if not isinstance(row, dict) or not output_id(row.get("id")) or row["id"] in seen:
            raise SessionError("unavailable")
        seen.add(row["id"])
        if row.get("cached") is not False or row.get("is_restricted") is not False:
            continue
        if type(row.get("active")) is not bool:
            raise SessionError("unavailable")
        if row["active"]:
            active.append(row["id"])
        name = row.get("name")
        if not isinstance(name, str) or not 1 <= len(name) <= 256 or any(ord(c) < 32 for c in name):
            raise SessionError("unavailable")
        choices.append({"id": row["id"], "name": name, "active": row["active"]})
    if active != [origin] or len(choices) > 32:
        raise SessionError("unavailable")
    return choices


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
        self.favorite_state = None
        self.favorite_status = ""
        self.outputs = None
        self.outputs_serial = 0
        self.outputs_status = ""
        self.favorite_serial = 0
        self.ready.connect(self.finish)

    def valid(self):
        try:
            request = self.request
            return (not self.closed and self.visible and request is not None
                    and self.owner._running_action not in {"start", "end"}
                    and request["binding"] == self.owner.transport.binding()
                    and request["reference"] == reference(self.owner)
                    and (request["command"] != "save_current_track" or self.favorite_supported())
                    and (request["command"] not in VOLUME_COMMANDS or self.volume_supported())
                    and (request["command"] not in FAVORITE_COMMANDS or self.favorite_read_supported())
                    and (request["command"] not in OUTPUT_COMMANDS or self.outputs_supported()))
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

    def favorite_read_supported(self):
        return self.favorite_supported() and getattr(self.owner.backend.cfg, "music_backend", None) == "spotify_direct"

    def favorite_valid(self):
        try:
            return (self.favorite_state is not None and not self.closed and self.visible
                    and self.favorite_read_supported() and self.owner._running_action not in {"start", "end"}
                    and self.favorite_state["binding"] == self.owner.transport.binding()
                    and self.favorite_state["reference"] == reference(self.owner))
        except (SessionError, AttributeError, KeyError, TypeError, ValueError, RuntimeError):
            return False

    def outputs_supported(self):
        return output_supported(getattr(self.owner.backend.cfg, "music_backend_capabilities", None),
                                getattr(self.owner.backend.cfg, "music_backend", None))

    def outputs_valid(self):
        try:
            return (self.outputs is not None and not self.closed and self.visible and self.outputs_supported()
                    and self.owner._running_action not in {"start", "end"}
                    and self.outputs["binding"] == self.owner.transport.binding()
                    and self.outputs["reference"] == reference(self.owner))
        except (SessionError, AttributeError, KeyError, TypeError, ValueError, RuntimeError):
            return False

    def sync(self):
        if self.outputs and not self.outputs_valid():
            self.outputs = None
            self.outputs_status = ""
        if self.favorite_state and not self.favorite_valid():
            self.favorite_state = None
            self.favorite_status = ""
        if self.volume and not self.volume_valid():
            self.volume = None
            self.volume_status = ""
        if self.request and not self.valid():
            self.request = None
            self.status = ""

    def hide(self, *, reset=False):
        self.outputs = None
        self.outputs_status = ""
        self.favorite_state = None
        self.favorite_status = ""
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
        busy = bool(self.running or self.owner._running or self.owner._question_running or self.owner._artwork_prepare.running
                    or getattr(getattr(self.owner, "_archive_delete", None), "running", False))
        return {"available": available, "enabled": available and not busy and not self.blocked,
                "favorite": self.favorite_read_supported(), "running": self.running,
                "favorite_observation": {"liked": self.favorite_state["liked"], "lease": self.favorite_state["serial"]} if self.favorite_valid() else {},
                "favorite_status": self.favorite_status,
                "outputs_supported": self.outputs_supported(),
                "outputs": {"choices": deepcopy(self.outputs["choices"]), "origin": self.outputs["origin"], "lease": self.outputs["serial"]} if self.outputs_valid() else {},
                "outputs_status": self.outputs_status,
                "reading_outputs": bool(self.running and self.request and self.request["command"] == "outputs_read"),
                "reading_favorite": bool(self.running and self.request and self.request["command"] == "favorite_read"),
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

    def read_favorite(self, session_id, item_id):
        if not self.favorite_read_supported():
            return False
        return self._start(session_id, item_id, "favorite_read")

    def set_favorite(self, session_id, item_id, lease, value):
        if (type(value) is not bool or type(lease) is not int or not self.favorite_valid()
                or self.favorite_state["serial"] != lease or value == self.favorite_state["liked"]):
            return False
        return self._start(session_id, item_id, "set_favorite", value=value)

    def read_outputs(self, session_id, item_id):
        if not self.outputs_supported():
            return False
        return self._start(session_id, item_id, "outputs_read")

    def set_output(self, session_id, item_id, lease, target):
        if (type(lease) is not int or not output_id(target) or not self.outputs_valid()
                or self.outputs["serial"] != lease or target == self.outputs["origin"]
                or not any(row["id"] == target for row in self.outputs["choices"])):
            return False
        return self._start(session_id, item_id, "set_output", value=target)

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
        if command == "set_favorite":
            self.request.update(value=value, liked=self.favorite_state["liked"])
        if command == "set_output":
            self.request.update(value=value, origin=self.outputs["origin"])
        self.outputs = None
        self.outputs_status = ""
        self.volume = None
        self.volume_status = ""
        self.favorite_state = None
        self.favorite_status = ""
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
                if command in OUTPUT_COMMANDS:
                    origin = output_origin(status, request["reference"][4])
                    if command == "set_output" and origin != request["origin"]:
                        raise SessionError("context_changed")
                    inventory = self.owner.transport.playback_outputs(binding)
                    if not self.valid() or self.request != request:
                        raise SessionError("context_changed")
                    choices = output_choices(inventory, request["reference"][4], request["reference"][5], origin)
                    if command == "outputs_read":
                        result.update(origin=origin, choices=choices)
                    else:
                        if not any(row["id"] == request["value"] for row in choices):
                            raise SessionError("context_changed")
                        if not self.valid() or self.request != request:
                            raise SessionError("context_changed")
                        self.owner.transport.playback_output(binding, request["value"], request["reference"][2] == "playing")
                elif command in FAVORITE_COMMANDS:
                    liked = favorite_observation(status, request["reference"][4])
                    if command == "favorite_read":
                        result["liked"] = liked
                    else:
                        if liked != request["liked"] or not self.valid() or self.request != request:
                            raise SessionError("context_changed")
                        self.owner.transport.playback_favorite(binding, request["value"])
                elif command in VOLUME_COMMANDS:
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
        elif command == "outputs_read":
            self.status = ""
            self.outputs_status = "unavailable" if result.get("error") else ""
            if not result.get("error"):
                self.outputs_serial += 1
                self.outputs = {"binding": self.request["binding"], "reference": self.request["reference"],
                                "serial": self.outputs_serial, "origin": result["origin"], "choices": result["choices"]}
        elif command == "favorite_read":
            self.status = ""
            self.favorite_status = "unavailable" if result.get("error") else ""
            if not result.get("error"):
                self.favorite_serial += 1
                self.favorite_state = {"binding": self.request["binding"], "reference": self.request["reference"],
                                       "serial": self.favorite_serial, "liked": result["liked"]}
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
        if valid and not result.get("error") and command not in OBSERVATION_COMMANDS:
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
            self.favorite_state = None
            self.favorite_status = ""
            self.outputs = None
            self.outputs_status = ""
            self.owner.changed.emit()

    def shutdown(self):
        self.closed = True
        self.hide(reset=True)
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
