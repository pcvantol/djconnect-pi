"""Prepared Moment conformance; synthetic joins never claim producer/live proof."""
import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_artwork import ArtworkGate, artwork_lease, fetch_artwork
from djconnect_pi.session_forecast_image import decode_pixels
from djconnect_pi.session_history_view import live_presentations
from djconnect_pi.session_projection import timestamp
from djconnect_pi.session_transport import SessionBinding

pytest_plugins=['test_session_controller']
ROOT=Path(__file__).parent/'fixtures/session_core'
MEDIA=json.loads((ROOT/'artwork-transport-v1.json').read_text())
NATIVE=json.loads((ROOT/'native-expressive-snapshots.json').read_text())
PIXELS=(ROOT/'forecast-test-pixels.png').read_bytes()


def frame(language='nl', kind='artist_story'):
    family='birth' if kind=='artist_story' else 'edition'
    snap=deepcopy(next(s for s in NATIVE[family][language]['home_dj'] if s['native_delivery']['current_moment_id']))
    sid=snap['session']['session_id'];mid=snap['native_delivery']['current_moment_id']
    grant=next(g for g in snap['native_delivery']['admissions'] if g['moment_id']==mid)
    now=timestamp(grant['display_expires_at'])-1
    p=deepcopy(MEDIA['examples'][kind]['projection']);p['session_id']=sid;p['moment_id']=mid
    # Explicit synthetic current-artist grant overlay; original fixture is flow-only.
    a=p['artwork'];a['current_display_allowed']=True;a['url']='/api/djconnect/v1/session/media/image/'+sid+'/synthetic-resource'
    a['captured_at']=datetime.fromtimestamp(now-1,UTC).isoformat()
    a['expires_at']=datetime.fromtimestamp(now+.5,UTC).isoformat()
    a.pop('media_revision',None);p['revision']=hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest()[:24]
    a['media_revision']=p['revision'];snap['session_media']=[p]
    binding=SessionBinding('https://fixture.invalid','synthetic-device','synthetic-secret','profile-a','profile-a',False,'personal','private',language)
    caps={'capabilities':{'session_artwork':True},'contract_versions':{'session_artwork':1}}
    return {**snap['session'],'broadcast':snap},caps,binding,now


class Response:
    def __init__(self,body=PIXELS,status=200,mime='image/png'):
        self.body=body;self.status_code=status;self.headers={'Content-Type':mime,'Content-Length':str(len(body))}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,size):yield self.body


class Client:
    def __init__(self,response):self.get=Mock(return_value=response);self.trust_env=True
    def __enter__(self):return self
    def __exit__(self,*args):pass


def prepare(owner):
    s,c,_binding,n=frame();owner._session=s;owner._caps=c
    host=SimpleNamespace(wall=n,tick=0);owner._clock=ExpiryClock(lambda:host.wall,lambda:host.tick)
    owner._moments=live_presentations(s,now=n)
    jobs=[];store=owner._moment_images;store.executor=SimpleNamespace(submit=jobs.append,shutdown=lambda **kw:None)
    return host,jobs,store


@pytest.mark.parametrize('lang',['en','nl','de','fr','es'])
@pytest.mark.parametrize('kind',['artist_story','album_story'])
def test_exact_current_native_and_independent_prepared_subject_grant(lang,kind):
    s,c,b,n=frame(lang,kind);lease=artwork_lease(s,c,b,n)
    assert lease and lease['moment_id']==s['broadcast']['native_delivery']['current_moment_id']
    assert lease['deadline']<=n+.5 and lease['artist']==s['broadcast']['session_media'][0]['artwork']['alt_text'][lang]
    assert live_presentations(s,now=n)


@pytest.mark.parametrize('field,bad',[
 ('state','loading'),('role','playback_thumbnail'),('current_display_allowed',False),
 ('current_display_allowed',1),('historical_display_allowed',True),('active_flow_display_allowed',False),
 ('crop_allowed',True),('requires_device_auth',False),('cache_policy','disk'),
 ('usage_basis','spotify_display_current_only'),('resolution_basis','observed'),
 ('edition_basis','original_bound'),('source_url','https://open.spotify.com/artist/'+'Z'*22),
 ('attribution',{}),('media_revision','unknown'),('captured_at','2099-01-01T00:00:00Z'),
 ('expires_at','2099-01-01T00:00:00Z'),('expires_at','no-zone'),('width',True),('height',4096),
 ('subject',{'provider':'spotify','type':'artist','uri':'same-name'}),
 ('url','https://external.invalid/image.png'),('url','/api/djconnect/v1/session/forecast/art/s/a')])
