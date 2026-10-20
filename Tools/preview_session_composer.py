"""Actual shared QML/controller with synthetic transport; never contact HA/model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_projection import timestamp

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    warnings = []
    qInstallMessageHandler(lambda kind, context, message: warnings.append(message))
    QQuickStyle.setStyle('Basic')
    app = QGuiApplication([])
    touch_device = QTest.createTouchDevice()
    apply_palette(app)
    captures = []
    for width, height, profile in [(720, 720, 'pi-zero-2w-arm64'), (1200, 1920, 'pi5-arm64')]:
        config = output / f'fixture-{width}.json'
        save_config(config, Config(language='nl', release_profile=profile, log_file=str(output/'fixture.log'),
            paired=True, device_token='synthetic-not-a-credential', device_id='djconnect-raspberry-pi-fixture',
            ha_url='http://fixture.invalid', active_profile_id='profile-fixture', explicit_profile_id='profile-fixture',
            active_profile_type='personal', active_profile_privacy_mode='private', screen_timeout_seconds=0))
        with patch.object(QTimer, 'singleShot'):
            backend = DJConnectBackend(config)
        for timer in backend.findChildren(QTimer):
            timer.stop()
        backend._executor.submit = Mock()
        backend._session_executor.submit = backend._executor.submit
        backend._question_executor.submit = backend._executor.submit
        owner = backend.djSession
        caps = {'capabilities': {'session_conversation_history':True, 'ask_dj_contextual_dialogue':True},
            'contract_versions': {'session_history_entries':2,'ask_dj_contextual_dialogue':1}}
        session = {'session_id':'synthetic-active-session','runtime_state':'active', 'selected_mood':'groove',
            'broadcast': {'session': {'session_id':'synthetic-active-session'}}}
        page = {'success':True,'schema_version':2,'history_contract_version':2,
            'session':{'session_id':session['session_id'],'revision':'fixture-history-revision'},
            'revision':'fixture-history-revision','next_cursor':None,'entries':[]}
        prior_entries=[]
        def answer(binding, value):
            turn_id=f"fixture-turn-{owner.transport.question.call_count}"
            context = {'session_id':value['session_id']}
            selected = value.get('selected') or {}
            if selected:
                context[selected['kind']] = {k:v for k,v in selected.items() if k!='kind'}
            page['entries'] = prior_entries + [{'entry_id':f'{turn_id}-entry-{i}','session_id':session['session_id'],
                'kind':'conversation_user' if i==0 else 'conversation_dj', 'order':len(prior_entries)+i+1,
                'occurred_at':'2026-10-20T00:00:00Z','retained_until':'9999-01-01T00:00:00Z',
                'historical_view_only':True,'current_display_allowed':False,
                'turn_id':turn_id,'input_type':'text','role':'user' if i==0 else 'assistant','client_message_id':value['client_message_id'],
                'text': value['text'] if i==0 else 'Synthetic answer read back from the server history.'}
                for i in range(2)]
            return {'success':True,'owner_profile_id':binding.resolved_profile_id,
                'client_message_id':value['client_message_id'],
                'conversation':{'schema_version':1,'turn_id':turn_id,'input_type':'text','context':context,
                    'entry_ids':[row['entry_id'] for row in page['entries'][-2:]]}}
        owner.transport.active = Mock(return_value={'success':True,'session':session})
        owner.transport.capabilities = Mock(return_value=caps)
        owner.transport.timeline = Mock(return_value=page)
        owner.transport.question = Mock(side_effect=answer)
        owner._session = session
        owner._caps = caps
        owner._loaded = True
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty('djconnect',backend)
        engine.rootContext().setContextProperty('startWindowed',True)
        engine.load(str(ROOT/'src/djconnect_pi/qml/Main.qml'))
        assert engine.rootObjects(),warnings
        window=engine.rootObjects()[0]
        window.setWidth(width); window.setHeight(height)
        window.setProperty('splashVisible',False)
        window.setProperty('activeScreen','session')
        owner.changed.emit()
        def capture(name):
            QTest.qWait(200)
            target=output/f'{name}-{width}x{height}.png'
            assert window.grabWindow().save(str(target))
            captures.append(target.name)
        capture('composer-dock')
        panel=window.findChild(QObject,'sessionComposerPanel')
        field=window.findChild(QObject,'sessionComposerInput')
        keyboard=window.findChild(QObject,'sessionComposerKeyboard')
        screen=window.findChild(QObject,'djSessionScreen')
        assert panel and field and keyboard and screen
        for locale in ('en','nl','de','fr','es'):
            backend.setLanguage(locale); backend._toast_visible=False;backend.toastChanged.emit()
            QMetaObject.invokeMethod(panel,'open')
            capture('composer-'+locale)
            QMetaObject.invokeMethod(panel,'close')
        backend.setLanguage('nl');backend._toast_visible=False;backend.toastChanged.emit()
        # Finish any timer read as a mocked read, then explicitly submit once through QML.
        if owner.busy:
            backend._executor.submit.call_args.args[0]()
        QMetaObject.invokeMethod(panel,'open')
        QMetaObject.invokeMethod(keyboard,'insertKey',Q_ARG('QVariant','Vertel over deze muziek é'))
        assert field.property('text') == 'Vertel over deze muziek é'
        QMetaObject.invokeMethod(screen,'submitQuestion')
        assert field.property('text') == ''
        worker=backend._executor.submit.call_args.args[0]
        worker()
        assert owner.transport.question.call_count==1
        assert len(owner.state['conversation'])==2 and owner.state['question_status']=='accepted'
        capture('composer-confirmed-history')
        owner._timeline=page
        owner.selectEntry(session['session_id'],page['entries'][0]['entry_id'])
        QMetaObject.invokeMethod(panel,'open')
        capture('composer-selected-entry')
        QMetaObject.invokeMethod(keyboard,'insertKey',Q_ARG('QVariant','Privé concept'))
        owner._timeline['entries'][0]['retained_until']='2000-01-01T00:00:00Z'
        owner._expire()
        assert field.property('text')=='' and not panel.property('opened')
        capture('composer-selection-withdrawn')
        QMetaObject.invokeMethod(panel,'open')
        QMetaObject.invokeMethod(keyboard,'insertKey',Q_ARG('QVariant','Privé concept'))
        owner.invalidate()
        assert field.property('text')=='' and not panel.property('opened')
        capture('composer-context-cleared')
        # Long retained conversation: exact post/refresh reconciliation focuses only this reply.
        prior_entries.extend([{'entry_id':f'older-entry-{i}','session_id':session['session_id'],
            'kind':'conversation_user' if i%2==0 else 'conversation_dj','order':i+1,
            'occurred_at':'2026-10-20T00:00:00Z','retained_until':'9999-01-01T00:00:00Z',
            'historical_view_only':True,'current_display_allowed':False,'input_type':'text',
            'turn_id':f'older-turn-{i//2}','role':'user' if i%2==0 else 'assistant',
            'client_message_id':f'older-client-{i//2}','text':'Earlier retained conversation. '*10}
            for i in range(24)])
        page['entries']=list(prior_entries)
        owner._session=session;owner._caps=caps;owner._loaded=True;owner.changed.emit()
        if owner.busy:
            backend._executor.submit.call_args.args[0]()
        owner.refresh();backend._executor.submit.call_args.args[0]()
        QTest.qWait(80)
        flick=window.findChild(QObject,'sessionHistoryScroll').property('contentItem')
        flick.setProperty('contentY',0)
        field.setProperty('text','Een nieuwe vraag na oudere gesprekken')
        QMetaObject.invokeMethod(screen,'submitQuestion')
        reply_worker=backend._executor.submit.call_args.args[0]
        owner.refresh();backend._executor.submit.call_args.args[0]()
        reply_worker()
        assert owner.state['question_status']=='accepted_unavailable'
        backend._executor.submit.call_args.args[0]()
        assert owner.state['question_status']=='accepted'
        capture('composer-reconciled-reply-focused')
        assert flick.property('contentY') > 100
        assert not screen.property('followQuestionReply')
        flick.setProperty('contentY',100)
        owner.refresh();backend._executor.submit.call_args.args[0]()
        capture('composer-refresh-reading-position-preserved')
        assert abs(flick.property('contentY')-100)<1
        if owner.busy:
            backend._executor.submit.call_args.args[0]()
        field.setProperty('text','Nog een bewuste vraag')
        QMetaObject.invokeMethod(screen,'submitQuestion')
        held_reply=backend._executor.submit.call_args.args[0]
        assert screen.property('followQuestionReply')
        touch=QTest.touchEvent(window,touch_device,False)
        touch.press(0,QPoint(width//2,260),window).commit()
        QTest.qWait(80)
        touch.move(0,QPoint(width//2,310),window).commit()
        QTest.qWait(50)
        touch.move(0,QPoint(width//2,370),window).commit()
        QTest.qWait(50)
        assert not screen.property('followQuestionReply'), 'User drag cancels automatic reply focus'
        touch.release(0,QPoint(width//2,370),window).commit()
        QTest.qWait(400)
        held_reply()
        capture('composer-user-drag-preserves-older-reading')
        assert flick.property('contentY') < 200
        prior_entries.clear();page['entries']=[];owner.invalidate()
        # Keep a synthetic POST pending while real QML exposes refresh and End.
        owner._session=session;owner._caps=caps;owner._loaded=True;owner.changed.emit()
        if owner.busy:
            backend._executor.submit.call_args.args[0]()
        prior_question_count=owner.transport.question.call_count
        assert owner.sendQuestion('Pending synthetic question')
        pending_question=backend._executor.submit.call_args.args[0]
        end_button=window.findChild(QObject,'sessionCompactEnd' if width < 900 else 'sessionExpandedEnd')
        refresh_button=window.findChild(QObject,'sessionRefresh')
        assert owner.questionBusy and not owner.busy
        assert end_button.property('enabled') and refresh_button.property('enabled')
        capture('composer-pending-controls-available')
        owner.refresh()
        pending_read=backend._executor.submit.call_args.args[0]
        assert end_button.property('enabled')
        capture('composer-pending-read-end-available')
        owner.transport.end=Mock()
        owner.end(session['session_id'])
        end_worker=backend._executor.submit.call_args.args[0]
        owner.transport.active.return_value={'success':True,'session':None}
        end_worker();pending_read();pending_question()
        assert not owner.state['session_id'] and not owner.state['conversation'] and not owner.questionBusy
        owner.transport.end.assert_called_once()
        assert owner.transport.question.call_count==prior_question_count  # revoked before dispatch
        capture('composer-ended-late-answer-withdrawn')
        # Original published native grant, same UI/caps; no metadata or deadline rewrite.
        frames=json.loads((ROOT/'tests/fixtures/session_core/native-expressive-snapshots.json').read_text())
        snapshot=frames['formation']['nl']['home_dj'][-1]
        current=next(row for row in snapshot['native_delivery']['admissions'] if row['moment_id']==snapshot['native_delivery']['current_moment_id'])
        stamp=timestamp(current['display_expires_at'])-1
        owner._clock=ExpiryClock(lambda:stamp,lambda:0)
        owner._session={**snapshot['session'],'broadcast':snapshot}
        owner._caps=caps;owner._loaded=True;owner._question_status=''
        owner._expire();owner.changed.emit()
        assert owner.selectMoment(snapshot['session']['session_id'],current['moment_id'])
        capture('composer-native-moment-reference')
        QMetaObject.invokeMethod(panel,'open')
        capture('composer-selected-moment')
        backend.shutdown()
        delete(window);delete(engine)
    errors=[value for value in warnings if any(word in value for word in ('ReferenceError','TypeError','Error:','Cannot assign','is not a type','failed to load'))]
    (output/'readback.json').write_text(json.dumps({'captures':captures,'qml_errors':errors,
        'proof':'Synthetic transport -> real controller -> actual QML; not HA/model/ARM/installed/physical acceptance'},indent=2))
    assert not errors,errors
    print(f'{len(captures)} composer views, explicit QML send and context clearing; no QML errors')


if __name__=='__main__':
    main()
