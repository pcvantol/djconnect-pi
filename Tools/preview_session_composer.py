"""Actual shared QML/controller with synthetic transport; never contact HA/model."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, QObject, QPoint, QTimer, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.session_projection import timestamp
from djconnect_pi.session_transport import SessionError

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
        owner.transport.history = Mock(return_value={'success':True,'schema_version':2,'history_contract_version':2,'sessions':[],'next_cursor':None})
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
        # Keep fixture reads explicit; wall-clock polling would race language/scope probes.
        for obj in window.findChildren(QObject):
            if 'Timer' in obj.metaObject().className() and obj.property('interval') in (3000,15000):
                QMetaObject.invokeMethod(obj,'stop')
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
        def complete_navigation():
            executed=set()
            for _ in range(3):
                QTest.qWait(80)
                if owner.busy:
                    job=backend._executor.submit.call_args.args[0]
                    assert job not in executed
                    executed.add(job);job()
                QTest.qWait(50)
                if not owner.busy and not screen.property('historyReadPending'): return
            raise AssertionError('bounded synthetic navigation did not settle')
        assert panel and field and keyboard and screen
        mood_button=window.findChild(QObject,'sessionToolbarMood')
        presence_button=window.findChild(QObject,'sessionToolbarPresence')
        persona_button=window.findChild(QObject,'sessionToolbarPersona')
        voice_button=window.findChild(QObject,'sessionToolbarVoice')
        more_button=window.findChild(QObject,'sessionToolbarMore')
        assert presence_button.property('visible') and persona_button.property('visible')
        assert voice_button.property('visible') == (width>=900)
        assert more_button.property('visible') == (width<900)
        shared={'available':True,'selection_required':False,'operation_pending':False,
            'edit_token':'synthetic-ui-token','values':{'mood':'groove','presence':'balanced','persona':'home_dj'},
            'options':{'mood':['chill','groove','energy','party'],
                'presence':['music_only','occasional','balanced','talkative','presenter'],
                'persona':['home_dj','radio_dj','club_dj','festival_dj'],'voice':[]}}
        backend._shared_settings_state=shared
        backend.sharedSettingsChanged.emit()
        choice=window.findChild(QObject,'sessionToolbarChoice')
        for setting,button in [('mood',mood_button),('presence',presence_button),('persona',persona_button)]:
            for value in shared['options'][setting]:
                shared['values'][setting]=value
                shared['edit_token']='synthetic-'+setting+'-'+value
                backend.sharedSettingsChanged.emit()
                capture('toolbar-'+setting+'-'+value)
            QMetaObject.invokeMethod(button,'clicked')
            capture('toolbar-'+setting+'-popover')
            assert choice.property('opened') and choice.property('canSubmit')
            QMetaObject.invokeMethod(choice,'close')
        QTest.qWait(200)
        # A queued old click cannot write after Session/context or server edit-token replacement.
        QMetaObject.invokeMethod(mood_button,'clicked');QTest.qWait(180)
        def find_option(item):
            if item.objectName()=='sessionToolbarOption':
                return item
            for child in item.childItems():
                found=find_option(child)
                if found is not None:
                    return found
            return None
        option=find_option(choice.property('contentItem'))
        assert option and choice.property('canSubmit')
        before=backend._executor.submit.call_count
        owner._session={**session,'session_id':'replacement-ui-session'};owner.changed.emit();QTest.qWait(120)
        assert not choice.property('opened')
        QMetaObject.invokeMethod(option,'clicked')
        assert backend._executor.submit.call_count==before
        owner._session=session;owner.changed.emit()
        QMetaObject.invokeMethod(mood_button,'clicked');QTest.qWait(180)
        shared['edit_token']='new-synthetic-revision';backend.sharedSettingsChanged.emit();QTest.qWait(120)
        assert not choice.property('opened')
        before=backend._executor.submit.call_count
        QMetaObject.invokeMethod(option,'clicked')
        assert backend._executor.submit.call_count==before
        QMetaObject.invokeMethod(mood_button,'clicked');QTest.qWait(180)
        shared['operation_pending']=True;backend.sharedSettingsChanged.emit()
        assert not choice.property('canSubmit')
        before=backend._executor.submit.call_count
        QMetaObject.invokeMethod(option,'clicked')
        assert backend._executor.submit.call_count==before
        shared['operation_pending']=False;backend.sharedSettingsChanged.emit()
        owner._session={**session,'runtime_state':'ending'};owner.changed.emit()
        assert not choice.property('canSubmit')
        before=backend._executor.submit.call_count
        QMetaObject.invokeMethod(option,'clicked')
        assert backend._executor.submit.call_count==before
        QMetaObject.invokeMethod(choice,'close')
        owner._session=session;owner.changed.emit()
        backend._shared_settings_state={};backend.sharedSettingsChanged.emit()

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
        for _ in range(3):
            if owner.busy:
                backend._executor.submit.call_args.args[0]()
        history_button=window.findChild(QObject,'sessionReadCurrentHistory')
        assert history_button.property('enabled')
        flick.setProperty('contentY',420);QTest.qWait(80)
        QMetaObject.invokeMethod(history_button,'clicked')
        complete_navigation()
        assert window.property('activeScreen')=='session-history'
        assert owner.state['timeline']['session']['session_id']==session['session_id']
        capture('active-session-history-from-beginning')
        saved=screen.property('flowReturn').toVariant()
        assert saved and saved['kind']=='conversation' and set(saved)=={'session','profile','kind','id','offset'}
        back_to_flow=window.findChild(QObject,'sessionHistoryBack')
        QMetaObject.invokeMethod(back_to_flow,'clicked');QTest.qWait(100)
        assert window.property('activeScreen')=='session'
        QMetaObject.invokeMethod(screen,'rememberFlow')
        restored=screen.property('flowReturn').toVariant()
        assert restored['id']==saved['id'] and abs(restored['offset']-saved['offset'])<1,(width,saved,restored)
        capture('flow-return-same-entry-and-pixel')
        # Body withdrawal during history must not restore an absent entry or cache its prose.
        QMetaObject.invokeMethod(history_button,'clicked');complete_navigation()
        saved=screen.property('flowReturn').toVariant()
        kept=owner._conversation
        owner._conversation=[row for row in kept if row['entry_id']!=saved['id']];owner.changed.emit()
        QMetaObject.invokeMethod(back_to_flow,'clicked');QTest.qWait(100)
        assert abs(flick.property('contentY'))<1
        capture('flow-return-withdrawn-entry-top')
        owner._conversation=kept;owner.changed.emit();QTest.qWait(80)
        flick.setProperty('contentY',420)
        QMetaObject.invokeMethod(history_button,'clicked');complete_navigation()
        assert screen.property('flowReturn').toVariant()
        # Scrolling history must keep the independent Flow reading identity.
        history_saved=screen.property('flowReturn').toVariant()
        touch=QTest.touchEvent(window,touch_device,False)
        touch.press(0,QPoint(width//2,260),window).commit();QTest.qWait(80)
        touch.move(0,QPoint(width//2,360),window).commit();QTest.qWait(80)
        touch.release(0,QPoint(width//2,360),window).commit();QTest.qWait(400)
        assert screen.property('flowReturn').toVariant()==history_saved
        QMetaObject.invokeMethod(back_to_flow,'clicked');QTest.qWait(100)
        QMetaObject.invokeMethod(screen,'rememberFlow')
        after_history_drag=screen.property('flowReturn').toVariant()
        assert after_history_drag['id']==history_saved['id'] and abs(after_history_drag['offset']-history_saved['offset'])<1
        capture('flow-return-after-history-touch-scroll')
        QMetaObject.invokeMethod(history_button,'clicked');complete_navigation()
        # Real shared QML previous-page control, re-reading canonical rows rather than cached prose.
        first_page={**page,'entries':list(prior_entries[:2]),'next_cursor':'preview-next'}
        second_page={**page,'entries':list(prior_entries[2:4]),'next_cursor':None}
        def paged_history(binding,sid,**kwargs):
            return second_page if kwargs.get('cursor')=='preview-next' else first_page
        owner.transport.timeline.side_effect=paged_history
        for _ in range(3):
            if owner.busy:
                backend._executor.submit.call_args.args[0]()
        owner.firstEntries();backend._executor.submit.call_args.args[0]()
        owner.nextEntries();backend._executor.submit.call_args.args[0]()
        assert owner.state['has_previous_entries']
        for locale in ('en','nl','de','fr','es'):
            backend.setLanguage(locale);backend._toast_visible=False;backend.toastChanged.emit()
            QTest.qWait(80)
            flick.setProperty('contentY',max(0,flick.property('contentHeight')-flick.property('height')))
            capture('history-previous-control-'+locale)
        backend.setLanguage('nl');backend._toast_visible=False;backend.toastChanged.emit()
        for _ in range(3):
            if owner.busy:
                backend._executor.submit.call_args.args[0]()
        previous_button=window.findChild(QObject,'sessionHistoryPrevious')
        assert previous_button.property('enabled') and previous_button.property('visible')
        QMetaObject.invokeMethod(previous_button,'clicked')
        backend._executor.submit.call_args.args[0]()
        assert not owner.state['has_previous_entries']
        assert owner.state['timeline']['entries'][0]['entry_id']==first_page['entries'][0]['entry_id']
        capture('history-previous-page-freshly-restored')
        # Keep only request/entry/offset metadata; the previous page is freshly read.
        first_page['entries']=list(prior_entries[:12])
        second_page['entries']=list(prior_entries[12:14])
        owner.firstEntries();backend._executor.submit.call_args.args[0]()
        QTest.qWait(100)
        flick.setProperty('contentY',min(180,max(0,flick.property('contentHeight')-flick.property('height'))))
        expected_anchor=QMetaObject.invokeMethod(screen,'readingAnchor',Q_RETURN_ARG('QVariant'))
        expected_offset=screen.property('readingOffset')
        assert expected_anchor and flick.property('contentY') > 100
        next_button=window.findChild(QObject,'sessionHistoryNext')
        QMetaObject.invokeMethod(next_button,'clicked');backend._executor.submit.call_args.args[0]()
        QTest.qWait(100)
        capture('history-reading-position-next-page')
        QMetaObject.invokeMethod(previous_button,'clicked');backend._executor.submit.call_args.args[0]()
        QTest.qWait(100)
        restored_anchor=QMetaObject.invokeMethod(screen,'readingAnchor',Q_RETURN_ARG('QVariant'))
        assert restored_anchor==expected_anchor,(width,restored_anchor,expected_anchor)
        assert abs(screen.property('readingOffset')-expected_offset)<1,(width,screen.property('readingOffset'),expected_offset)
        capture('history-previous-entry-pixel-restored')
        owner.transport.timeline.side_effect=None

        # Read-only anchor recovery for a receipt outside the fresh tail.
        owner.closeSaved();window.setProperty('activeScreen','session')
        prior_entries.clear();page['entries']=[];owner.invalidate()
        owner._session=session;owner._caps=caps;owner._loaded=True;owner.changed.emit()
        def anchor_history(binding,sid,**kwargs):
            result={**page,'session':dict(page['session']),'entries':list(page['entries'])}
            if kwargs.get('window')=='anchor':
                result.update(window='anchor',anchor_entry_id=kwargs['anchor_entry_id'],window_limit=20,
                    scanned_order_min=1,scanned_order_max=2,scan_complete=True,
                    coverage='bounded_saved_entry_window',next_cursor=None)
            else:
                result['entries']=[]
            return result
        owner.transport.timeline.side_effect=anchor_history
        if owner.busy:
            backend._executor.submit.call_args.args[0]()
        field.setProperty('text','Een antwoord buiten de nieuwste pagina')
        QMetaObject.invokeMethod(screen,'submitQuestion')
        backend._executor.submit.call_args.args[0]()
        assert owner.state['question_status']=='accepted' and len(owner.state['conversation'])==2
        assert owner._question_receipt.get('anchor_entry_id')
        capture('composer-exact-anchor-recovered-answer')
        owner.transport.timeline.side_effect=None
        page['entries']=[];owner.invalidate()

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
        assert not owner.state['pending_question']
        assert not window.findChild(QObject,'sessionPendingQuestion').property('visible')
        assert window.findChild(QObject,'sessionPendingQuestionText').property('text')==''
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
        QMetaObject.invokeMethod(panel,'close')
        window.setProperty('activeScreen','session')
        flick.setProperty('contentY',0)
        QTest.qWait(80)
        QMetaObject.invokeMethod(screen,'rememberFlow')
        native_reading=screen.property('flowReturn').toVariant()
        assert native_reading['kind']=='moment'
        assert native_reading['id'] in {row['moment_id'] for row in owner.state['moments']}
        capture('flow-reading-native-moment-identity')
        QMetaObject.invokeMethod(screen,'clearFlowReturn')
        # Selected live questions intentionally return no canonical history entries.
        # Reuse released response prose; only synthetic receipt/context identities adapt.
        original_question=owner.transport.question
        current_response=next(row['body'] for row in json.loads((ROOT/'tests/fixtures/session_core/contextual-dialogue-v1.json').read_text())['fixtures'] if row['case']=='active-credit')
        native_session=owner._session
        owner.transport.active=Mock(return_value={'success':True,'session':native_session})
        def current_answer(binding,request):
            reply=deepcopy(current_response)
            reply.update(owner_profile_id=binding.resolved_profile_id,client_message_id=request['client_message_id'])
            reply['conversation']['context']={'session_id':request['session_id'],'selected_moment':{key:value for key,value in request['selected'].items() if key!='kind'}}
            return reply
        owner.transport.question=Mock(side_effect=current_answer)
        for language in ['en','nl','de','fr','es']:
            complete_navigation()
            backend.setLanguage(language);backend._toast_visible=False;backend.toastChanged.emit()
            complete_navigation()
            assert owner.selectMoment(native_session['session_id'],current['moment_id'])
            field.setProperty('text','Synthetic <img> 🎧\nQuestion about selected live credit')
            QMetaObject.invokeMethod(screen,'submitQuestion')
            assert owner.questionBusy
            question_job=backend._executor.submit.call_args.args[0]
            QTest.qWait(60)
            assert window.findChild(QObject,'sessionPendingQuestion').property('visible')
            assert window.findChild(QObject,'sessionPendingQuestionText').property('text')==owner.state['pending_question']['text']
            assert QQmlExpression(engine.rootContext(),window.findChild(QObject,'sessionPendingQuestionText'),'textFormat === 0').evaluate()[0] is True
            assert not owner.state['current_reply']
            capture('current-question-pending-'+language)
            question_job();complete_navigation()
            assert not owner.state['pending_question']
            assert not window.findChild(QObject,'sessionPendingQuestion').property('visible')
            assert owner.state['current_reply']['text']==current_response['text']
            question_text=window.findChild(QObject,'sessionCurrentQuestionText')
            assert question_text.property('text')==owner.state['current_reply']['question_text']=='Synthetic <img> 🎧\nQuestion about selected live credit'
            assert QQmlExpression(engine.rootContext(),question_text,'textFormat === 0').evaluate()[0] is True  # Qt PlainText
            question_card=window.findChild(QObject,'sessionCurrentQuestion')
            assert question_card.property('width')<=window.findChild(QObject,'sessionCurrentReply').property('width')*0.85+1
            assert not owner._question_receipt
            capture('current-response-not-saved-'+language)
            assert window.findChild(QObject,'sessionCurrentReply').property('visible')
        # Current-only replies have no retained entry ID. Remember only their
        # receipt identity/position, and resolve against the still-live card.
        # Explicit synthetic long reply ensures a distinct visible reply on
        # tablet too; short content may legitimately leave a Moment visible first.
        current_response=deepcopy(current_response)
        current_response['text']=(current_response['text']+'\n')*40
        current_response['assistant_message']['text']=current_response['text']
        complete_navigation()
        assert owner.selectMoment(native_session['session_id'],current['moment_id'])
        field.setProperty('text','Synthetic long reading-position fixture')
        QMetaObject.invokeMethod(screen,'submitQuestion')
        assert owner.questionBusy
        backend._executor.submit.call_args.args[0]();complete_navigation()
        reply_card=window.findChild(QObject,'sessionCurrentReply')
        flick.setProperty('contentY',max(0,min(flick.property('contentY')+reply_card.mapToItem(flick,0,0).y()-12,flick.property('contentHeight')-flick.property('height'))))
        QTest.qWait(80)
        reply_y=reply_card.mapToItem(flick,0,0).y()
        QMetaObject.invokeMethod(screen,'rememberFlow')
        reply_reading=screen.property('flowReturn').toVariant()
        assert reply_reading['kind']=='current_reply' and reply_reading['id']==owner.state['current_reply']['reply_id']
        assert set(reply_reading)=={'session','profile','kind','id','offset'}
        window.setProperty('activeScreen','session-history');QTest.qWait(80)
        flick.setProperty('contentY',0)
        window.setProperty('activeScreen','session');QTest.qWait(120)
        assert abs(reply_card.mapToItem(flick,0,0).y()-reply_y)<2
        capture('current-reply-return-same-identity-and-pixel')
        QMetaObject.invokeMethod(screen,'rememberFlow')
        window.setProperty('activeScreen','session-history');QTest.qWait(80)
        # A withdrawn reply must not be restored from position metadata.
        owner._current_reply={};owner._current_reply_binding=None;owner.changed.emit()
        window.setProperty('activeScreen','session');QTest.qWait(120)
        assert not owner.state['current_reply'] and flick.property('contentY')<1
        assert not reply_card.property('visible')
        assert not window.findChild(QObject,'sessionCurrentQuestion').property('visible')
        assert window.findChild(QObject,'sessionCurrentQuestionText').property('text')==''
        capture('current-reply-return-withdrawn-top')
        owner.transport.question=original_question
        backend.setLanguage('nl');backend._toast_visible=False;backend.toastChanged.emit()
        playback_card=window.findChild(QObject,'sessionPlaybackMetadata')
        assert owner.state['playback']['title']==snapshot['playback']['title']
        assert owner.state['playback']['source_url']==snapshot['playback']['source_url']
        for language in ['en','nl','de','fr','es']:
            backend.setLanguage(language);backend._toast_visible=False;backend.toastChanged.emit()
            QTest.qWait(80)
            flick.setProperty('contentY',max(0,flick.property('contentHeight')-flick.property('height')))
            capture('session-playback-metadata-'+language)
            assert playback_card.property('visible')
        # Explicit synthetic output variant; the pinned producer bytes stay unchanged.
        owner._session={**owner._session,'broadcast':{**snapshot,'playback':{**snapshot['playback'],'target_name':'Synthetic output device','state':'paused','position_ms':150000}}}
        owner.changed.emit()
        capture('session-playback-synthetic-output-paused')
        owner._session={**owner._session,'runtime_state':'ending'};owner.changed.emit()
        QTest.qWait(80)
        assert not owner.state['playback'] and not playback_card.property('visible')
        capture('session-playback-ending-withdrawn')
        # Pure released ForecastProjection fixtures; no Runtime/model/provider calls.
        forecast_frames=json.loads((ROOT/'tests/fixtures/session_core/forecast-v1.json').read_text())
        forecast_caps={'capabilities':{'session_forecast':True},'contract_versions':{'session_forecast':1}}
        window.setProperty('activeScreen','session')
        for language in ['en','nl','de','fr','es']:
            frame=next(row for row in forecast_frames if row['locale']==language and row['persona']=='home_dj')
            p=frame['projection'];stamp=frame['now']
            owner._clock=ExpiryClock(lambda:stamp,lambda:0)
            backend.setLanguage(language);backend._toast_visible=False;backend.toastChanged.emit()
            owner._selection={}  # Match real controller withdrawal before fixture Session replacement.
            owner._session={'session_id':p['session_id'],'runtime_state':'active','broadcast':{
                'session':{'session_id':p['session_id']},'session_forecast':p,'playback':{
                    'state':'playing','item_id':p['current_anchor']['item_id'],'title':'Observed track',
                    'source_url':p['current_anchor']['source_url'],'updated_at':p['issued_at']}}}
            owner._caps={**caps,'capabilities':{**caps['capabilities'],**forecast_caps['capabilities']},
                'contract_versions':{**caps['contract_versions'],**forecast_caps['contract_versions']}}
            owner._moments=[];owner._conversation=[];owner._loaded=True
            owner._forecast.reset();owner._forecast.receive(owner._session,owner._caps,stamp);owner.changed.emit()
            field.setProperty('text','Synthetic unsent draft')
            forecast_button=window.findChild(QObject,'sessionForecastMode')
            assert forecast_button.property('visible')
            QTest.qWait(80)
            flick.setProperty('contentY',min(90,max(0,flick.property('contentHeight')-flick.property('height'))))
            flow_position=flick.property('contentY')
            if width < 900: assert flow_position > 50
            QMetaObject.invokeMethod(forecast_button,'clicked')
            capture('session-forecast-'+language)
            assert screen.property('showForecast') and screen.property('draft')=='Synthetic unsent draft'
            QMetaObject.invokeMethod(window.findChild(QObject,'sessionFlowMode'),'clicked')
            assert not screen.property('showForecast') and screen.property('draft')=='Synthetic unsent draft'
            QTest.qWait(80)
            assert abs(flick.property('contentY')-flow_position)<1
            assert field.property('text')=='Synthetic unsent draft'
        QMetaObject.invokeMethod(forecast_button,'clicked')
        owner._clock=ExpiryClock(lambda:stamp+120,lambda:0)
        assert not owner.state['forecast']['sections']
        owner._expire()
        assert not owner.state['forecast']['sections']
        capture('session-forecast-expired')
        owner.invalidate()
        assert not owner.state['forecast']['sections']
        # Explicit synthetic history2 playback row; no artwork/current grant is invented.
        history_fixture=json.loads((ROOT/'tests/fixtures/session_core/retention-v2-touch.json').read_text())['tail_window']
        playback_page=deepcopy(history_fixture)
        seed=history_fixture['entries'][0]
        observed={key:deepcopy(seed[key]) for key in ['session_id','order','occurred_at','retained_until','historical_view_only','current_display_allowed']}
        observed.update(entry_id='synthetic-history-playback',kind='playback_observed',
            text='Observed <img> 🎧 · Observed artist · Observed album',requires_spotify_attribution=True,
            playback={'coverage':'observed_playing_not_full_listen','title':'Observed <img> 🎧','artist':'Observed artist','album':'Observed album','source_url':'https://open.spotify.com/track/0000000000000000000001'})
        playback_page.update(entries=[observed],next_cursor=None)
        owner._clock=ExpiryClock(lambda:timestamp(seed['occurred_at'])+1,lambda:0)
        owner._caps=caps;owner.transport.timeline=Mock(return_value=playback_page)
        window.setProperty('activeScreen','history')
        owner.openSaved(playback_page['session']['session_id']);backend._executor.submit.call_args.args[0]()
        assert owner.state['timeline']['entries'][0]['historical_playback']['title']=='Observed <img> 🎧'
        for language in ['en','nl','de','fr','es']:
            backend.setLanguage(language);backend._toast_visible=False;backend.toastChanged.emit()
            flick.setProperty('contentY',0)
            capture('history-observed-playback-'+language)
            if language=='nl':
                flick.setProperty('contentY',max(0,flick.property('contentHeight')-flick.property('height')))
                capture('history-observed-playback-full-card')
        owner._clock=ExpiryClock(lambda:timestamp(seed['retained_until']),lambda:0);owner._expire()
        assert not owner.state['timeline']['entries']
        capture('history-observed-playback-expired')
        # Bounded multi-page search is freshly re-read, never old-body appended.
        owner.invalidate();window.setProperty('activeScreen','session')
        search_caps={**caps,'capabilities':{**caps['capabilities'],'session_flow_text_search':True},
            'contract_versions':{**caps['contract_versions'],'session_flow_text_search':1}}
        owner.transport.active=Mock(return_value={'success':True,'session':session})
        owner._session=session;owner._caps=search_caps;owner._loaded=True
        owner._clock=ExpiryClock(lambda:timestamp(seed['occurred_at'])+1,lambda:0)
        owner.transport.capabilities=Mock(return_value=search_caps)
        owner.changed.emit()
        search_pages=[]
        for number in range(6):
            rows=[]
            for n in range(2):
                row=deepcopy(seed)
                row.update(entry_id=f'synthetic-search-{number}-{n}',session_id=session['session_id'],order=number*2+n+1,
                    text=('Synthetic <img> 🎧 retained search text. '*10),highlights=[{'start_utf16':0,'length_utf16':9}])
                rows.append(row)
            search_pages.append({'success':True,'schema_version':2,'history_contract_version':2,
                'session_id':session['session_id'],'query':'Synthetic','revision':'synthetic-search-revision',
                'matches':rows,'returned_count':2,'complete':False,'next_cursor':f'search-{number+1}',
                'total_count':None,'normalization':'NFKC-casefold','highlight_units':'utf16'})
        owner.transport.search=Mock(side_effect=lambda binding,sid,q,**kw:deepcopy(search_pages[int(kw['cursor'].split('-')[-1]) if kw['cursor'] else 0]))
        search_panel=window.findChild(QObject,'sessionSearchPanel')
        search_field=window.findChild(QObject,'sessionSearchInput')
        QMetaObject.invokeMethod(screen,'showSearch');QTest.qWait(80)
        complete_navigation()
        search_field.setProperty('text','Synthetic')
        QMetaObject.invokeMethod(screen,'searchNow');complete_navigation()
        search_panel.setProperty('keyboardVisible',False)
        for _ in range(4):
            complete_navigation();owner.moreSearch();complete_navigation()
        assert owner.state['search_limit_reached'] and len(owner.state['search']['matches'])==10,(owner.state['error'],owner.state['search'],search_panel.property('opened'))
        for language in ['en','nl','de','fr','es']:
            backend.setLanguage(language);backend._toast_visible=False;backend.toastChanged.emit()
            capture('search-bounded-scan-limit-'+language)
        # Revalidation replaces all displayed bodies atomically; surviving visible identity stays put.
        # Obtain the actual Flickable through its ScrollView rather than assuming visual parents.
        search_flick=window.findChild(QObject,'sessionSearchScroll').property('contentItem')
        search_flick.setProperty('contentY',160);QTest.qWait(80)
        QMetaObject.invokeMethod(screen,'rememberSearch')
        search_position=screen.property('searchReturn').toVariant()
        removed=search_pages[4]['matches'].pop();search_pages[4]['returned_count']=1
        search_pages[3]['matches'][0]['text']='Fresh replacement <img> 🎧 from the synthetic server'
        QMetaObject.invokeMethod(screen,'refreshSearchResults');complete_navigation()
        assert removed['entry_id'] not in {row['entry_id'] for row in owner.state['search']['matches']}
        assert any(row['text'].startswith('Fresh replacement') for row in owner.state['search']['matches'])
        QMetaObject.invokeMethod(screen,'rememberSearch')
        restored_search_position=screen.property('searchReturn').toVariant()
        assert restored_search_position['id']==search_position['id'] and abs(restored_search_position['offset']-search_position['offset'])<1
        capture('search-revalidated-withdrawal-position')
        # Actual timer callback waits for a busy read; closing cancels before query dispatch.
        complete_navigation()
        owner.refresh();held_search_control=backend._executor.submit.call_args.args[0]
        search_tick=window.findChild(QObject,'sessionSearchRevalidationTimer')
        QMetaObject.invokeMethod(search_tick,'triggered');QTest.qWait(30)
        assert screen.property('searchRefreshPending')
        before_search=owner.transport.search.call_count
        QMetaObject.invokeMethod(search_panel,'close');QTest.qWait(80)
        held_search_control();QTest.qWait(80)
        assert not screen.property('searchRefreshPending') and owner.transport.search.call_count==before_search
        assert search_field.property('text')=='' and not owner.state['search']
        capture('search-close-cancels-busy-timer-intent')
        QMetaObject.invokeMethod(screen,'showSearch');complete_navigation()
        search_field.setProperty('text','Synthetic')
        QMetaObject.invokeMethod(screen,'searchNow');complete_navigation()
        owner.transport.search=Mock(side_effect=SessionError('denied'))
        QMetaObject.invokeMethod(search_tick,'triggered');complete_navigation()
        assert not owner.state['search']
        capture('search-denied-withdrawal')
        QMetaObject.invokeMethod(search_panel,'close');QTest.qWait(80)
        assert search_field.property('text')=='' and not screen.property('searchRefreshPending')
        owner.transport.capabilities=Mock(return_value=caps)
        # Current-history and archive routing share source code, not authority.
        owner.invalidate();window.setProperty('activeScreen','session')
        owner._session=session;owner._caps=caps;owner._loaded=True;owner.changed.emit()
        nav_page={**page,'entries':[],'next_cursor':None}
        archive_sid='synthetic-archive-session'
        archive_page={**nav_page,'session':{**page['session'],'session_id':archive_sid}}
        owner.transport.timeline=Mock(side_effect=lambda binding,sid,**kwargs: archive_page if sid==archive_sid else nav_page)
        owner.transport.active=Mock(return_value={'success':True,'session':session})
        owner._clock=ExpiryClock()
        field.setProperty('text','Synthetic navigation draft')
        QMetaObject.invokeMethod(history_button,'clicked');complete_navigation()
        def visual_named(item,name):
            if item.objectName()==name: return item
            for child in item.childItems():
                found=visual_named(child,name)
                if found is not None: return found
            return None
        session_tab=visual_named(window.contentItem(),'appTab-session');more_tab=visual_named(window.contentItem(),'appTab-more')
        back_button=window.findChild(QObject,'sessionHistoryBack')
        assert window.property('activeScreen')=='session-history' and session_tab.property('checked') and not more_tab.property('checked')
        capture('navigation-current-history-session-tab')
        QMetaObject.invokeMethod(back_button,'clicked')
        assert window.property('activeScreen')=='session' and not owner.state['timeline']
        assert field.property('text')=='Synthetic navigation draft'
        capture('navigation-current-history-back-flow')
        QMetaObject.invokeMethod(more_tab,'clicked')
        QTest.qWait(80)  # The archive control must actually be visible before a user can click it.
        owner.transport.history=Mock(return_value={'success':True,'schema_version':2,'history_contract_version':2,
            'sessions':[{'session_id':archive_sid,'revision':'archive-revision','started_at':'2026-10-19T12:00:00Z'}],'next_cursor':None})
        QMetaObject.invokeMethod(window.findChild(QObject,'openSessionArchive'),'clicked')
        QTest.qWait(80)
        complete_navigation()
        assert owner.state['history_loaded'] and len(owner.state['sessions'])==1
        assert window.property('activeScreen')=='history' and more_tab.property('checked') and not session_tab.property('checked')
        capture('navigation-more-archive-list')
        archive_row=visual_named(window.contentItem(),'sessionArchiveRow')
        assert archive_row is not None
        QMetaObject.invokeMethod(archive_row,'clicked');backend._executor.submit.call_args.args[0]()
        assert owner.state['timeline']['session']['session_id']==archive_sid
        assert owner.state['session_id']==session['session_id'] and more_tab.property('checked')
        capture('navigation-archive-detail-original-session')
        QMetaObject.invokeMethod(back_button,'clicked')
        assert window.property('activeScreen')=='history' and not owner.state['timeline']
        capture('navigation-archive-back-list')
        QMetaObject.invokeMethod(back_button,'clicked')
        assert window.property('activeScreen')=='more'
        capture('navigation-archive-back-more')
        # Real owner open/anchor read -> QML entryOpened, from both navigation origins.
        def opened_page(sid):
            row={'entry_id':'synthetic-navigation-entry','session_id':sid,'kind':'conversation_user','order':1,
                'occurred_at':'2026-10-20T01:00:00Z','retained_until':'9999-01-01T00:00:00Z',
                'historical_view_only':True,'current_display_allowed':False,'text':'Synthetic retained text',
                'role':'user','input_type':'text','turn_id':'synthetic-navigation-turn'}
            return {**nav_page,'session':{'session_id':sid,'revision':'navigation-revision'},'revision':'navigation-revision','entries':[row]}
        for origin,sid,label in [('session',session['session_id'],'current'),('session',archive_sid,'foreign-from-flow'),('history',archive_sid,'archive')]:
            window.setProperty('activeScreen',origin)
            target=opened_page(sid)
            owner.transport.timeline=Mock(return_value=target)
            owner.transport.open_entry=Mock(return_value={**target,'navigation_only':True,'read_only':True,'entry':target['entries'][0]})
            owner.openEntry(sid,'synthetic-navigation-entry');backend._executor.submit.call_args.args[0]()
            expected='session-history' if origin=='session' else 'history'
            assert window.property('activeScreen')==expected
            assert session_tab.property('checked')==(origin=='session')
            assert owner.state['session_id']==session['session_id']
            capture('navigation-search-open-'+label)
        owner.invalidate()
        assert window.property('activeScreen')=='more' and not owner.state['timeline']
        capture('navigation-archive-context-withdrawn')
        owner._session=session;owner._caps=caps;owner._loaded=True;owner.changed.emit()
        before_submit=backend._executor.submit.call_count
        QMetaObject.invokeMethod(window.findChild(QObject,'openSessionArchive'),'clicked')
        owner.invalidate();QTest.qWait(80)
        assert backend._executor.submit.call_count==before_submit
        assert window.property('activeScreen')=='more' and not screen.property('historyReadPending')
        capture('navigation-queued-archive-withdrawn')
        window.setProperty('activeScreen','session')
        owner._session=session;owner._caps=caps;owner._loaded=True;owner.changed.emit()
        owner.transport.timeline=Mock(return_value=nav_page)
        QMetaObject.invokeMethod(history_button,'clicked');complete_navigation()
        owner.setForeground(False)
        assert window.property('activeScreen')=='session' and not owner.state['timeline'] and not owner.state['session_id']
        assert screen.property('flowReturn') is None
        capture('navigation-current-foreground-withdrawn')
        backend.shutdown()
        delete(window);delete(engine)
    errors=[value for value in warnings if any(word in value for word in ('ReferenceError','TypeError','Error:','Cannot assign','is not a type','failed to load','Binding loop detected'))]
    (output/'readback.json').write_text(json.dumps({'captures':captures,'qml_errors':errors,
        'proof':'Synthetic transport -> real controller -> actual QML; automatic fixture polling paused, reads explicit; not HA/model/ARM/installed/physical acceptance'},indent=2))
    assert not errors,errors
    print(f'{len(captures)} composer views, explicit QML send and context clearing; no QML errors')


if __name__=='__main__':
    main()
