"""Bounded image bytes and GUI withdrawal; transports/pixels are fixtures only."""
import base64
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_forecast import projection
from djconnect_pi.session_forecast_image import MAX_BYTES, ImageGate, fetch_pixels
from djconnect_pi.session_projection import timestamp

pytest_plugins = ['test_session_controller']
FIXTURES=Path(__file__).parent/'fixtures/session_core'
PIXELS=(FIXTURES/'forecast-test-pixels.png').read_bytes()
DATA='data:image/png;base64,'+base64.b64encode(PIXELS).decode()


def frame(index=0):
    fixture=json.loads((FIXTURES/'forecast-transport-v1.json').read_text())[index]
    snapshot=deepcopy(fixture['reconnect']['snapshot']);snapshot['session_forecast']=deepcopy(fixture['owner_read']['forecast'])
    # Explicit fixture Runtime-style envelope, not a newly captured Runtime claim.
    session={**snapshot['session'],'broadcast':snapshot,'dj_persona':fixture['persona'],'persona_revision':0,
        'session_direction':snapshot['planner']['session_direction']}
    caps={'capabilities':{'session_forecast':True},'contract_versions':{'session_forecast':1}}
    now=timestamp(snapshot['session_forecast']['issued_at'])+0.001
    return session,caps,now


def ready(owner):
    session,caps,now=frame();host=SimpleNamespace(wall=now,tick=0)
    owner._clock=ExpiryClock(lambda:host.wall,lambda:host.tick)
    owner._session=session;owner._caps=caps;owner._forecast.receive(session,caps,now)
    jobs=[];owner._forecast_images.executor=SimpleNamespace(submit=jobs.append,shutdown=lambda **kw:None)
    return host,jobs


class Response:
    def __init__(self,body=PIXELS,status=200,mime='image/png',length=None):
        self.body=body;self.status_code=status;self.closed=False;self.reads=0
        self.headers={'Content-Type':mime,'Content-Length':str(len(body)) if length is None else length}
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def iter_content(self,size):
        self.reads+=1
        yield self.body


class Client:
    def __init__(self,response):self.get=Mock(return_value=response);self.trust_env=True
    def __enter__(self):return self
    def __exit__(self,*args):pass


def lease_and_binding():
    session,caps,now=frame();binding=SimpleNamespace(ha_url='https://owner-ha.invalid')
    lease=ImageGate().admit(session,projection(session,caps,now),'owner',now)
    return lease,binding


@pytest.mark.parametrize('index',range(20))
def test_unchanged_protected_twenty_frames_admit_one_typed_current_artist(index):
    session,caps,now=frame(index);gate=ImageGate()
    lease=gate.admit(session,projection(session,caps,now),'owner',now)
    assert lease and lease['subject_id']=='spotify:artist:XXXXXXXXXXXXXXXXXXXXXX'
    assert lease['deadline']==timestamp(session['broadcast']['session_forecast']['valid_until'])
    assert gate.admit(session,projection(session,caps,now),'owner',lease['deadline']) is None


@pytest.mark.parametrize('field,bad',[
 ('url','https://outside.invalid/a.png'),('url','/api/djconnect/v1/session/media/image/s/a'),
 ('role','qualified_upcoming'),('source_url','https://open.spotify.com/artist/YYYYYYYYYYYYYYYYYYYYYY'),
 ('attribution',{}),('usage_basis','private_discovery'),('cache_policy','public'),
 ('subject',{'type':'artist','id':'name-only','name':'Same display name'}),('expires_at','2099-01-01T00:00:00Z')])
def test_bad_media_never_borrows_text_or_history_authority(field,bad):
    session,caps,now=frame();session['broadcast']['session_forecast']['imagery'][0][field]=bad
    text=projection(session,caps,now)
    assert text['sections'] and ImageGate().admit(session,text,'owner',now) is None


