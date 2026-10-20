"""Explicit preparation keeps provider work separate from pure image reads."""
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from test_session_artwork import prepare

from djconnect_pi.session_transport import SessionError

pytest_plugins = ['test_session_controller']


def setup(owner):
    host, image_jobs, _store = prepare(owner)
    fresh = deepcopy(owner._session)
    owner._session['broadcast']['session_media'] = []
    owner._artwork_prepare.executor = SimpleNamespace(submit=owner.backend.jobs.append, shutdown=lambda **kw: None)
    owner.setMomentArtworkVisible(True)
    owner.transport.prepare_artwork = Mock(return_value={'success': True, 'contract_version': 1,
        'session_media': deepcopy(fresh['broadcast']['session_media'])})
    owner.transport.active = Mock(return_value={'success': True, 'session': fresh})
    sid = owner._session['session_id'];mid = owner._session['broadcast']['native_delivery']['current_moment_id']
    return host, image_jobs, fresh, sid, mid


def test_explicit_prepare_then_independent_owner_read_preserves_other_client_state(controller):
    owner, backend = controller;_host, image_jobs, _fresh, sid, mid = setup(owner)
    owner._conversation = [{'body': 'existing conversation'}]
    owner._selection = {'kind': 'selected_moment', 'session_id': sid, 'moment_id': mid}
    assert owner.prepareArtwork(sid, mid) and owner.busy
    assert not owner.prepareArtwork(sid, mid) and len(backend.jobs) == 1
    assert owner.state['artwork_prepare']['status'] == 'loading'
    backend.jobs.pop()()
    owner.transport.prepare_artwork.assert_called_once_with(owner.transport.binding(), sid, mid)
    owner.transport.active.assert_called_once()
    assert owner._conversation == [{'body': 'existing conversation'}] and owner._selection['moment_id'] == mid
    assert owner._session['broadcast']['session_media'] and not owner.busy and len(image_jobs) == 1
    assert owner._artwork_prepare.request is None


@pytest.mark.parametrize('reason', ['foreground','profile','hide','end','expiry','current','revision','capability','private'])
def test_original_authority_required_before_queued_post_without_gui_tick(controller, reason):
    owner, backend = controller;host, _jobs, _fresh, sid, mid = setup(owner)
    assert owner.prepareArtwork(sid, mid);work = backend.jobs.pop()
    if reason == 'foreground': owner.setForeground(False)
    elif reason == 'profile': backend.cfg.active_profile_id = 'foreign'
    elif reason == 'hide': owner.setMomentArtworkVisible(False)
    elif reason == 'end': owner.end(sid)
    elif reason == 'expiry': host.tick = 2
    elif reason == 'current': owner._session['broadcast']['native_delivery']['current_moment_id'] = None
    elif reason == 'revision': owner._session['broadcast']['native_delivery']['revision'] = 'new'
    elif reason == 'capability': owner._caps['capabilities']['session_artwork'] = False
    else: backend.cfg.private_session = True
    work();owner.transport.prepare_artwork.assert_not_called();owner.transport.active.assert_not_called()
    assert not owner._artwork_prepare.running


@pytest.mark.parametrize('reason', ['hide', 'revision'])
def test_observed_withdrawal_cannot_revive_queued_intent_on_return(controller, reason):
    owner, backend = controller;_host, _jobs, _fresh, sid, mid = setup(owner)
    assert owner.prepareArtwork(sid, mid);work = backend.jobs.pop()
    if reason == 'hide': owner.setMomentArtworkVisible(False);owner.setMomentArtworkVisible(True)
    else:
        original = owner._session['broadcast']['native_delivery']['revision']
        owner._session['broadcast']['native_delivery']['revision'] = 'changed';owner.changed.emit()
        owner._session['broadcast']['native_delivery']['revision'] = original;owner.changed.emit()
    work();owner.transport.prepare_artwork.assert_not_called()


@pytest.mark.parametrize('reason', ['foreground','profile','hide','expiry'])
def test_started_post_can_finish_but_cannot_start_followup_read_after_withdrawal(controller, reason):
    owner, backend = controller;host, _jobs, _fresh, sid, mid = setup(owner)
    response = owner.transport.prepare_artwork.return_value
    def finish(*args):
        if reason == 'foreground':owner.setForeground(False)
        elif reason == 'profile':backend.cfg.active_profile_id = 'foreign'
        elif reason == 'hide':owner.setMomentArtworkVisible(False)
        else:host.tick = 2
        return response
    owner.transport.prepare_artwork.side_effect = finish
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    owner.transport.prepare_artwork.assert_called_once();owner.transport.active.assert_not_called()


@pytest.mark.parametrize('bad', ['boolversion','foreign','entry','duplicate','missing'])
def test_malformed_post_is_not_published_or_followed_by_get(controller, bad):
    owner, backend = controller;_host, _jobs, _fresh, sid, mid = setup(owner)
    response = owner.transport.prepare_artwork.return_value
    if bad == 'boolversion':response['contract_version'] = True
    elif bad == 'foreign':response['session_media'][0]['session_id'] = 'foreign'
    elif bad == 'entry':response['session_media'][0]['entry_id'] = 'historical'
    elif bad == 'duplicate':response['session_media'] *= 2
    else:response.pop('session_media')
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    owner.transport.active.assert_not_called();assert owner.state['artwork_prepare']['status'] == 'unavailable'
    assert owner.state['moments']


def test_post_ready_does_not_replace_missing_or_flow_only_fresh_grant(controller):
    owner, backend = controller;_host, image_jobs, fresh, sid, mid = setup(owner)
    fresh['broadcast']['session_media'][0]['artwork']['current_display_allowed'] = False
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    assert not image_jobs and not owner.momentArtwork and owner.state['artwork_prepare']['status'] == 'unavailable'
    assert owner.state['moments']


