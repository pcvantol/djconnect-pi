"""Read-only text Forecast v1 receiver; never a Planner, media grant or history."""
import hashlib
import json
from copy import deepcopy

from .session_projection import session_playback, text, timestamp


def forecast_supported(session, caps):
    return (isinstance(session, dict) and isinstance(caps, dict)
            and isinstance(caps.get('capabilities'), dict) and isinstance(caps.get('contract_versions'), dict)
            and session.get('runtime_state') == 'active'
            and caps.get('capabilities', {}).get('session_forecast') is True
            and type(caps.get('contract_versions', {}).get('session_forecast')) is int
            and caps['contract_versions']['session_forecast'] == 1)


def projection(session, caps, now):
    if not forecast_supported(session, caps):
        return None
    broadcast = session.get('broadcast')
    if not isinstance(broadcast, dict):
        return None
    identity = broadcast.get('session')
    status = broadcast.get('broadcast')
    if (not isinstance(identity, dict) or identity.get('session_id') != session.get('session_id')
            or (isinstance(status, dict) and status.get('subscription_state') == 'revoked')):
        return None
    value = broadcast.get('session_forecast')
    if not isinstance(value, dict) or type(value.get('contract_version')) is not int or value['contract_version'] != 1:
        return None
    revision = value.get('revision')
    if (value.get('session_id') != session.get('session_id') or type(revision) is not int
            or not 0 <= revision < 2**63 or value.get('state') not in ('ready', 'limited', 'empty', 'expired', 'withdrawn')):
        return None
    if value['state'] in ('empty', 'expired', 'withdrawn'):
        return {'state': value['state'], 'revision': revision, 'sections': []}
    issued, deadline = timestamp(value.get('issued_at')), timestamp(value.get('valid_until'))
    if (issued is None or deadline is None or issued > now or not 0 < deadline - issued <= 120
            or type(value.get('nominal_window_seconds')) is not int or value['nominal_window_seconds'] != 900
            or type(value.get('supported_window_seconds')) is not int or value['supported_window_seconds'] not in (0, 900)):
        return None
    if deadline <= now:
        return {'state': 'expired', 'revision': revision, 'sections': []}
    source = ''
    anchor = value.get('current_anchor')
    if anchor is not None:
        playback = session_playback(session)
        if (not isinstance(anchor, dict) or not playback or anchor.get('item_id') != playback['item_id']
                or anchor.get('source_url', '') != playback['source_url']):
            return None
        source = playback['source_url']
    sections = value.get('sections')
    if not isinstance(sections, list) or len(sections) > 3:
        return None
    result, seen = [], set()
    claims = {'current': 'current', 'guidance': 'intention', 'aim': 'conditional_target'}
    for section in sections:
        if not isinstance(section, dict) or not isinstance(section.get('id'), str):
            return None
        key = section['id']
        if key not in claims or key in seen or section.get('claim_type') != claims[key]:
            return None
        if (not text(section.get('text'), 4096) or not text(section.get('title'), 512)
                or (key == 'current' and (anchor is None or section.get('source_url', '') != source))
                or (key != 'current' and section.get('source_url'))):
            return None
        seen.add(key)
        result.append({'id': key, 'claim_type': claims[key], 'title': section['title'], 'text': section['text']})
    return {'state': value['state'], 'revision': revision, 'valid_until': value['valid_until'],
            'summary': text(value.get('summary'), 4096), 'sections': result, 'source_url': source}