def test_observed_withdrawal_or_equal_revision_change_cannot_revive_pixels():
    session,caps,now=frame();gate=ImageGate();text=projection(session,caps,now)
    assert gate.admit(session,text,'owner',now)
    original=deepcopy(session);session['broadcast']['session_forecast']['imagery']=[]
    assert gate.admit(session,text,'owner',now) is None
    assert gate.admit(original,text,'owner',now) is None
    original['broadcast']['session_forecast']['revision']+=1;text['revision']+=1
    assert gate.admit(original,text,'owner',now)


def test_reused_asset_keeps_original_asset_expiry_under_new_forecast_revision():
    session,caps,now=frame();gate=ImageGate();first=gate.admit(session,projection(session,caps,now),'owner',now)
    f=session['broadcast']['session_forecast'];old_asset=timestamp(f['imagery'][0]['expires_at'])
    f['revision']+=1;f['issued_at']=datetime.fromtimestamp(now+200,UTC).isoformat()
    f['valid_until']=datetime.fromtimestamp(now+320,UTC).isoformat()
    f['imagery'][0]['expires_at']=datetime.fromtimestamp(old_asset+50,UTC).isoformat()
    second=gate.admit(session,projection(session,caps,now+200),'owner',now+200)
    assert first and second and second['deadline']==old_asset


def test_managed_forecast_get_is_headerless_bounded_and_preserves_original_pixels():
    lease,binding=lease_and_binding();response=Response();client=Client(response)
    with patch('djconnect_pi.session_forecast_image.requests.Session',return_value=client):
        source=fetch_pixels(binding,lease,lambda:True)
    assert base64.b64decode(source.split(',',1)[1])==PIXELS and response.closed
    assert client.trust_env is False
    call=client.get.call_args
    assert call.args==(binding.ha_url+lease['path'],)
    assert call.kwargs=={'headers':{'Accept':'image/png,image/jpeg','Cache-Control':'no-store'},
        'stream':True,'allow_redirects':False,'timeout':(4,4)}
    assert 'Authorization' not in call.kwargs['headers'] and 'cookies' not in call.kwargs


@pytest.mark.parametrize('status',[301,302,401,403,404,429,500])
def test_redirects_and_denials_never_decode_or_retry(status):
    lease,binding=lease_and_binding();response=Response(status=status);client=Client(response)
    with patch('djconnect_pi.session_forecast_image.requests.Session',return_value=client):
        assert not fetch_pixels(binding,lease,lambda:True)
    assert not response.reads and response.closed and client.get.call_count==1


@pytest.mark.parametrize('body,mime,length',[
 (PIXELS,'image/svg+xml',None),(PIXELS,'image/jpeg',None),(b'invalid','image/png',None),
 (PIXELS+b'acTL','image/png',None),(PIXELS,'image/png',str(MAX_BYTES+1)),
 (PIXELS,'image/png','0'),(PIXELS,'image/png','-1'),(PIXELS,'image/png','nan'),
 (PIXELS,'image/png','1'),(b'x'*(MAX_BYTES+1),'image/png',None)])
def test_mime_magic_animation_size_and_length_fail_to_text(body,mime,length):
    lease,binding=lease_and_binding();client=Client(Response(body,mime=mime,length=length))
    with patch('djconnect_pi.session_forecast_image.requests.Session',return_value=client):
        assert not fetch_pixels(binding,lease,lambda:True)


@pytest.mark.parametrize('origin',['https://u:p@ha.invalid','file:///tmp','https://ha.invalid/path',
 'https://ha.invalid?token=x','https://ha.invalid:bad','https://[bad'])
def test_bad_configured_origin_is_not_a_fetch_authority(origin):
    lease,binding=lease_and_binding();binding.ha_url=origin
    with patch('djconnect_pi.session_forecast_image.requests.Session') as request:
        assert not fetch_pixels(binding,lease,lambda:True)
    request.assert_not_called()