def test_bad_artwork_degrades_without_removing_valid_native_text(field,bad):
    s,c,b,n=frame();s['broadcast']['session_media'][0]['artwork'][field]=bad
    assert artwork_lease(s,c,b,n) is None and live_presentations(s,now=n)


@pytest.mark.parametrize('bad',['caps','versionbool','foreignsession','entry','duplicate','wrongmoment','nativewithdrawn'])
def test_root_scope_never_borrows_history_or_playback_authority(bad):
    s,c,b,n=frame();p=s['broadcast']['session_media'][0]
    if bad=='caps':c['capabilities']['session_artwork']=False
    elif bad=='versionbool':c['contract_versions']['session_artwork']=True
    elif bad=='foreignsession':p['session_id']='foreign'
    elif bad=='entry':p['entry_id']='retained-row'
    elif bad=='duplicate':s['broadcast']['session_media'].append(deepcopy(p))
    elif bad=='wrongmoment':p['moment_id']='foreign'
    else:s['broadcast']['native_delivery']['current_moment_id']=None
    assert artwork_lease(s,c,b,n) is None


def test_paired_image_get_sends_exact_owner_identity_and_no_ambient_credentials():
    s,c,b,n=frame();lease=artwork_lease(s,c,b,n);client=Client(Response())
    with patch('djconnect_pi.session_artwork.requests.Session',return_value=client):out=fetch_artwork(b,lease,lambda:True)
    assert out.startswith('data:image/png;base64,') and client.trust_env is False
    args,kwargs=client.get.call_args
    assert args==(b.ha_url+lease['path'],)
    assert kwargs['headers']=={'Authorization':'Bearer '+b.token,'X-DJConnect-Device-ID':b.device_id,
        'X-DJConnect-Client-Type':'raspberry_pi','X-DJConnect-Profile-ID':b.profile_id,
        'Accept':'image/png,image/jpeg','Cache-Control':'no-store','Accept-Language':'nl-NL'}
    assert kwargs['params']==b.identity() and kwargs['allow_redirects'] is False and kwargs['timeout']==(4,4)
    assert kwargs['stream'] is True


@pytest.mark.parametrize('bad',['forecast','cdn','foreignsession','userinfo','originpath','profile','guest','private'])
def test_credentials_never_forward_to_wrong_route_origin_or_context(bad):
    s,c,b,n=frame();lease=artwork_lease(s,c,b,n)
    if bad=='forecast':lease['path']='/api/djconnect/v1/session/forecast/art/s/a'
    elif bad=='cdn':lease['path']='https://i.scdn.co/image/'+'a'*40
    elif bad=='foreignsession':lease['session_id']='foreign'
    elif bad=='userinfo':b=replace(b,ha_url='https://user:pw@fixture.invalid')
    elif bad=='originpath':b=replace(b,ha_url='https://fixture.invalid/ha')
    elif bad=='profile':b=replace(b,resolved_profile_id='foreign')
    elif bad=='guest':b=replace(b,profile_type='guest')
    else:b=replace(b,private_session=True)
    with patch('djconnect_pi.session_artwork.requests.Session') as request:
        assert not fetch_artwork(b,lease,lambda:True)
    request.assert_not_called()


@pytest.mark.parametrize('status',[301,302,401,403,404,500])
def test_denied_or_redirected_bytes_have_no_fallback_or_retry(status):
    s,c,b,n=frame();client=Client(Response(status=status))
    with patch('djconnect_pi.session_artwork.requests.Session',return_value=client):
        assert not fetch_artwork(b,artwork_lease(s,c,b,n),lambda:True)
    assert client.get.call_count==1


