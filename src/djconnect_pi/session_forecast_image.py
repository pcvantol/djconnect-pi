"""Current-only Forecast artist pixels. No generic or Session-artwork transport."""
from __future__ import annotations

import base64
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, is_dataclass
from math import ceil
from urllib.parse import urlsplit

import requests
from PySide6.QtCore import (
    QBuffer,
    QByteArray,
    QIODevice,
    QObject,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QImageReader

from .session_projection import timestamp
from .session_transport import SessionError, session_profile_id

MAX_BYTES = 2 * 1024 * 1024


def image_lease(session, forecast, now):
    """Narrow ready/current Spotify artist subset of protected Forecast v1."""
    try:
        sid = session['session_id']
        raw = session['broadcast']['session_forecast']
        playback = session['broadcast']['playback']
        if (session['runtime_state'] != 'active' or session['broadcast']['session']['session_id'] != sid
                or raw.get('session_id') != sid or raw.get('state') != 'ready'
                or type(raw.get('revision')) is not int or not 0 <= raw['revision'] < 2**63
                or forecast.get('state') != 'ready'
                or raw['revision'] != forecast['revision'] or playback['state'] != 'playing'
                or raw['current_anchor']['item_id'] != playback['item_id']
                or raw['current_anchor']['source_url'] != playback['source_url']
                or forecast['source_url'] != playback['source_url']
                or len(raw['imagery']) != 1):
            return None
        image = raw['imagery'][0]; subject = image['subject']
        artist = subject['id'].removeprefix('spotify:artist:')
        source = 'https://open.spotify.com/artist/' + artist
        expires = timestamp(image['expires_at']); deadline = timestamp(forecast['valid_until'])
        if (subject['type'] != 'artist' or re.fullmatch(r'[A-Za-z0-9]{22}', artist) is None
                or not isinstance(subject['name'], str) or not 0 < len(subject['name']) <= 512
                or image['role'] != 'current' or image['source_url'] != source
                or image['attribution'] != {'provider': 'Spotify', 'mark': 'spotify', 'url': source}
                or image['usage_basis'] != 'spotify_display_current_only'
                or image['cache_policy'] != 'active_session_no_store'
                or not isinstance(sid, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', sid) is None
                or not isinstance(image['url'], str)
                or re.fullmatch('/api/djconnect/v1/session/forecast/art/' + re.escape(sid) + r'/[A-Za-z0-9_-]{32}', image['url']) is None
                or expires is None or deadline is None or timestamp(raw.get('issued_at')) is None
                or expires > timestamp(raw['issued_at']) + 300):
            return None
        return {'session_id': sid, 'revision': forecast['revision'], 'path': image['url'],
            'artist': subject['name'], 'source_url': source, 'subject_id': subject['id'],
            'item_id': playback['item_id'], 'asset_deadline': expires, 'deadline': min(expires, deadline)}
    except (KeyError, TypeError, AttributeError, ValueError):
        return None


class ImageGate:
    """Metadata-only equality/floor fences; no persistent token or pixel cache."""
    def __init__(self):
        self.context = None; self.revision = -1; self.terminal = -1
        self.signature = ''; self.floors = {}

    def admit(self, session, forecast, binding, now):
        identity = asdict(binding) if is_dataclass(binding) else binding
        context = hashlib.sha256(json.dumps([identity, session.get('session_id')], sort_keys=True).encode()).hexdigest()
        if context != self.context:
            self.__init__(); self.context = context
        raw = session.get('broadcast', {}).get('session_forecast', {})
        revision = raw.get('revision') if isinstance(raw, dict) else None
        if type(revision) is not int or not 0 <= revision < 2**63:
            self.terminal = max(self.terminal, self.revision); return None
        lease = image_lease(session, forecast, now)
        signature = hashlib.sha256(json.dumps(lease, sort_keys=True).encode()).hexdigest() if lease else ''
        if (not lease or revision < self.revision or revision <= self.terminal
                or (revision == self.revision and signature != self.signature)):
            self.terminal = max(self.terminal, self.revision, revision)
            self.revision = max(self.revision, revision); self.signature = ''; return None
        self.revision = revision; self.signature = signature
        key = hashlib.sha256(lease['path'].encode()).hexdigest()
        if key not in self.floors and len(self.floors) >= 32:
            self.terminal = max(self.terminal, revision); return None
        self.floors[key] = min(self.floors.get(key, lease['asset_deadline']), lease['asset_deadline'])
        lease['deadline'] = min(lease['deadline'], self.floors[key])
        if lease['deadline'] <= now:
            self.terminal = max(self.terminal, revision); return None
        return lease


def fetch_pixels(binding, lease, allowed):
    """Only the configured HA's headerless Forecast route; never paired/media/image."""
    if not isinstance(binding.ha_url, str): return ''
    try:
        origin = urlsplit(binding.ha_url)
        port = origin.port  # Validate malformed/custom port values before any request.
    except (ValueError, TypeError):
        return ''
    if (origin.scheme not in ('http', 'https') or not origin.hostname or origin.username or origin.password
            or origin.path not in ('', '/') or origin.query or origin.fragment or (port is not None and not 1 <= port <= 65535)):
        return ''
    if not isinstance(lease.get('path'), str): return ''
    if re.fullmatch(r'/api/djconnect/v1/session/forecast/art/[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]{32}', lease.get('path', '')) is None:
        return ''
    started = time.monotonic()
    def check(): return allowed() and time.monotonic() - started <= 8
    if not check(): return ''
    try:
        with requests.Session() as client:
            client.trust_env = False  # No netrc, proxy credentials or ambient cookies.
            with client.get(binding.ha_url.rstrip('/') + lease['path'],
                    headers={'Accept': 'image/png,image/jpeg', 'Cache-Control': 'no-store'},
                    stream=True, allow_redirects=False, timeout=(4, 4)) as response:
                mime = response.headers.get('Content-Type', '').split(';')[0].lower()
                if not check() or response.status_code != 200 or mime not in ('image/png', 'image/jpeg'):
                    return ''
                length = response.headers.get('Content-Length')
                if length is not None and (not length.isdigit() or not 0 < int(length) <= MAX_BYTES): return ''
                body = bytearray()
                for chunk in response.iter_content(64 * 1024):
                    if not check() or len(body) + len(chunk) > MAX_BYTES: return ''
                    body.extend(chunk)
        if not body or not check() or (length is not None and len(body) != int(length)): return ''
        return decode_pixels(body, mime, check)
    except (requests.RequestException, TypeError, ValueError, OverflowError):
        return ''


def decode_pixels(body, mime, allowed, expected_size=None):
    """Pure bounded static-image decode; HTTP authorization stays route-specific."""
    if mime not in ('image/png', 'image/jpeg') or not body or len(body) > MAX_BYTES or not allowed(): return ''
    if mime == 'image/png' and (not body.startswith(b'\x89PNG\r\n\x1a\n') or b'acTL' in body): return ''
    if mime == 'image/jpeg' and not body.startswith(b'\xff\xd8\xff'): return ''
    data = QByteArray(bytes(body)); buffer = QBuffer(data);buffer.open(QIODevice.ReadOnly)
    reader = QImageReader(buffer);reader.setAutoTransform(False);reader.setDecideFormatFromContent(True)
    size = reader.size()
    if (bytes(reader.format()) not in (b'png', b'jpeg', b'jpg') or not 0 < size.width() <= 2048
            or not 0 < size.height() <= 2048 or size.width() * size.height() > 4_000_000
            or (expected_size is not None and (size.width(), size.height()) != expected_size)
            or reader.imageCount() > 1 or reader.read().isNull() or not allowed()):
        return ''
    return 'data:' + mime + ';base64,' + base64.b64encode(body).decode('ascii')


class ForecastImages(QObject):
    changed = Signal()
    aboutToChange = Signal()
    _ready = Signal(object)

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner;self.gate = ImageGate();self.visible = False
        self.generation = 0;self.desired = None;self.binding = None
        self.public = {};self.attempted = '';self.running = False;self.executor = None
        self.closed = False;self.dirty = False;self.attempts = 0;self.attempt_session = ''
        self._ready.connect(self._finish)
        self.timer = QTimer(self);self.timer.setInterval(250);self.timer.timeout.connect(self._tick)
        self.deadline_timer = QTimer(self);self.deadline_timer.setSingleShot(True)
        self.deadline_timer.setTimerType(Qt.PreciseTimer);self.deadline_timer.timeout.connect(self._deadline_tick)

    def _replace_public(self, value):
        if self.public != value:
            self.aboutToChange.emit()
            self.public = value

    def set_visible(self, visible):
        if self.visible == visible: return
        self.visible = visible;self.attempted = ''
        if visible: self.timer.start()
        else: self.timer.stop()
        self.sync()

    def _valid(self, generation):
        try:
            return (not self.closed and self.visible and self.owner._foreground and generation == self.generation
                and self.owner._running_action not in {'start', 'end'}
                and self.desired is not None and self.owner._clock.now() < self.desired['deadline']
                and self.binding == self.owner.transport.binding())
        except (SessionError, AttributeError, TypeError, ValueError):  # No private transport diagnostics
            return False

    def sync(self):
        if self.closed: return
        cfg = self.owner.backend.cfg
        eligible = (self.visible and self.owner._foreground and self.owner._running_action not in {'start', 'end'}
            and bool(session_profile_id(cfg)) and cfg.active_profile_type in {'personal', 'household'}
            and cfg.active_profile_privacy_mode == 'private' and not cfg.private_session)
        try:
            binding = self.owner.transport.binding() if eligible else None
            lease = self.gate.admit(self.owner._session, self.owner._forecast.snapshot(), binding, self.owner._clock.now()) if eligible else None
        except (SessionError, AttributeError, KeyError, TypeError, ValueError):
            binding = lease = None
        self._set_lease(binding, lease)

    def _set_lease(self, binding, lease):
        if (binding, lease) != (self.binding, self.desired):
            self.generation += 1;self.binding = binding;self.desired = lease;self._replace_public({});self.attempted = ''
            self.deadline_timer.stop()
            if lease: self.deadline_timer.start(max(1, ceil((lease['deadline'] - self.owner._clock.now()) * 1000)))
            self.changed.emit()
        self._start()

    def fetch(self, binding, lease, allowed):
        return fetch_pixels(binding, lease, allowed)

    def public_pixels(self, pixels):
        return {'source': pixels, 'artist': self.desired['artist'], 'source_url': self.desired['source_url']}

    def _start(self):
        if self.running or not self._valid(self.generation): return
        key = hashlib.sha256(json.dumps(self.desired, sort_keys=True).encode()).hexdigest()
        if key == self.attempted: return
        sid = self.desired['session_id']
        if sid != self.attempt_session: self.attempt_session = sid;self.attempts = 0
        if self.attempts >= 32: return
        self.attempts += 1;self.attempted = key;self.running = True
        generation, binding, lease = self.generation, self.binding, dict(self.desired)
        if self.executor is None: self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='djconnect-forecast-image')
        def work():
            pixels = ''
            try:
                pixels = self.fetch(binding, lease, lambda: self._valid(generation))
            except (OSError, RuntimeError, SessionError):
                pass  # Decoder/platform failure keeps text; no identifier/URL diagnostics.
            finally:
                try: self._ready.emit((generation, pixels))
                except RuntimeError: pass  # The owner was destroyed; no result may outlive it.
        self.executor.submit(work)

    @Slot(object)
    def _finish(self, result):
        self.running = False
        generation, pixels = result
        if self._valid(generation) and pixels:
            self._replace_public(self.public_pixels(pixels))
            self.changed.emit()
        self._start()  # At most one pending latest lease, never a queue of obsolete reads.

    def snapshot(self):
        if self.public and not self._valid(self.generation):
            self._replace_public({});self.dirty = True
        return dict(self.public)

    def _tick(self):
        self.snapshot()
        if self.dirty: self.dirty = False;self.changed.emit()

    def _deadline_tick(self):
        self._tick()
        if self.desired and self._valid(self.generation):
            self.deadline_timer.start(max(1, ceil((self.desired['deadline'] - self.owner._clock.now()) * 1000)))

    def shutdown(self):
        self.closed = True;self.generation += 1;self.desired = None;self._replace_public({});self.timer.stop();self.deadline_timer.stop()
        self.changed.emit()
        if self.executor: self.executor.shutdown(wait=False, cancel_futures=True)