def test_cancel_before_dispatch_and_between_chunks_leaves_no_pixels():
    lease,binding=lease_and_binding()
    with patch('djconnect_pi.session_forecast_image.requests.Session') as request:
        assert not fetch_pixels(binding,lease,lambda:False)
    request.assert_not_called()
    client=Client(Response());allowed=iter([True,True,False])
    with patch('djconnect_pi.session_forecast_image.requests.Session',return_value=client):
        assert not fetch_pixels(binding,lease,lambda:next(allowed))


def test_no_fetch_until_explicit_forecast_visibility_and_failed_read_has_no_poll_retry(controller):
    owner,_=controller;_,jobs=ready(owner);images=owner._forecast_images
    owner.changed.emit();assert not jobs and not owner.forecastImage
    owner.setForecastImagesVisible(True);assert len(jobs)==1
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value='') as fetch:
        jobs.pop()();owner.changed.emit();images.sync()
    assert fetch.call_count==1 and not jobs and not owner.forecastImage


def test_delivered_pixels_are_ram_only_and_expiry_getter_then_tick_withdraws(controller):
    owner,_=controller;host,jobs=ready(owner);images=owner._forecast_images
    owner.setForecastImagesVisible(True)
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=DATA):jobs.pop()()
    assert owner.forecastImage['source']==DATA
    notify=Mock();owner.forecastImageChanged.connect(notify)
    host.tick=121
    assert not owner.forecastImage and not images.public
    assert not notify.call_count
    images._tick();assert notify.call_count==1 and not owner.forecastImage


@pytest.mark.parametrize('withdrawal',['foreground','profile','end','expiry','paused','capability','shutdown'])
def test_queued_image_read_after_withdrawal_never_starts_http_or_restores_pixels(controller,withdrawal):
    owner,backend=controller;host,jobs=ready(owner);images=owner._forecast_images
    owner.setForecastImagesVisible(True);work=jobs.pop()
    if withdrawal=='foreground':owner.setForeground(False)
    elif withdrawal=='profile':backend.cfg.active_profile_id='foreign';owner.invalidate()
    elif withdrawal=='end':owner.end(owner._session['session_id'])
    elif withdrawal=='expiry':host.tick=121
    elif withdrawal=='shutdown':images.shutdown()
    elif withdrawal=='paused':owner._session['broadcast']['playback']['state']='paused';owner.changed.emit()
    else:owner._caps['capabilities']['session_forecast']=False;owner._forecast.receive(owner._session,owner._caps,host.wall);owner.changed.emit()
    with patch('djconnect_pi.session_forecast_image.requests.Session') as request:work()
    request.assert_not_called();assert not owner.forecastImage


def test_hide_releases_public_pixels_and_at_most_one_latest_image_job_is_queued(controller):
    owner,_=controller;_,jobs=ready(owner);images=owner._forecast_images
    owner.setForecastImagesVisible(True);old=jobs.pop()
    owner.setForecastImagesVisible(False);owner.setForecastImagesVisible(True)
    assert not jobs and images.running
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=DATA):old()
    assert not owner.forecastImage and len(jobs)==1
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=DATA):jobs.pop()()
    assert owner.forecastImage
    owner.setForecastImagesVisible(False);assert not owner.forecastImage and not images.public


def test_explicit_view_retries_are_still_session_bounded(controller):
    owner,_=controller;_,jobs=ready(owner);images=owner._forecast_images
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=''):
        for _ in range(40):
            owner.setForecastImagesVisible(True)
            if jobs:jobs.pop()()
            owner.setForecastImagesVisible(False)
    assert images.attempts==32 and not jobs


def test_platform_decode_failure_settles_worker_without_hidden_retry(controller):
    owner,_=controller;_,jobs=ready(owner)
    owner.setForecastImagesVisible(True)
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',side_effect=RuntimeError('synthetic decoder failure')):jobs.pop()()
    assert not owner._forecast_images.running and not owner.forecastImage and not jobs