class ForecastReceiver:
    def __init__(self):
        self.reset()

    def reset(self):
        self.session_id = ''
        self.revision = -1
        self.terminal = -1
        self.deadline = 0
        self.valid_until = ''
        self.value = {'state': 'empty', 'sections': []}
        self.scope = None
        self.content_signature = ""
        self.style_floors = {}
        self.confirmed_style = {}

    def _runtime_scope(self, session):
        allowed = {
            'selected_mood': ('mood_revision', {'chill', 'groove', 'energy', 'party'}),
            'selected_presence': ('presence_revision', {'music_only', 'occasional', 'balanced', 'talkative', 'presenter'}),
            'dj_persona': ('persona_revision', {'home_dj', 'radio_dj', 'club_dj', 'festival_dj'}),
        }
        style = []
        valid = True
        for field, (counter, values) in allowed.items():
            revision = session.get(counter)
            if type(revision) is not int or not 0 <= revision < 2**63:
                valid = False
                continue
            floor = self.style_floors.get(counter, -1)
            if revision < floor:
                valid = False
                continue
            if revision > floor:
                self.style_floors[counter] = revision
                self.confirmed_style.pop(field, None)
            value = session.get(field)
            if not isinstance(value, str) or value not in values:
                valid = False
                continue
            if field in self.confirmed_style and self.confirmed_style[field] != value:
                valid = False
                continue  # A value cannot change under the same public Runtime revision.
            self.confirmed_style[field] = value
            style.extend((value, revision))
        if not valid:
            return None
        locale = session.get('locale')
        if locale not in ('en', 'nl', 'de', 'fr', 'es'):
            return None
        direction = session.get('session_direction')
        try:
            direction = json.dumps(direction, sort_keys=True, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError, RecursionError):
            return None
        if len(direction) > 4096:
            return None
        playback = session_playback(session)
        raw = session.get('broadcast', {}).get('playback')
        if isinstance(raw, dict) and raw.get('item_id') and not playback:
            return None
        return (*style, locale, direction, playback.get('item_id'), playback.get('source_url'))

    def receive(self, session, caps, now):
        sid = session.get('session_id', '')
        if sid != self.session_id:
            self.reset()
            self.session_id = sid
        scope = self._runtime_scope(session)
        incoming = projection(session, caps, now)
        self.value = {'state': 'withdrawn', 'sections': []}
        if incoming is None or scope is None:
            raw = session.get('broadcast', {}).get('session_forecast')
            observed = raw.get('revision') if isinstance(raw, dict) and raw.get('session_id') == sid else -1
            if type(observed) is not int or not 0 <= observed < 2**63:
                observed = -1
            self.terminal = max(self.terminal, self.revision, observed)
            self.content_signature = ""; self.scope = None
            return
        revision = incoming['revision']
        terminal_state = incoming['state'] in ('expired', 'withdrawn', 'empty')
        if revision < self.revision or revision < self.terminal or (revision == self.terminal and not terminal_state):
            self.terminal = max(self.terminal, self.revision)
            self.content_signature = ""; self.scope = None
            return
        previous = self.revision
        if terminal_state:
            # Released expired reads keep their original revision; invalidation is not new content.
            self.revision = revision
            self.terminal = max(self.terminal, revision)
            self.value = incoming
            self.content_signature = ""; self.scope = None
            return
        content = {key: value for key, value in incoming.items() if key != 'valid_until'}
        signature = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()
        if revision == previous and (scope != self.scope or signature != self.content_signature):
            self.terminal = max(self.terminal, revision)
            self.content_signature = ""; self.scope = None
            return
        self.revision = revision
        deadline = timestamp(incoming['valid_until'])
        if revision == previous and deadline >= self.deadline:
            incoming['valid_until'] = self.valid_until
        else:
            self.deadline = deadline
            self.valid_until = incoming['valid_until']
        # Only a newly admitted revision can bind content to another Runtime scope.
        self.scope = scope
        self.content_signature = signature
        self.value = incoming
        self.expire(now)

    def expire(self, now):
        if self.value.get('state') in ('ready', 'limited') and now >= self.deadline:
            self.terminal = max(self.terminal, self.revision)
            self.value = {'state': 'expired', 'revision': self.revision, 'sections': []}
            self.content_signature = ""; self.scope = None
            return True
        return False

    def snapshot(self):
        return deepcopy(self.value)