def test_declared_dimensions_bind_actual_pixels_and_late_cancel_drops_bytes():
    s,c,b,n=frame();lease=artwork_lease(s,c,b,n)
    client=Client(Response());lease['width']=65
    with patch('djconnect_pi.session_artwork.requests.Session',return_value=client):
        assert not fetch_artwork(b,lease,lambda:True)
    assert not decode_pixels(PIXELS,'image/png',lambda:True,(65,64))
    assert not decode_pixels(PIXELS,'image/gif',lambda:True)
    permitted=iter([True,True,False])
    with patch('djconnect_pi.session_artwork.requests.Session',return_value=Client(Response())):
        assert not fetch_artwork(b,artwork_lease(s,c,b,n),lambda:next(permitted))


def test_opaque_revision_is_equality_not_sort_order_and_rollback_cannot_revive():
    s,c,b,n=frame();p=s['broadcast']['session_media'][0];gate=ArtworkGate()
    p['revision']='f'*24;assert gate.admit(s,c,b,n)
    p['revision']='0'*24;assert gate.admit(s,c,b,n)
    p['revision']='f'*24;assert gate.admit(s,c,b,n) is None


def test_observed_withdrawal_and_same_revision_content_change_latch():
    s,c,b,n=frame();gate=ArtworkGate();assert gate.admit(s,c,b,n)
    original=deepcopy(s);s['broadcast']['session_media']=[];assert gate.admit(s,c,b,n) is None
    assert gate.admit(original,c,b,n) is None
    s=deepcopy(original);gate=ArtworkGate();assert gate.admit(s,c,b,n)
    s['broadcast']['session_media'][0]['artwork']['alt_text']['nl']='different'
    assert gate.admit(s,c,b,n) is None and gate.admit(original,c,b,n) is None


def test_metadata_budget_and_asset_expiry_are_original_and_bounded():
    s,c,b,n=frame();gate=ArtworkGate();first=gate.admit(s,c,b,n);p=s['broadcast']['session_media'][0]
    for i in range(100):p['revision']=f'{i:024x}';gate.admit(s,c,b,n)
    assert len(gate.seen)==32 and len(gate.revoked)<=32 and len(gate.floors)<=32
    gate=ArtworkGate();assert gate.admit(s,c,b,n)
    p['revision']='e'*24;p['artwork']['expires_at']=datetime.fromtimestamp(n+.9,UTC).isoformat()
    assert gate.admit(s,c,b,n)['deadline']==first['deadline']
    assert gate.admit(s,c,b,n+.6) is None


@pytest.mark.parametrize('reason',['foreground','profile','end','expiry','capability','native','hidden'])
def test_queued_reads_stop_before_paired_credentials_are_dispatched(controller,reason):
    owner,backend=controller;host,jobs,store=prepare(owner);owner.setMomentArtworkVisible(True);job=jobs.pop()
    if reason=='foreground':owner.setForeground(False)
    elif reason=='profile':backend.cfg.active_profile_id='foreign';owner.invalidate()
    elif reason=='end':owner.end(owner._session['session_id'])
    elif reason=='expiry':host.tick=.6
    elif reason=='capability':owner._caps['capabilities']['session_artwork']=False;owner.changed.emit()
    elif reason=='native':owner._session['broadcast']['native_delivery']['current_moment_id']=None;owner.changed.emit()
    else:owner.setMomentArtworkVisible(False)
    with patch('djconnect_pi.session_artwork.requests.Session') as request:job()
    request.assert_not_called();assert not owner.momentArtwork and not store.public


def test_image_only_expiry_preserves_native_text_and_notifies_after_atomic_clear(controller):
    owner,_=controller;host,jobs,store=prepare(owner);owner.setMomentArtworkVisible(True)
    from base64 import b64encode
    with patch('djconnect_pi.session_artwork.fetch_artwork',return_value='data:image/png;base64,'+b64encode(PIXELS).decode()):jobs.pop()()
    assert owner.momentArtwork['moment_id'] and live_presentations(owner._session,now=owner._clock.now())
    host.tick=.6;assert not owner.momentArtwork and not store.public
    store._tick();assert live_presentations(owner._session,now=owner._clock.now())


def test_original_flow_only_artist_projection_is_not_promoted_to_current():
    s,c,b,n=frame()
    s['broadcast']['session_media'][0]['artwork']['current_display_allowed']=False
    assert artwork_lease(s,c,b,n) is None