def test_exact_deadline_timer_clears_pixels_without_periodic_polling(controller):
    owner,_=controller;host,jobs=ready(owner);images=owner._forecast_images
    owner.setForecastImagesVisible(True)
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=DATA):jobs.pop()()
    assert images.deadline_timer.isActive() and owner.forecastImage
    host.tick=121;images._deadline_tick()
    assert not images.public and not owner.forecastImage


def test_actual_image_thread_does_not_hold_end_and_late_bytes_are_discarded():
    # A fresh Qt process owns its application/thread; do not pump earlier tests' Qt state.
    import os
    import subprocess
    import sys
    import textwrap
    root=Path(__file__).parents[1]
    script=textwrap.dedent("""
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from unittest.mock import patch
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtTest import QTest
        from shiboken6 import delete
        from test_session_controller import Backend
        from test_session_forecast_image import ready, DATA
        from djconnect_pi.session_controller import SessionController
        app=QCoreApplication([]);backend=Backend();owner=SessionController(backend)
        ready(owner);images=owner._forecast_images;images.executor=ThreadPoolExecutor(max_workers=1)
        started=threading.Event();release=threading.Event()
        def held(binding,lease,allowed):
            started.set();assert release.wait(3);return DATA
        try:
            with patch('djconnect_pi.session_forecast_image.fetch_pixels',side_effect=held):
                owner.setForecastImagesVisible(True);assert started.wait(1)
                owner.end(owner._session['session_id']);assert owner.lifecycleBusy and backend.jobs
                release.set()
                for _ in range(60):
                    QTest.qWait(10)
                    if not images.running:break
                assert not images.running and not owner.forecastImage
                print('End-before-byte-release; late image withdrawn; real image thread PASS')
        finally:
            release.set();images.shutdown();images.executor.shutdown(wait=True)
            delete(owner);delete(backend)
    """)
    env={**os.environ,'PYTHONPATH':os.pathsep.join([str(root/'src'),str(root/'tests')])}
    result=subprocess.run([sys.executable,'-c',script],cwd=root,env=env,capture_output=True,text=True,timeout=15,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'real image thread PASS' in result.stdout


def test_retained_image_floors_store_only_hashed_authority_context(controller):
    owner,_=controller;_,jobs=ready(owner)
    owner.setForecastImagesVisible(True)
    context=owner._forecast_images.gate.context
    assert isinstance(context,str) and len(context)==64
    assert owner.backend.cfg.device_token not in context and owner.backend.cfg.active_profile_id not in context
    owner.setForecastImagesVisible(False)
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=''):jobs.pop()()


def test_lost_pairing_is_text_fallback_without_image_request_or_exception(controller):
    owner,backend=controller;_,jobs=ready(owner)
    backend.cfg.paired=False
    with patch('djconnect_pi.session_forecast_image.requests.Session') as request:
        owner.setForecastImagesVisible(True);owner.changed.emit()
    assert not jobs and not owner.forecastImage
    request.assert_not_called()


@pytest.mark.parametrize('withdrawal', ['hidden', 'expiry', 'foreground'])
def test_position_notice_precedes_pixel_publication_and_atomic_withdrawal(controller, withdrawal):
    owner,_=controller;host,jobs=ready(owner);images=owner._forecast_images
    before=[];after=[]
    owner.forecastImageAboutToChange.connect(lambda:before.append(bool(images.public)))
    owner.forecastImageChanged.connect(lambda:after.append(bool(images.public)))
    owner.setForecastImagesVisible(True)
    with patch('djconnect_pi.session_forecast_image.fetch_pixels',return_value=DATA):jobs.pop()()
    assert before == [False] and after[-1] is True
    images.sync()  # Equal state cannot manufacture a new layout transition.
    assert before == [False]
    if withdrawal == 'hidden':owner.setForecastImagesVisible(False)
    elif withdrawal == 'foreground':owner.setForeground(False)
    else:host.tick=121;images._deadline_tick()
    assert before == [False, True] and after[-1] is False and not images.public
    images.sync()
    assert before == [False, True]