def test_expiry_between_worker_and_gui_result_drops_media(controller):
    owner, backend = controller;host, image_jobs, _fresh, sid, mid = setup(owner)
    prep = owner._artwork_prepare;results=[];prep.ready.disconnect(prep.finish);prep.ready.connect(results.append)
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()();assert results
    host.tick = 2;prep.finish(results.pop())
    assert not owner._session['broadcast']['session_media'] and not image_jobs


def test_uncertain_optional_prepare_preserves_text_and_refresh_never_replays_post(controller):
    owner, backend = controller;_host, _jobs, _fresh, sid, mid = setup(owner)
    owner.transport.prepare_artwork.side_effect = SessionError('uncertain')
    owner.transport.active.return_value = {'success': True, 'session': deepcopy(owner._session)}
    owner.transport.capabilities.return_value = deepcopy(owner._caps)
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    assert owner.state['moments'] and owner.state['artwork_prepare']['status'] == 'uncertain'
    owner.refresh();backend.jobs.pop()()
    owner.transport.prepare_artwork.assert_called_once()
    assert owner.state['artwork_prepare']['available']


def test_optional_owner_denial_withdraws_private_session(controller):
    owner, backend = controller;_host, _jobs, _fresh, sid, mid = setup(owner)
    owner.transport.prepare_artwork.side_effect = SessionError('denied')
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    assert not owner.state['moments'] and owner.state['error'] == 'denied'


def test_paired_wire_contains_only_version_original_session_and_single_moment_target(controller):
    owner, _backend = controller;_host, _jobs, _fresh, sid, mid = setup(owner)
    transport = owner.transport
    del transport.prepare_artwork
    response = Mock(status_code=200);response.json.return_value = {'success': True, 'contract_version': 1, 'session_media': []}
    binding = transport.binding()
    with patch('djconnect_pi.session_transport.requests.request', return_value=response) as request:
        transport.prepare_artwork(binding, sid, mid)
    args, kwargs = request.call_args
    assert args == ('POST', binding.ha_url+'/api/djconnect/v1/session/media/prepare')
    assert kwargs['json'] == {**binding.identity(), 'contract_version': 1, 'session_id': sid, 'targets': [{'moment_id': mid}]}
    assert kwargs['headers']['Authorization'] == 'Bearer '+binding.token
    assert kwargs['headers']['X-DJConnect-Profile-ID'] == binding.profile_id
    assert kwargs['timeout'] == 24 and kwargs['allow_redirects'] is False


def test_real_preparation_worker_keeps_end_control_independent_in_isolated_qt_process():
    import os
    import subprocess
    import sys
    from pathlib import Path

    script = '''
from threading import Event
from unittest.mock import Mock
from PySide6.QtCore import QCoreApplication
from djconnect_pi.session_controller import SessionController
from test_session_controller import Backend
from test_session_artwork_prepare import setup
app=QCoreApplication([]);backend=Backend();owner=SessionController(backend);owner._deadline_timer.stop()
_host,_jobs,_fresh,sid,mid=setup(owner);owner._artwork_prepare.executor=None
entered=Event();release=Event();response=owner.transport.prepare_artwork.return_value
calls=owner.transport.active
calls.return_value={'success':True,'session':None}
owner.transport.capabilities=Mock(return_value={})
owner.transport.end=Mock(return_value={'success':True})
def held(*args):
    entered.set()
    assert release.wait(3)
    return response
owner.transport.prepare_artwork.side_effect=held
assert owner.prepareArtwork(sid,mid) and entered.wait(2)
assert not backend.jobs
owner.end(sid);assert len(backend.jobs)==1
backend.jobs.pop()()
owner.transport.end.assert_called_once()
assert not owner.state['session_id'] and not release.is_set()
release.set();owner._artwork_prepare.executor.shutdown(wait=True)
app.processEvents()
assert calls.call_count==1 and not owner.momentArtwork
owner.shutdownImages()
'''
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'PYTHONPATH': str(root/'src')+os.pathsep+str(root/'tests')}
    result = subprocess.run([sys.executable, '-c', script], cwd=root, env=env, capture_output=True, text=True, timeout=12, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize('reason', ['session','native'])
def test_fresh_owner_withdrawal_clears_only_still_original_current_context(controller, reason):
    owner, backend = controller;_host, _jobs, fresh, sid, mid = setup(owner)
    if reason == 'session':owner.transport.active.return_value = {'success': True, 'session': None}
    else:fresh['broadcast']['native_delivery']['current_moment_id'] = None
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    assert not owner.state['session_id'] and owner.state['error'] == 'context_changed'
    assert owner._artwork_prepare.request is None


def test_withdrawal_clears_pending_binding_metadata_before_worker_finishes(controller):
    owner, backend = controller;_host, _jobs, _fresh, sid, mid = setup(owner)
    assert owner.prepareArtwork(sid, mid);assert owner._artwork_prepare.request
    owner.setMomentArtworkVisible(False)
    assert owner._artwork_prepare.request is None and owner._artwork_prepare.running
    backend.jobs.pop()();owner.transport.prepare_artwork.assert_not_called()


def test_unavailable_status_drops_reference_metadata_at_original_native_expiry(controller):
    owner, backend = controller;host, _jobs, fresh, sid, mid = setup(owner)
    fresh['broadcast']['session_media'] = []
    assert owner.prepareArtwork(sid, mid);backend.jobs.pop()()
    assert owner._artwork_prepare.request and owner.state['artwork_prepare']['status'] == 'unavailable'
    host.tick = 2
    assert owner.state['artwork_prepare']['status'] == '' and owner._artwork_prepare.request is None
