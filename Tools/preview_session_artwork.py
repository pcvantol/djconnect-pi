"""Actual Qt Moment artwork; explicitly synthetic native/media joins, no network."""
from __future__ import annotations
import argparse
from copy import deepcopy
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QMetaObject, QObject, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_history_view import live_presentations
from djconnect_pi.session_transport import SessionError

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
        assert self.trust_env is False and url.startswith('http://fixture.invalid/api/djconnect/v1/session/media/image/')
        assert kwargs['allow_redirects'] is False and kwargs['timeout']==(4,4)
        assert kwargs['headers']['Authorization']=='Bearer synthetic-not-a-credential'
        assert kwargs['headers']['X-DJConnect-Profile-ID']=='profile-a'
        assert kwargs['headers']['X-DJConnect-Client-Type']=='raspberry_pi'
        assert kwargs['params']['profile_id']=='profile-a'
        self.calls.append(True)  # No path, identity or token diagnostics.
        return Response(self.body)


def main():
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('--output',type=Path,required=True)
    output=parser.parse_args().output;output.mkdir(parents=True,exist_ok=True)
    warnings=[];qInstallMessageHandler(lambda kind,context,message:warnings.append(message))
    QQuickStyle.setStyle('Basic');app=QGuiApplication([]);apply_palette(app);captures=[];calls=[]
    helper=runpy.run_path(str(ROOT/'tests/test_session_artwork.py'));make_frame=helper['frame'];pixels=helper['PIXELS']
    with patch('djconnect_pi.session_artwork.requests.Session',side_effect=lambda:Client(pixels,calls)):
        for width,height,profile in [(720,720,'pi-zero-2w-arm64'),(1200,1920,'pi5-arm64')]:
            config=output/f'fixture-{width}.json';save_config(config,Config(language='nl',release_profile=profile,log_file=str(output/'fixture.log'),paired=True,
                device_token='synthetic-not-a-credential',device_id='djconnect-raspberry-pi-fixture',ha_url='http://fixture.invalid',
                active_profile_id='profile-a',explicit_profile_id='profile-a',active_profile_type='personal',active_profile_privacy_mode='private',screen_timeout_seconds=0))
            with patch.object(QTimer,'singleShot'):backend=DJConnectBackend(config)
            for timer in backend.findChildren(QTimer):timer.stop()
            backend._executor.submit=Mock();control=[];backend._session_executor.submit=control.append;backend._question_executor.submit=Mock()
            owner=backend.djSession;owner._artwork_prepare.executor=SimpleNamespace(submit=control.append,shutdown=lambda **kw:None);store=owner._moment_images;jobs=[];store.executor=SimpleNamespace(submit=jobs.append,shutdown=lambda **kw:None)
            owner.transport.active=Mock(return_value={'success':True,'session':None});owner.transport.capabilities=Mock(return_value={})
            engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('djconnect',backend);engine.rootContext().setContextProperty('startWindowed',True)
            engine.load(str(ROOT/'src/djconnect_pi/qml/Main.qml'));assert engine.rootObjects(),warnings
            window=engine.rootObjects()[0];window.setWidth(width);window.setHeight(height);window.setProperty('splashVisible',False)
            for obj in window.findChildren(QObject):
                if 'Timer' in obj.metaObject().className() and obj.property('interval') in (3000,15000):
                    e=QQmlExpression(engine.rootContext(),obj,'running=false');e.evaluate();assert not e.hasError()
            screen=window.findChild(QObject,'djSessionScreen');flick=window.findChild(QObject,'sessionHistoryScroll').property('contentItem')
            def visual(item,name):
                if item.objectName()==name:return item
                for child in item.childItems():
                    found=visual(child,name)
                    if found is not None:return found
                return None
            def drain():
                for _ in range(4):
                    QTest.qWait(40)
                    if control:control.pop(0)()
                assert not control
            def capture(name):
                QTest.qWait(100);target=output/f'{name}-{width}x{height}.png';assert window.grabWindow().save(str(target));captures.append(target.name)
            def install(lang,kind='artist_story', mutate=None):
                if not owner._foreground:owner.setForeground(True)
                drain();owner.invalidate();backend.setLanguage(lang);backend._toast_visible=False;backend.toastChanged.emit();drain()
                s,c,_,stamp=make_frame(lang,kind)
                if mutate:mutate(s)
                wall=[stamp];elapsed=[0.0];owner._clock=ExpiryClock(lambda:wall[0],lambda:elapsed[0])
                owner._session=s;owner._caps=c;owner._moments=live_presentations(s,now=stamp);owner._loaded=True
                owner.transport.active=Mock(return_value={'success':True,'session':deepcopy(s)});owner.transport.capabilities=Mock(return_value=c)
                owner.changed.emit();window.setProperty('activeScreen','session');drain();QTest.qWait(100)
                return s,elapsed
            for language in ['en','nl','de','fr','es']:
                s,elapsed=install(language);assert len(jobs)==1, (len(jobs), store.visible, owner._foreground, bool(owner._session), owner._caps, backend.cfg.explicit_profile_id, backend.cfg.active_profile_type, backend.cfg.active_profile_privacy_mode, bool(store.desired),screen.property('historical'),screen.property('showForecast'))
                jobs.pop(0)();QTest.qWait(150)
                art=visual(screen,'sessionMomentArtworkImage');card=visual(screen,'sessionMomentArtworkCard')
                assert owner.momentArtwork and card.property('visible') and art.property('source').toString().startswith('data:image/png;base64,')
                assert art.property('cache') is False and QQmlExpression(engine.rootContext(),art,'status===1 && fillMode===1').evaluate()[0]
                flick.setProperty('contentY',max(0,min(flick.property('contentY')+art.mapToItem(flick,0,0).y()-12,flick.property('contentHeight')-flick.property('height'))))
                capture('moment-artist-synthetic-current-grant-'+language)
                # Image expires before the independent original native text deadline.
                elapsed[0]=.6;QMetaObject.invokeMethod(store.deadline_timer,'timeout');QTest.qWait(100)
                assert not owner.momentArtwork and not art.property('source').toString() and owner.state['moments']
                capture('moment-art-expired-text-kept-'+language)
                # Explicit synthetic long native prose for layout only, no narration claim.
                def long_prose(snapshot):
                    row=snapshot['broadcast']['dj_moments'][0]
                    row['content']=(row['content'][:12]+'\n')*200
                    row['content']=row['content'][:3000]
                s,elapsed=install(language,mutate=long_prose);assert len(jobs)==1
                body=visual(screen,'sessionLiveMomentBody');assert body and body.property('height')>flick.property('height')
                flick.setProperty('contentY',flick.property('contentY')+body.mapToItem(flick,0,0).y()+35)
                QTest.qWait(60);before=body.mapToItem(flick,0,0).y();assert before<0
                jobs.pop(0)();QTest.qWait(180)
                body=visual(screen,'sessionLiveMomentBody')
                assert abs(body.mapToItem(flick,0,0).y()-before)<3, (width,language,before,body.mapToItem(flick,0,0).y())
                art=visual(screen,'sessionMomentArtworkImage');assert art.property('width')<=100 and art.property('height')<=100
                capture('moment-late-art-preserves-body-pixel-'+language)
                elapsed[0]=.6;QMetaObject.invokeMethod(store.deadline_timer,'timeout');QTest.qWait(180)
                body=visual(screen,'sessionLiveMomentBody')
                assert abs(body.mapToItem(flick,0,0).y()-before)<3, (width,language,before,body.mapToItem(flick,0,0).y(),(screen.property('flowReturn').toVariant() if screen.property('flowReturn') is not None else None))
                capture('moment-art-expiry-preserves-body-pixel-'+language)
                QMetaObject.invokeMethod(screen,'clearFlowReturn');position=flick.property('contentY')
                QMetaObject.invokeMethod(window.findChild(QObject,'sessionArtworkReadingRestore'),'timeout')
                QTest.qWait(40);assert abs(flick.property('contentY')-position)<.1
                capture('moment-cleared-reading-late-callback-no-jump-'+language)
                s,elapsed=install(language,'album_story');assert len(jobs)==1;jobs.pop(0)();QTest.qWait(150)
                art=visual(screen,'sessionMomentArtworkImage');assert owner.momentArtwork
                flick.setProperty('contentY',max(0,min(flick.property('contentY')+art.mapToItem(flick,0,0).y()-12,flick.property('contentHeight')-flick.property('height'))))
                capture('moment-album-current-grant-'+language)
                QMetaObject.invokeMethod(screen,'rememberFlow');saved=screen.property('flowReturn').toVariant();assert saved
                window.setProperty('activeScreen','session-history');QTest.qWait(120)
                assert not owner.momentArtwork and screen.property('flowReturn').toVariant()==saved
                capture('moment-art-history-hidden-descriptor-kept-'+language)
                window.setProperty('activeScreen','session');QTest.qWait(150);assert len(jobs)==1;jobs.pop(0)();QTest.qWait(120)
                assert owner.momentArtwork
                capture('moment-art-fresh-flow-return-'+language)
                before=len(calls)
                s,elapsed=install(language,mutate=lambda s:s['broadcast']['session_media'][0]['artwork'].update(current_display_allowed=False))
                assert not jobs and not owner.momentArtwork and len(calls)==before and owner.state['moments']
                capture('moment-original-flow-only-media-refused-'+language)
                s,elapsed=install(language,mutate=lambda s:s['broadcast']['session_media'][0]['artwork'].update(url='/api/djconnect/v1/session/forecast/art/s/a'))
                assert not jobs and not owner.momentArtwork and len(calls)==before
                capture('moment-wrong-route-no-credential-fallback-'+language)
                s,elapsed=install(language);assert len(jobs)==1
                screen.setProperty('followQuestionReply',True);jobs.pop(0)();QTest.qWait(100)
                assert screen.property('followQuestionReply')
                capture('moment-art-keeps-explicit-user-follow-state-'+language)
                screen.setProperty('followQuestionReply',False)
                # Explicit preparation has no effect until actual user click.
                s,elapsed=install(language,mutate=lambda x:x['broadcast'].update(session_media=[]))
                fresh=make_frame(language)[0]
                owner.transport.prepare_artwork=Mock(return_value={'success':True,'contract_version':1,'session_media':deepcopy(fresh['broadcast']['session_media'])})
                owner.transport.active=Mock(return_value={'success':True,'session':fresh})
                button=visual(screen,'sessionPrepareArtwork');assert button.property('visible') and button.property('enabled')
                owner.transport.prepare_artwork.assert_not_called()
                QMetaObject.invokeMethod(button,'clicked');QTest.qWait(40)
                assert owner._artwork_prepare.running and owner.busy and not button.property('enabled')
                capture('moment-explicit-prepare-pending-'+language)
                drain();assert len(jobs)==1;jobs.pop(0)();QTest.qWait(100)
                owner.transport.prepare_artwork.assert_called_once()
                assert owner.momentArtwork and not owner.busy
                capture('moment-explicit-prepare-fresh-owner-ready-'+language)
                s,elapsed=install(language,mutate=lambda x:x['broadcast'].update(session_media=[]))
                owner.transport.prepare_artwork=Mock(side_effect=SessionError('uncertain'))
                button=visual(screen,'sessionPrepareArtwork');QMetaObject.invokeMethod(button,'clicked');drain()
                assert visual(screen,'sessionPrepareArtworkStatus').property('visible') and owner.state['moments'] and not owner.momentArtwork
                owner.transport.prepare_artwork.assert_called_once()
                capture('moment-explicit-prepare-uncertain-no-replay-'+language)
                s,elapsed=install(language,mutate=lambda x:x['broadcast'].update(session_media=[]))
                fresh=make_frame(language)[0];fresh['broadcast']['session_media'][0]['artwork']['current_display_allowed']=False
                owner.transport.prepare_artwork=Mock(return_value={'success':True,'contract_version':1,'session_media':deepcopy(fresh['broadcast']['session_media'])})
                owner.transport.active=Mock(return_value={'success':True,'session':fresh})
                button=visual(screen,'sessionPrepareArtwork');QMetaObject.invokeMethod(button,'clicked');drain()
                assert not jobs and not owner.momentArtwork and owner.state['artwork_prepare']['status']=='unavailable' and owner.state['moments']
                capture('moment-explicit-prepare-flow-only-refused-'+language)
                s,elapsed=install(language);assert len(jobs)==1;late=jobs.pop(0);before=len(calls)
                owner.setForeground(False);late();QTest.qWait(100)
                assert not owner.momentArtwork and len(calls)==before
                capture('moment-art-background-before-paired-read-'+language)
                s,elapsed=install(language);assert len(jobs)==1;late=jobs.pop(0);before=len(calls)
                owner.transport.end=Mock(return_value={'success':True,'session':{**s,'runtime_state':'ending'}})
                owner.transport.active=Mock(return_value={'success':True,'session':None})
                owner.end(s['session_id']);late();drain();QTest.qWait(100)
                assert not owner.momentArtwork and len(calls)==before
                capture('moment-art-End-before-paired-read-'+language)
            backend.shutdown();delete(window);delete(engine)
    errors=[m for m in warnings if any(w in m for w in ['ReferenceError','TypeError','Error:','Cannot assign','is not a type','failed to load','Binding loop detected'])]
    (output/'readback.json').write_text(json.dumps({'captures':captures,'qml_errors':errors,'synthetic_paired_byte_reads':len(calls),
        'proof':'Original protected native/media fixtures joined with explicitly synthetic IDs/clocks/current-artist flag; owned synthetic PNG. Original flow-only artist is refused. Real paired byte validation/Qt decode/QML; no network/provider/HA/ARM/install/physical proof. User-follow flag probe is synthetic view state; existing composer harness independently covers actual submit.'},indent=2))
    assert not errors,errors
    print(f'{len(captures)} actual Moment artwork QML views; no errors/binding loops; synthetic paired transport only')

if __name__=='__main__':main()
