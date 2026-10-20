"""Actual bounded Forecast image decode/QML; only synthetic HTTP and owned pixels."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QMetaObject, QObject, QPoint, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlEngine, QQmlExpression
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_projection import timestamp

ROOT=Path(__file__).resolve().parents[1]


class Response:
    status_code=200
    def __init__(self,body):self.body=body;self.headers={'Content-Type':'image/png','Content-Length':str(len(body))}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,size):yield self.body


class Client:
    def __init__(self,body,calls):self.body=body;self.calls=calls;self.trust_env=True
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def get(self,url,**kwargs):
        assert self.trust_env is False and url.startswith('http://fixture.invalid/api/djconnect/v1/session/forecast/art/')
        assert kwargs=={'headers':{'Accept':'image/png,image/jpeg','Cache-Control':'no-store'},'stream':True,'allow_redirects':False,'timeout':(4,4)}
        self.calls.append(True)  # Never record managed URLs or pixel bytes in diagnostics.
        return Response(self.body)


def main():
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('--output',type=Path,required=True)
    output=parser.parse_args().output;output.mkdir(parents=True,exist_ok=True)
    warnings=[];qInstallMessageHandler(lambda kind,context,message:warnings.append(message))
    QQuickStyle.setStyle('Basic');app=QGuiApplication([]);apply_palette(app);captures=[];touch_device=QTest.createTouchDevice()
    fixtures=json.loads((ROOT/'tests/fixtures/session_core/forecast-transport-v1.json').read_text())
    pixels=(ROOT/'tests/fixtures/session_core/forecast-test-pixels.png').read_bytes();calls=[]
    with patch('djconnect_pi.session_forecast_image.requests.Session',side_effect=lambda:Client(pixels,calls)):
        for width,height,profile in [(720,720,'pi-zero-2w-arm64'),(1200,1920,'pi5-arm64')]:
            config=output/f'fixture-{width}.json'
            save_config(config,Config(language='nl',release_profile=profile,log_file=str(output/'fixture.log'),paired=True,
                device_token='synthetic-not-a-credential',device_id='djconnect-raspberry-pi-fixture',ha_url='http://fixture.invalid',
                active_profile_id='profile-fixture',explicit_profile_id='profile-fixture',active_profile_type='personal',
                active_profile_privacy_mode='private',screen_timeout_seconds=0))
            with patch.object(QTimer,'singleShot'):backend=DJConnectBackend(config)
            for timer in backend.findChildren(QTimer):timer.stop()
            backend._executor.submit=Mock();control=[]
            backend._session_executor.submit=control.append;backend._question_executor.submit=Mock()
            owner=backend.djSession;images=owner._forecast_images;jobs=[]
            images.executor=SimpleNamespace(submit=jobs.append,shutdown=lambda **kwargs:None)
            owner.transport.active=Mock(return_value={'success':True,'session':None});owner.transport.capabilities=Mock(return_value={})
            engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('djconnect',backend)
            engine.rootContext().setContextProperty('startWindowed',True);engine.load(str(ROOT/'src/djconnect_pi/qml/Main.qml'))
            assert engine.rootObjects(),warnings
            window=engine.rootObjects()[0];window.setWidth(width);window.setHeight(height);window.setProperty('splashVisible',False)
            for obj in window.findChildren(QObject):
                if 'Timer' in obj.metaObject().className() and obj.property('interval') in (3000,15000):
                    expression=QQmlExpression(engine.rootContext(),obj,'running=false');expression.evaluate();assert not expression.hasError()
            screen=window.findChild(QObject,'djSessionScreen');art=window.findChild(QObject,'sessionForecastArtistImage')
            card=window.findChild(QObject,'sessionForecastArtistCard')
            def drain():
                for _ in range(3):
                    QTest.qWait(40)
                    if control:control.pop(0)()
                assert not control
            def capture(name):
                QTest.qWait(100);target=output/f'{name}-{width}x{height}.png'
                assert window.grabWindow().save(str(target));captures.append(target.name)
            for language in ['en','nl','de','fr','es']:
                if not owner._foreground:owner.setForeground(True)
                drain();backend.setLanguage(language);backend._toast_visible=False;backend.toastChanged.emit();drain();owner.invalidate()
                sample=next(f for f in fixtures if f['language']==language and f['persona']=='home_dj')
                snapshot=deepcopy(sample['reconnect']['snapshot']);snapshot['session_forecast']=deepcopy(sample['owner_read']['forecast'])
                session={**snapshot['session'],'broadcast':snapshot,'dj_persona':sample['persona'],'persona_revision':0,
                    'session_direction':snapshot['planner']['session_direction']}
                # Explicit Runtime-style envelope; source transport/pure authored prose unchanged.
                stamp=timestamp(snapshot['session_forecast']['issued_at'])+0.001;elapsed=[0.0];wall=[stamp]
                owner._clock=ExpiryClock(lambda:wall[0],lambda:elapsed[0])
                owner._session=session;owner._caps={'capabilities':{'session_forecast':True},'contract_versions':{'session_forecast':1}}
                owner._forecast.receive(session,owner._caps,stamp);owner._loaded=True;owner.changed.emit()
                window.setProperty('activeScreen','session');drain()
                if not screen.property('showForecast'):QMetaObject.invokeMethod(window.findChild(QObject,'sessionForecastMode'),'clicked')
                QTest.qWait(60);assert len(jobs)==1
                forecast_flick=window.findChild(QObject,'sessionForecastScroll').property('contentItem')
                forecast_flick.setProperty('contentY',0)
                jobs.pop(0)();QTest.qWait(400)
                assert abs(forecast_flick.property('contentY'))<1,'Late image must not follow when reading the top header'
                assert owner.forecastImage and art.property('source').toString().startswith('data:image/png;base64,')
                assert art.property('cache') is False and card.property('visible')
                assert QQmlExpression(engine.rootContext(),art,'status === 1 && fillMode === 1').evaluate()[0]
                assert owner.state['forecast']['sections'] and len(owner.state['forecast']['sections'])==3
                capture('forecast-artist-original-owned-test-pixels-'+language)
                # A wrong route receives no authentication fallback, lookup or request.
                f=session['broadcast']['session_forecast'];original_path=f['imagery'][0]['url']
                f['revision']+=1;f['imagery'][0]['url']='/api/djconnect/v1/session/media/image/not-a-grant'
                before=len(calls);owner._forecast.receive(session,owner._caps,owner._clock.now());owner.changed.emit();QTest.qWait(80)
                assert not owner.forecastImage and not card.property('visible') and not jobs and len(calls)==before
                assert len(owner.state['forecast']['sections'])==3
                capture('forecast-artist-wrong-route-text-only-'+language)
                # Explicit synthetic shorter asset lease; original producer fixture bytes are unchanged.
                f['revision']+=1;f['imagery'][0]['url']=original_path
                from datetime import UTC, datetime
                f['imagery'][0]['expires_at']=datetime.fromtimestamp(stamp+4,UTC).isoformat()
                owner._forecast.receive(session,owner._caps,owner._clock.now());owner.changed.emit();assert len(jobs)==1
                jobs.pop(0)();QTest.qWait(80);assert owner.forecastImage
                elapsed[0]=6;wall[0]-=500
                QMetaObject.invokeMethod(images.deadline_timer,'timeout');QTest.qWait(80)
                assert not owner.forecastImage and not card.property('visible') and not art.property('source').toString()
                assert len(owner.state['forecast']['sections'])==3
                capture('forecast-artist-expired-pixels-text-kept-'+language)
                # A different synthetic managed asset models a new explicit grant, not old-asset renewal.
                f['revision']+=1;f['imagery'][0]['url']=original_path.rsplit('/',1)[0]+'/'+'z'*32
                f['imagery'][0]['expires_at']=sample['owner_read']['forecast']['imagery'][0]['expires_at']
                owner._forecast.receive(session,owner._caps,owner._clock.now());owner.changed.emit();assert len(jobs)==1
                jobs.pop(0)();QTest.qWait(80);assert owner.forecastImage
                QMetaObject.invokeMethod(window.findChild(QObject,'sessionFlowMode'),'clicked');QTest.qWait(80)
                assert not owner.forecastImage and not images.public and not art.property('source').toString()
                capture('forecast-artist-hidden-releases-pixels-'+language)
                QMetaObject.invokeMethod(window.findChild(QObject,'sessionForecastMode'),'clicked');QTest.qWait(40)
                assert len(jobs)==1;late=jobs.pop(0);before=len(calls)
                owner.setForeground(False);late();QTest.qWait(80)
                assert not owner.forecastImage and not owner.state['session_id'] and len(calls)==before
                assert not art.property('source').toString()
                capture('forecast-artist-background-late-request-withdrawn-'+language)
                # Explicit synthetic long text exposes reading offsets on both canvases.
                owner.setForeground(True);drain();owner.invalidate()
                snapshot=deepcopy(sample['reconnect']['snapshot']);snapshot['session_forecast']=deepcopy(sample['owner_read']['forecast'])
                f=snapshot['session_forecast'];f['revision']+=100
                for section in f['sections']:section['text']=((section['text']+' ') * 100)[:3000]
                f['imagery'][0]['url']=original_path.rsplit('/',1)[0]+'/'+'r'*32
                f['imagery'][0]['expires_at']=datetime.fromtimestamp(stamp+30,UTC).isoformat()
                session={**snapshot['session'],'broadcast':snapshot,'dj_persona':sample['persona'],'persona_revision':0,
                    'session_direction':snapshot['planner']['session_direction']}
                elapsed=[0.0];wall=[stamp];owner._clock=ExpiryClock(lambda:wall[0],lambda:elapsed[0])
                owner._session=session;owner._caps={'capabilities':{'session_forecast':True},'contract_versions':{'session_forecast':1}}
                owner._forecast.receive(session,owner._caps,stamp);owner._loaded=True;owner.changed.emit()
                window.setProperty('activeScreen','session');drain()
                if not screen.property('showForecast'):QMetaObject.invokeMethod(window.findChild(QObject,'sessionForecastMode'),'clicked')
                QTest.qWait(100);assert len(jobs)==1
                def evaluate(code):
                    expression=QQmlExpression(QQmlEngine.contextForObject(screen),screen,code);value=expression.evaluate()[0]
                    assert not expression.hasError(),expression.error().toString()
                    return value
                flick=window.findChild(QObject,'sessionForecastScroll').property('contentItem')
                def visual(item,name):
                    if item.objectName()==name:return item
                    for child in item.childItems():
                        found=visual(child,name)
                        if found is not None:return found
                    return None
                section=visual(screen,'sessionForecastSection-current')
                assert section
                flick.setProperty('contentY',flick.property('contentY')+section.mapToItem(flick,0,0).y()+60)
                QTest.qWait(60)
                before=section.mapToItem(flick,0,0).y()
                assert abs(before+60)<1
                jobs.pop(0)();QTest.qWait(400)
                after=section.mapToItem(flick,0,0).y()
                assert abs(after-before)<1,(width,language,'arrival',before,after)
                assert evaluate('forecastReading === null')
                capture('forecast-reading-late-image-same-section-pixel-'+language)
                owner.changed.emit();QTest.qWait(160)
                section=visual(screen,'sessionForecastSection-current')
                assert abs(section.mapToItem(flick,0,0).y()-before)<1,(width,language,'unchanged-refresh')
                elapsed[0]=31
                QMetaObject.invokeMethod(images.deadline_timer,'timeout');QTest.qWait(400)
                after=section.mapToItem(flick,0,0).y()
                assert abs(after-before)<1,(width,language,'expiry',before,after)
                assert not owner.forecastImage and len(owner.state['forecast']['sections'])==3
                capture('forecast-reading-expired-image-same-section-pixel-'+language)
                # Hold a real touch drag while a fresh explicitly synthetic image arrives.
                f['revision']+=1;f['imagery'][0]['url']=original_path.rsplit('/',1)[0]+'/'+'s'*32
                f['imagery'][0]['expires_at']=datetime.fromtimestamp(stamp+90,UTC).isoformat()
                owner._forecast.receive(session,owner._caps,owner._clock.now());owner.changed.emit();QTest.qWait(100)
                assert len(jobs)==1
                touch=QTest.touchEvent(window,touch_device,False)
                touch.press(0,QPoint(width//2,350),window).commit();QTest.qWait(80)
                touch.move(0,QPoint(width//2,410),window).commit();QTest.qWait(40)
                touch.move(0,QPoint(width//2,470),window).commit();QTest.qWait(40)
                assert flick.property('dragging')
                jobs.pop(0)();QTest.qWait(80)
                assert evaluate('forecastReading === null') and not window.findChild(QObject,'sessionForecastReadingRestore').property('running')
                touch.release(0,QPoint(width//2,470),window).commit();QTest.qWait(400)
                assert evaluate('forecastReading === null') and not window.findChild(QObject,'sessionForecastReadingRestore').property('running')
                capture('forecast-reading-actual-touch-cancels-follow-'+language)
                # A second real drag begins after image publication queued a layout restore.
                QMetaObject.invokeMethod(flick,'cancelFlick');QTest.qWait(60)
                f['revision']+=1;f['imagery'][0]['url']=original_path.rsplit('/',1)[0]+'/'+'t'*32
                owner._forecast.receive(session,owner._caps,owner._clock.now());owner.changed.emit();QTest.qWait(400)
                assert len(jobs)==1
                section=visual(screen,'sessionForecastSection-current')
                flick.setProperty('contentY',flick.property('contentY')+section.mapToItem(flick,0,0).y()+60)
                touch=QTest.touchEvent(window,touch_device,False)
                touch.press(0,QPoint(width//2,350),window).commit();QTest.qWait(80)
                assert not flick.property('dragging')
                restore_timer=window.findChild(QObject,'sessionForecastReadingRestore')
                restore_timer.setProperty('interval',500)  # Fixture holds layout callback while real touch begins.
                jobs.pop(0)()
                assert evaluate('forecastReading !== null')
                touch.move(0,QPoint(width//2,410),window).commit();QTest.qWait(80)
                touch.move(0,QPoint(width//2,470),window).commit();QTest.qWait(50)
                assert flick.property('dragging')
                assert evaluate('forecastReading === null') and not window.findChild(QObject,'sessionForecastReadingRestore').property('running')
                touch.release(0,QPoint(width//2,470),window).commit();QTest.qWait(400)
                assert evaluate('forecastReading === null')
                restore_timer.setProperty('interval',32)
                QMetaObject.invokeMethod(flick,'cancelFlick');QTest.qWait(60)
                flick.setProperty('contentY',200);position=flick.property('contentY')
                QMetaObject.invokeMethod(restore_timer,'triggered');QTest.qWait(60)
                assert abs(flick.property('contentY')-position)<1
                capture('forecast-reading-queued-restore-real-touch-cancel-'+language)
            backend.shutdown();delete(window);delete(engine)
    errors=[m for m in warnings if any(w in m for w in ['ReferenceError','TypeError','Error:','Cannot assign','is not a type','failed to load','Binding loop detected'])]
    (output/'readback.json').write_text(json.dumps({'captures':captures,'qml_errors':errors,'synthetic_managed_byte_reads':len(calls),
        'proof':'Original protected expired Forecast metadata with explicit fixture Runtime envelope, synthetic timing/new-asset overlays and owned test PNG. Real bounded byte reader/QImageReader/QML; no network/provider/HA/ARM/install/physical proof.'},indent=2))
    assert not errors,errors
    print(f'{len(captures)} actual Forecast image QML views; no errors/binding loops; synthetic transport only')


if __name__=='__main__':main()
