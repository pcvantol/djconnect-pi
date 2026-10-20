"""Prepared current-Moment images; paired owner reads, never Forecast auth."""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict
from urllib.parse import urlsplit

import requests

from .config import CLIENT_TYPE
from .i18n import locale_for_language
from .session_current_reply import moment_reference
from .session_forecast_image import MAX_BYTES, ForecastImages, decode_pixels
from .session_projection import timestamp
from .session_transport import SessionError

PATH = r'/api/djconnect/v1/session/media/image/[A-Za-z0-9_-]{1,128}/[A-Za-z0-9_-]{1,128}'


def artwork_lease(session, caps, binding, now):
    """Only already-prepared current native Moment grants, not history/thumbnail."""
    try:
        if (caps['capabilities'].get('session_artwork') is not True
                or type(caps['contract_versions'].get('session_artwork')) is not int
                or caps['contract_versions']['session_artwork'] != 1 or session['runtime_state'] != 'active'):
            return None
        sid = session['session_id'];snapshot = session['broadcast']
        mid = snapshot['native_delivery']['current_moment_id']
        selected = {'kind': 'selected_moment', 'session_id': sid, 'moment_id': mid}
        reference = moment_reference(session, selected, now=now)
        if not reference or snapshot['session']['session_id'] != sid:
            return None
        media = snapshot['session_media']
        if not isinstance(media, list) or len(media) > 64: return None
        matches = [p for p in media if isinstance(p, dict) and p.get('moment_id') == mid]
        if len(matches) != 1: return None
        p = matches[0];art = p['artwork'];subject = art['subject']
        match = re.fullmatch(r'spotify:(track|album|artist):([A-Za-z0-9]{22})', subject['uri'])
        if not match: return None
        kind, identity = match.groups();source = 'https://open.spotify.com/' + kind + '/' + identity
        captured, expiry = timestamp(art['captured_at']), timestamp(art['expires_at'])
        alt = art['alt_text'][binding.language]
        if (type(p['schema_version']) is not int or p['schema_version'] != 1 or p['session_id'] != sid
                or 'entry_id' in p or not isinstance(p['revision'], str)
                or re.fullmatch(r'[a-f0-9]{24}', p['revision']) is None
                or not isinstance(art['media_revision'], str) or re.fullmatch(r'[a-f0-9]{24}', art['media_revision']) is None
                or art['state'] != 'ready' or subject['provider'] != 'spotify' or subject['type'] != kind
                or art['resolution_basis'] != 'resolved_now'
                or art['role'] != ('contextual_artist' if kind == 'artist' else 'cover')
                or art['edition_basis'] not in ({'not_applicable'} if kind == 'artist' else {'original_bound', 'provider_resolved_now'})
                or (kind != 'track' and 'album_uri' in subject)
                or (kind == 'album' and art['edition_basis'] != 'original_bound')
                or (kind == 'track' and art['edition_basis'] == 'original_bound' and not subject.get('album_uri'))
                or (subject.get('album_uri') and re.fullmatch(r'spotify:album:[A-Za-z0-9]{22}', subject['album_uri']) is None)
                or art['source_url'] != source or art['attribution'] != {'provider':'Spotify','mark':'spotify','url':source}
                or art['usage_basis'] != 'spotify_temporary_owner_display' or art['cache_policy'] != 'no-store'
                or art['crop_allowed'] is not False or art['requires_device_auth'] is not True
                or art['current_display_allowed'] is not True or art['active_flow_display_allowed'] is not True
                or art['historical_display_allowed'] is not False
                or not isinstance(alt, str) or not 0 < len(alt) <= 512
                or any(type(art.get(k)) is not int or not 0 < art[k] <= 2048 for k in ('width','height'))
                or art['width'] * art['height'] > 4_000_000
                or captured is None or expiry is None or not captured <= now < expiry or not 0 < expiry-captured <= 300
                or not isinstance(sid, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', sid) is None
                or not isinstance(art['url'], str) or re.fullmatch(PATH, art['url']) is None
                or art['url'].split('/')[-2] != sid):
            return None
        return {'session_id':sid, 'moment_id':mid, 'revision':p['revision'], 'path':art['url'],
                'artist':alt, 'source_url':source, 'reference':reference['signature'],
                'asset_deadline':expiry, 'deadline':min(expiry,reference['deadline']),
                'media_revision':art['media_revision'], 'width':art['width'], 'height':art['height']}
    except (KeyError, TypeError, AttributeError, ValueError):
        return None


class ArtworkGate:
    """Opaque equality revisions, original floors and observed-withdrawal latches."""
    def __init__(self):
        self.context = '';self.previous = '';self.seen = {};self.revoked = set();self.floors = {}

    def admit(self, session, caps, binding, now):
        context = hashlib.sha256(json.dumps([asdict(binding),session.get('session_id')],sort_keys=True).encode()).hexdigest()
        if self.context != context:self.__init__();self.context = context
        lease = artwork_lease(session,caps,binding,now)
        key = hashlib.sha256(json.dumps([lease['path'],lease['revision']],sort_keys=True).encode()).hexdigest() if lease else ''
        if self.previous and key != self.previous:self.revoked.add(self.previous)
        if key != self.previous:self.previous = ''
        if not lease or key in self.revoked:return None
        digest = hashlib.sha256(json.dumps(lease,sort_keys=True).encode()).hexdigest()
        if key in self.seen and self.seen[key] != digest:
            self.revoked.add(key);return None
        if key not in self.seen and len(self.seen) >= 32:return None
        self.previous = key
        self.seen[key] = digest
        asset = hashlib.sha256(lease['path'].encode()).hexdigest()
        self.floors[asset] = min(self.floors.get(asset,lease['asset_deadline']),lease['asset_deadline'])
        lease['deadline'] = min(lease['deadline'],self.floors[asset])
        if lease['deadline'] <= now:self.revoked.add(key);return None
        return lease


def fetch_artwork(binding, lease, allowed):
    """Paired owner GET only; never forward its credentials to Forecast or CDN."""
    try:
        origin = urlsplit(binding.ha_url);port = origin.port
        if (not binding.profile_id or binding.profile_id != binding.resolved_profile_id or not binding.token
                or binding.profile_type not in {'personal','household'} or binding.privacy_mode != 'private' or binding.private_session
                or origin.scheme not in ('http','https') or not origin.hostname or origin.username or origin.password
                or origin.path not in ('','/') or origin.query or origin.fragment
                or (port is not None and not 0 < port <= 65535)
                or re.fullmatch(PATH,lease.get('path','')) is None
                or lease['path'].split('/')[-2] != lease.get('session_id')):return ''
        started = time.monotonic()
        def check():return allowed() and time.monotonic()-started <= 8
        if not check():return ''
        headers = {'Authorization':'Bearer '+binding.token,'X-DJConnect-Device-ID':binding.device_id,
            'X-DJConnect-Client-Type':CLIENT_TYPE,'X-DJConnect-Profile-ID':binding.profile_id,
            'Accept':'image/png,image/jpeg','Cache-Control':'no-store','Accept-Language':locale_for_language(binding.language)}
        params = binding.identity()
        with requests.Session() as client:
            client.trust_env = False
            with client.get(binding.ha_url.rstrip('/')+lease['path'], headers=headers,params=params,
                    stream=True,allow_redirects=False,timeout=(4,4)) as response:
                mime = response.headers.get('Content-Type','').split(';')[0].lower()
                length = response.headers.get('Content-Length')
                if (not check() or response.status_code != 200 or mime not in ('image/png','image/jpeg')
                        or (length is not None and (not length.isdigit() or not 0 < int(length) <= MAX_BYTES))):return ''
                body = bytearray()
                for chunk in response.iter_content(64*1024):
                    if not check() or len(body)+len(chunk) > MAX_BYTES:return ''
                    body.extend(chunk)
        if not check() or (length is not None and len(body) != int(length)):return ''
        return decode_pixels(body,mime,check,(lease['width'],lease['height']))
    except (requests.RequestException,KeyError,TypeError,ValueError,OverflowError):
        return ''


class MomentImages(ForecastImages):
    def __init__(self, owner):
        super().__init__(owner);self.gate = ArtworkGate()

    def sync(self):
        if self.closed:return
        cfg = self.owner.backend.cfg
        eligible = (self.visible and self.owner._foreground and self.owner._running_action not in {'start','end'}
            and bool(cfg.explicit_profile_id) and cfg.explicit_profile_id == cfg.active_profile_id
            and cfg.active_profile_type in {'personal','household'} and cfg.active_profile_privacy_mode == 'private'
            and not cfg.private_session)
        try:
            binding = self.owner.transport.binding() if eligible else None
            lease = self.gate.admit(self.owner._session,self.owner._caps,binding,self.owner._clock.now()) if eligible else None
        except (SessionError,AttributeError,KeyError,TypeError,ValueError):binding = lease = None
        self._set_lease(binding,lease)

    def fetch(self, binding, lease, allowed):
        return fetch_artwork(binding,lease,allowed)

    def public_pixels(self, pixels):
        return {**super().public_pixels(pixels),'moment_id':self.desired['moment_id'],
                'width':self.desired['width'],'height':self.desired['height']}
