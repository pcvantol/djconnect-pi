"""Real shared Qt buttons/controller; synthetic owner transport, no HA/player actions."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, QTimer, qInstallMessageHandler
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
    apply_palette(app)
    captures = []
    original = json.loads((ROOT/'tests/fixtures/session_core/native-expressive-snapshots.json').read_text())
    with patch('requests.request', side_effect=AssertionError('Unexpected network')) as network:
        for width, height, profile in [(720, 720, 'pi-zero-2w-arm64'), (1200, 1920, 'pi5-arm64')]:
            for language in ['en', 'nl', 'de', 'fr', 'es']:
                path = output/f'fixture-{width}-{language}.json'
                save_config(path, Config(language=language, release_profile=profile, log_file=str(output/'fixture.log'),
                    paired=True, device_token='synthetic-not-a-credential', device_id='djconnect-raspberry-pi-fixture',
                    ha_url='http://fixture.invalid', explicit_profile_id='profile-a', active_profile_id='profile-a',
                    active_profile_type='personal', active_profile_privacy_mode='private', screen_timeout_seconds=0,
                    music_backend='spotify_direct', music_backend_available=True, music_backend_revision=4,
                    music_backend_capabilities={'supports_favorites': True}))
                with patch.object(QTimer, 'singleShot'):
                    backend = DJConnectBackend(path)
                for timer in backend.findChildren(QTimer):
                    timer.stop()
                reads = []
                intents = []
                backend._executor.submit = Mock()
                backend._session_executor = SimpleNamespace(submit=reads.append, shutdown=lambda **kw: None)
                backend._question_executor.submit = Mock()
                owner = backend.djSession
                owner._playback_control.executor = SimpleNamespace(submit=intents.append, shutdown=lambda **kw: None)
                snapshot = deepcopy(original['formation'][language]['home_dj'][-1])
                grant = next(row for row in snapshot['native_delivery']['admissions'] if row['moment_id'] == snapshot['native_delivery']['current_moment_id'])
                owner._clock = ExpiryClock(lambda: timestamp(grant['display_expires_at'])-1, lambda: 0)
                session = {**snapshot['session'], 'broadcast': snapshot}
                owner._session = deepcopy(session)
                owner._loaded = True
                owner.transport.active = Mock(return_value={'success': True, 'session': deepcopy(session)})
                owner.transport.capabilities = Mock(return_value={'success': True})
                owner.transport.playback_status = Mock(return_value={'success': True, 'music_backend': 'spotify_direct',
                    'music_backend_revision': 4, 'music_backend_available': True, 'backend_available': True,
                    'music_backend_capabilities': {'supports_favorites': True},
                    'playback': {'uri': 'spotify:track:'+snapshot['playback']['source_url'].rsplit('/',1)[-1], 'has_playback': True, 'is_playing': True}})
                owner.transport.playback_command = Mock(return_value={'success': True, 'playback': {'title': 'Never import command response'}})
                engine = QQmlApplicationEngine()
                engine.rootContext().setContextProperty('djconnect', backend)
                engine.rootContext().setContextProperty('startWindowed', True)
                engine.load(str(ROOT/'src/djconnect_pi/qml/Main.qml'))
                assert engine.rootObjects(), warnings
                window = engine.rootObjects()[0]
                window.setWidth(width); window.setHeight(height); window.setProperty('splashVisible', False)
                window.setProperty('activeScreen', 'session')
                for obj in window.findChildren(QObject):
                    if 'Timer' in obj.metaObject().className() and obj.property('interval') in (3000, 15000):
                        expression = QQmlExpression(engine.rootContext(), obj, 'running=false')
                        expression.evaluate(); assert not expression.hasError()
                def drain():
                    for _ in range(4):
                        if not reads:
                            break
                        reads.pop(0)()
                    assert not reads
                    QTest.qWait(80)
                drain()
                owner.refresh(); drain()
                assert owner.state['moments']
                QTest.qWait(700)  # Let the existing startup fade complete before real mouse input.
                backend._toast_visible = False; backend.toastChanged.emit()
                screen = window.findChild(QObject, 'djSessionScreen')
                popup = window.findChild(QObject, 'sessionPlaybackPanel')
                def click(name):
                    button = window.findChild(QObject, name)
                    assert button is not None and button.property('visible') and button.property('enabled'), name
                    point = button.mapToScene(QPointF(button.width()/2, button.height()/2))
                    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(round(point.x()), round(point.y())))
                    QTest.qWait(60)
                def capture(name):
                    QTest.qWait(60)
                    file = output/f'{width}-{language}-{name}.png'
                    assert window.grabWindow().save(str(file))
                    captures.append({'width': width, 'height': height, 'locale': language, 'case': name,
                        'status': owner.state['playback_control']['status'], 'file': file.name})
                def visual(item, name):
                    if item.objectName() == name:
                        return item
                    for child in item.childItems():
                        found = visual(child, name)
                        if found is not None:
                            return found
                    return None
                current_card = visual(window.contentItem(), 'sessionLiveMomentCard')
                scroll = window.findChild(QObject, 'sessionHistoryScroll').property('contentItem')
                top = current_card.mapToItem(scroll, QPointF(0, 0)).y()
                assert 0 <= top < scroll.property('height')/2, (width, language, 'contribution below fold', top)
                click('sessionPlaybackOpen'); assert popup.property('visible'), warnings
                capture('ready')
                image = window.grabWindow()
                for name in ['sessionPlaybackPrevious', 'sessionPlaybackToggle', 'sessionPlaybackNext']:
                    button = window.findChild(QObject, name)
                    icon = next(child for child in button.property('contentItem').childItems() if child.property('iconName') in ['previous', 'pause', 'next'])
                    origin = icon.mapToScene(QPointF(0, 0))
                    bright = sum(1 for yy in range(round(origin.y()), round(origin.y()+icon.height()))
                        for xx in range(round(origin.x()), round(origin.x()+icon.width()))
                        if min(image.pixelColor(xx, yy).red(), image.pixelColor(xx, yy).green(), image.pixelColor(xx, yy).blue()) > 180)
                    assert bright > 10, (width, language, name, 'missing visible glyph', bright)
                original_playback = deepcopy(owner.state['playback'])
                click('sessionPlaybackToggle')
                assert owner.state['playback_control']['status'] == 'sending' and len(intents) == 1
                assert not window.findChild(QObject, 'sessionPlaybackNext').property('enabled')
                capture('pending-pause')
                intents.pop()()
                assert owner.transport.playback_command.call_args.args[1] == 'pause'
                assert owner.state['playback'] == original_playback and owner.state['playback_control']['status'] == 'accepted'
                capture('accepted-no-optimism')
                fresh = deepcopy(session); fresh['broadcast']['playback']['state'] = 'paused'
                owner.transport.active.return_value = {'success': True, 'session': fresh}
                drain()
                owner.transport.playback_status.return_value['playback']['is_playing'] = False
                assert owner.state['playback']['state'] == 'paused'
                click('sessionPlaybackToggle'); intents.pop()()
                assert owner.transport.playback_command.call_args.args[1] == 'play'
                capture('play-sent'); drain()
                click('sessionPlaybackFavorite'); intents.pop()()
                assert owner.transport.playback_command.call_args.args[1] == 'save_current_track'
                capture('favorite-sent'); drain()
                owner.transport.playback_command.side_effect = SessionError('uncertain')
                click('sessionPlaybackNext'); intents.pop()()
                assert owner.state['playback_control']['status'] == 'uncertain' and not reads
                count = owner.transport.playback_command.call_count
                assert not owner.playbackCommand(owner.state['session_id'], owner.state['playback']['item_id'], 'next')
                capture('uncertain-no-replay')
                click('sessionPlaybackRefresh'); assert len(reads) == 1
                drain(); assert owner.transport.playback_command.call_count == count
                owner.transport.playback_command.side_effect = None
                click('sessionPlaybackPrevious'); assert len(intents) == 1
                QMetaObject.invokeMethod(popup, 'close')
                intents.pop()()  # No GUI tick/exit-animation wait may authorize queued dispatch.
                assert owner.transport.playback_command.call_count == count
                capture('closed-before-dispatch')
                screen.setProperty('historical', True); QTest.qWait(40)
                screen.setProperty('historical', False); drain()
                click('sessionPlaybackOpen')
                backend.cfg.music_backend_capabilities = {'supports_favorites': False}; owner.changed.emit(); QTest.qWait(60)
                assert not window.findChild(QObject, 'sessionPlaybackFavorite').property('visible')
                capture('favorite-unsupported')
                owner.setForeground(False); QTest.qWait(60)
                assert not popup.property('visible') and not owner.state['playback_control']['available']
                capture('foreground-withdrawn')
                backend.shutdown(); delete(window); delete(engine); delete(backend)
                app.processEvents()
        network.assert_not_called()
    errors = [x for x in warnings if any(word in x for word in ['Error:', 'ReferenceError', 'TypeError', 'Binding loop', 'Cannot assign'])]
    (output/'readback.json').write_text(json.dumps({'captures': captures, 'warnings': warnings, 'errors': errors,
        'proof': 'Real Qt mouse buttons/controller; original native frame bytes replayed at original clock. Backend metadata, commands and owner playback-state updates synthetic; no network/provider/ARM/install/physical effects.'}, indent=2))
    assert not errors, errors[:10]
    print(json.dumps({'actual_views': len(captures), 'errors': errors}))


if __name__ == '__main__':
    main()
