"""Real shared Qt buttons/controller; synthetic owner transport, no HA/player actions."""
from __future__ import annotations

import argparse
import base64
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import (
    QBuffer,
    QIODevice,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QTimer,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QImage, QWheelEvent
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from shiboken6 import delete

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.brand_theme import apply_palette
from djconnect_pi.config import Config, save_config
from djconnect_pi.expiry_clock import ExpiryClock
from djconnect_pi.ha import Playback
from djconnect_pi.i18n import TRANSLATIONS
from djconnect_pi.session_projection import timestamp
from djconnect_pi.session_transport import (
    JSON_CONTROL_BYTES,
    SessionError,
    SessionTransport,
)

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
    art = QImage(16, 16, QImage.Format.Format_RGB32)
    art.fill(Qt.GlobalColor.cyan)
    art_buffer = QBuffer()
    assert art_buffer.open(QIODevice.OpenModeFlag.WriteOnly) and art.save(art_buffer, 'PNG')
    art_source = 'data:image/png;base64,' + base64.b64encode(bytes(art_buffer.data())).decode()
    art_path = '/api/djconnect/v1/image_proxy/' + 'a' * 24
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
                    'playback': {'uri': 'spotify:track:'+snapshot['playback']['source_url'].rsplit('/',1)[-1], 'has_playback': True, 'is_playing': True, 'favorite_status': False, 'is_liked': False}})
                owner.transport.playback_command = Mock(return_value={'success': True, 'playback': {'title': 'Never import command response'}})
                owner.transport.playback_favorite = Mock(return_value={'success': True})
                engine = QQmlApplicationEngine()
                engine.rootContext().setContextProperty('djconnect', backend)
                engine.rootContext().setContextProperty('startWindowed', True)
                engine.load(str(ROOT/'src/djconnect_pi/qml/Main.qml'))
                assert engine.rootObjects(), warnings
                window = engine.rootObjects()[0]
                window.setWidth(width); window.setHeight(height); window.setProperty('splashVisible', False)
                window.setProperty('activeScreen', 'session')
                for obj in window.findChildren(QObject):
                    if (obj.objectName() == 'sessionRuntimePollTimer'
                            or ('Timer' in obj.metaObject().className() and obj.property('interval') == 3000)):
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
                transport_opener = 'sessionPlaybackProgress'
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
                assert 0 <= top < scroll.property('height'), (width, language, 'contribution below fold', top)
                artwork_button = visual(window.contentItem(), 'sessionExpandTrackArtwork')
                metadata = visual(window.contentItem(), 'sessionPlaybackMetadata')
                heading = window.findChild(QObject, 'sessionFlowHeading')
                assert not heading.property('visible')
                assert 0 <= metadata.mapToItem(scroll, 0, 0).y() < 1
                gap = top - metadata.mapToItem(scroll, 0, metadata.height()).y()
                assert abs(gap - (22 if width == 720 else 26)) <= 1, (width, language, gap)
                mode_strip = visual(window.contentItem(), 'sessionModeStrip')
                if mode_strip.property('visible'):
                    lead_gap = metadata.mapToScene(QPointF()).y() - mode_strip.mapToScene(QPointF(0, mode_strip.height())).y()
                    assert abs(lead_gap - (20 if width == 720 else 26)) <= 1, (width, language, lead_gap)
                assert visual(window.contentItem(), 'sessionPlaybackVinyl') is None
                expected_cover_size = 120 if width == 720 else 2 * round(270 * min(1.45, width / 835))
                assert artwork_button.width() == artwork_button.height() == expected_cover_size
                assert artwork_button.mapToItem(metadata, 0, 0).x() >= 0
                assert artwork_button.mapToItem(metadata, artwork_button.width(), artwork_button.height()).x() <= metadata.width()
                meter = window.findChild(QObject, 'sessionPlaybackMeter')
                bars = [item for item in meter.childItems() if item.property('level') is not None]
                assert meter.property('visible') and meter.property('playing') and len(bars) == 4
                assert max(bar.height() for bar in bars) > min(bar.height() for bar in bars)
                phase = meter.property('phase')
                QTest.qWait(100)
                assert (meter.property('phase') != phase) == meter.property('animating')
                capture('inline-track-art')
                owner._playback_artwork.fetch = Mock(return_value=art_source)
                art_jobs = []
                owner._playback_artwork.executor = SimpleNamespace(submit=art_jobs.append, shutdown=lambda **kw: None)
                cover = visual(window.contentItem(), 'sessionTrackArtwork')
                current_playback = owner._session['broadcast']['playback']
                original_item = current_playback['item_id']
                current_playback['artwork_url'] = art_path
                owner.changed.emit()
                assert len(art_jobs) == 1
                art_jobs.pop(0)()
                expression = QQmlExpression(engine.rootContext(), cover, 'Number(status) === 1')
                for _ in range(20):
                    if expression.evaluate()[0] is True:
                        break
                    QTest.qWait(50)
                assert expression.evaluate()[0] is True, warnings
                capture('current-track-art')
                click('sessionExpandTrackMetadata')
                overlay = visual(window.contentItem(), 'trackArtworkOverlay')
                expanded = visual(overlay, 'expandedTrackArtwork')
                QTest.qWait(100)
                assert overlay.width() == width and overlay.height() == height
                title = visual(overlay, 'expandedTrackTitle')
                artist = visual(overlay, 'expandedTrackArtist')
                card = expanded.parentItem()
                column = card.parentItem()
                assert expanded.width() == expanded.height() and expanded.width() > width * 0.65
                assert title.y() == card.height() + column.property('spacing')
                assert card.width() == column.width() or abs(column.height() - column.parentItem().height()) < 1
                assert expanded.property('source') == cover.property('source')
                assert title.property('text') == owner.state['playback']['title']
                assert artist.property('text') == owner.state['playback']['artist']
                capture('fullscreen-track-art')
                shade = visual(window.contentItem(), 'trackArtworkControlsShade')
                assert shade.property('visible')
                previous = visual(window.contentItem(), 'sessionPlaybackPrevious')
                toggle = visual(window.contentItem(), 'sessionPlaybackToggle')
                gap = previous.mapToScene(QPointF(previous.width(), previous.height()/2))
                gap_x = (gap.x() + toggle.mapToScene(QPointF(0, 0)).x()) / 2
                QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                                 QPoint(round(gap_x), round(gap.y())))
                QTest.qWait(60)
                assert not shade.property('visible') and window.property('trackArtworkOpen') and not intents
                click('expandedTrackArtwork')
                assert shade.property('visible')
                click('closeTrackArtwork')
                assert not window.property('trackArtworkOpen')
                for x, y in ((8, 8), (artwork_button.width() - 8, artwork_button.height() - 8)):
                    origin = artwork_button.mapToScene(QPointF(x, y))
                    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                                     QPoint(round(origin.x()), round(origin.y())))
                    QTest.qWait(60)
                    assert window.property('trackArtworkOpen') and not popup.property('opened') and not intents
                    owner.transport.playback_command.assert_not_called()
                    click('closeTrackArtwork')
                    assert not window.property('trackArtworkOpen')
                current_playback['item_id'] = 'synthetic-cover-replacement'
                current_playback['artwork_url'] = art_path[:-1] + 'b'
                owner.changed.emit()
                assert len(art_jobs) == 1 and cover.property('source').isEmpty()
                current_playback['artwork_url'] = 'https://external.invalid/album.jpg'
                owner.changed.emit()
                art_jobs.pop(0)()
                QTest.qWait(80)
                assert not art_jobs and cover.property('source').isEmpty()
                current_playback['item_id'] = original_item
                del current_playback['artwork_url']
                owner.changed.emit()

                waiting = window.findChild(QObject, 'sessionWaitingCard')
                waiting_vinyl = window.findChild(QObject, 'sessionWaitingVinyl')
                moments, retained = owner._moments, owner._retained_flow
                owner._moments, owner._retained_flow = [], []
                owner.changed.emit()
                QTest.qWait(80)
                assert waiting.property('visible') and not waiting_vinyl.property('visible')
                assert metadata.mapToItem(scroll, 0, metadata.height()).y() < waiting.mapToItem(scroll, 0, 0).y()
                capture('inline-art-before-waiting')
                assert not waiting.property('compactIdle')  # A hidden moment is not an idle receipt.
                active_session = owner._session
                owner._session = deepcopy(active_session)
                idle_broadcast = owner._session['broadcast']
                idle_broadcast['session']['runtime_state'] = 'active'
                idle_broadcast['native_delivery'].update(current_moment_id=None, current_silence_moment_id=None)
                owner.changed.emit()
                QTest.qWait(80)
                assert waiting.property('compactIdle') and waiting.width() < 120
                assert window.findChild(QObject, 'sessionCompactEnd').property('enabled')
                assert window.findChild(QObject, 'sessionCompactEnd').property('visible')
                capture('confirmed-idle-compact')
                idle_broadcast['playback']['state'] = 'paused'
                owner.changed.emit()
                QTest.qWait(80)
                paused_detail = window.findChild(QObject, 'sessionWaitingPausedDetail')
                waiting_title = window.findChild(QObject, 'sessionWaitingTitle')
                assert paused_detail.property('visible')
                assert waiting_title.property('text') == TRANSLATIONS[language]['session_playback_paused']
                assert paused_detail.property('text') == TRANSLATIONS[language]['session_playback_paused_detail']
                assert window.findChild(QObject, 'sessionExpandedEnd').property('enabled')
                assert metadata.property('visible')
                capture('waiting-paused')
                owner._session['broadcast']['playback'] = {}
                owner.changed.emit()
                QTest.qWait(80)
                assert waiting_vinyl.property('visible') and not metadata.property('visible')
                assert not paused_detail.property('visible')
                capture('waiting-vinyl-no-current-item')
                owner._session = {}
                owner.changed.emit()
                QTest.qWait(80)
                assert not heading.property('visible')
                assert window.findChild(QObject, 'sessionStartCard').property('visible')
                assert window.findChild(QObject, 'sessionWelcomeTitle').property('text') == TRANSLATIONS[language]['session_welcome_title']
                capture('heading-start-session')
                owner._session = active_session
                owner._moments, owner._retained_flow = moments, retained
                owner.changed.emit()
                QTest.qWait(80)
                modifiers = Qt.KeyboardModifier.NoModifier
                paused = deepcopy(session)
                paused['broadcast']['playback']['state'] = 'paused'
                owner.transport.active.return_value = {'success': True, 'session': paused}
                owner.transport.playback_status.return_value['playback']['is_playing'] = False
                owner.refresh(); drain()
                assert visual(window.contentItem(), 'sessionLiveMomentCard').property('visible')
                assert not paused_detail.property('visible')
                assert not meter.property('playing') and not meter.property('animating')
                assert max(bar.height() for bar in bars) == min(bar.height() for bar in bars)
                phase = meter.property('phase')
                QTest.qWait(100)
                assert meter.property('phase') == phase
                owner.transport.active.return_value = {'success': True, 'session': deepcopy(session)}
                owner.transport.playback_status.return_value['playback']['is_playing'] = True
                owner.refresh(); drain()
                progress = window.findChild(QObject, 'sessionPlaybackProgress')
                assert progress.height() >= 44
                artwork_right = artwork_button.mapToItem(metadata, artwork_button.width(), 0).x()
                progress_origin = progress.mapToItem(metadata, 0, 0)
                if width == 720:
                    assert abs(progress_origin.x() - artwork_button.mapToItem(metadata, 0, 0).x()) < 1
                    assert progress_origin.y() >= artwork_button.mapToItem(metadata, 0, artwork_button.height()).y()
                else:
                    assert progress_origin.x() > artwork_right
                    assert progress_origin.y() < artwork_button.mapToItem(metadata, 0, artwork_button.height()).y()
                capture('progress-layout')
                command_count = owner.transport.playback_command.call_count
                click('sessionPlaybackProgress'); assert popup.property('opened'), warnings
                assert popup.property('controlView') == 'all'
                assert not intents and not reads
                assert owner.transport.playback_command.call_count == command_count
                def assert_popup_anchor(trigger, panel=popup):
                    top = trigger.mapToItem(screen, 0, 0)
                    bottom = trigger.mapToItem(screen, trigger.width(), trigger.height())
                    popup_width = panel.property('width')
                    popup_height = panel.property('height')
                    x, y = panel.property('x'), panel.property('y')
                    expected_x = max(16, min((top.x() + bottom.x() - popup_width)/2,
                                             width - popup_width - 16))
                    assert abs(x - expected_x) < 2, (width, x, expected_x)
                    assert 15 <= y and y + popup_height <= height - 15
                    if bottom.y() + 8 + popup_height <= height - 16:
                        assert abs(y - (bottom.y() + 8)) < 2
                assert_popup_anchor(progress)
                assert popup.property('width') == (520 if width == 720 else round(380 * min(1.45, width / 835)))
                capture('progress-opens-playback-controls')
                QMetaObject.invokeMethod(popup, 'close')
                QTest.qWait(160)
                initial_caps = backend.cfg.music_backend_capabilities
                backend.cfg.music_backend_capabilities = {
                    **initial_caps, 'supports_volume': True, 'supports_outputs': True,
                    'supports_transfer_or_output_selection': True,
                }
                owner.changed.emit()
                QTest.qWait(80)
                output_panel = window.findChild(QObject, 'sessionOutputPanel')
                original_session = owner._session
                owner._session = deepcopy(original_session)
                owner._session['broadcast']['playback']['title'] = (
                    'A long synthetic track title with no audio or provider effect ' * 4
                ).strip()
                original_status = owner.transport.playback_status.return_value
                volume_status = deepcopy(original_status)
                volume_status['music_backend_capabilities'].update(supports_volume=True)
                volume_status['playback'].update(volume_percent=85, device={
                    'id': 'synthetic-output', 'name': 'Synthetic loudspeaker', 'active': True,
                    'is_restricted': False, 'supports_volume': True,
                })
                owner.transport.playback_status.return_value = volume_status
                owner.changed.emit()
                assert owner.readPlaybackVolume(owner.state['session_id'], owner.state['playback']['item_id'])
                intents.pop()()
                assert owner.state['playback_control']['volume']['percent'] == 85
                owner._playback_control.blocked = True
                owner.changed.emit()
                QTest.qWait(80)
                click(transport_opener)
                assert popup.property('opened')
                assert popup.property('height') <= height - 32, (width, language, popup.property('height'))
                menu_scroll = window.findChild(QObject, 'sessionPlaybackScroll')
                menu_flick = menu_scroll.property('contentItem')
                assert abs(menu_flick.property('contentY')) < 1
                if menu_flick.property('contentHeight') > menu_flick.height():
                    point = menu_scroll.mapToScene(QPointF(menu_scroll.width()/2, menu_scroll.height()/2))
                    event = QWheelEvent(point, point, QPoint(), QPoint(0, -720),
                                        Qt.MouseButton.NoButton, modifiers, Qt.ScrollPhase.NoScrollPhase, False)
                    app.sendEvent(window, event)
                    for _ in range(20):
                        QTest.qWait(50)
                        if not menu_flick.property('moving'):
                            break
                    assert menu_flick.property('contentY') > 0
                    assert not menu_flick.property('moving')
                capture('long-playback-menu-close-accessible')
                click('sessionPlaybackClose')
                assert not popup.property('opened')
                owner._playback_control.blocked = False
                owner.transport.playback_status.return_value = original_status
                owner._session = original_session
                owner.changed.emit()
                QTest.qWait(180)
                if width == 1200:
                    observed = deepcopy(volume_status)
                    observed['music_backend_capabilities'].update(supports_outputs=True, supports_transfer_or_output_selection=True)
                    observed['playback']['volume_percent'] = 11
                    owner.transport.playback_status.return_value = observed
                    owner.transport.playback_outputs = Mock(return_value={**observed, 'devices': [
                        {'id': 'synthetic-output', 'name': 'Synthetic loudspeaker', 'active': True, 'cached': False, 'is_restricted': False},
                        {'id': 'synthetic-alternative', 'name': 'Synthetic second speaker', 'active': False, 'cached': False, 'is_restricted': False},
                    ]})
                    click('sessionToolbarOutput')
                    assert output_panel.property('opened') and len(intents) == 1
                    intents.pop()()
                    QTest.qWait(80)
                    assert output_panel.property('width') == round(360 * min(1.45, width / 835))
                    selected_output = visual(window.contentItem(), 'sessionOutputChoice-synthetic-output')
                    assert selected_output.property('checked') and not selected_output.property('enabled')
                    capture('ipad-output-inventory')
                    click('sessionOutputClose')
                    QTest.qWait(80)
                    click('sessionToolbarVolume')
                    assert popup.property('opened') and len(intents) == 1
                    intents.pop()()
                    QTest.qWait(80)
                    slider = window.findChild(QObject, 'sessionVolumeSlider')
                    assert slider.property('visible') and slider.property('value') == 11
                    assert popup.property('width') == round(320 * min(1.45, width / 835))
                    capture('ipad-volume-observed')
                    click('sessionPlaybackClose')
                    QTest.qWait(80)
                    owner.transport.playback_status.return_value = original_status
                backend.cfg.music_backend_capabilities = initial_caps
                owner.changed.emit()
                QTest.qWait(80)
                click(transport_opener); assert popup.property('visible'), warnings
                assert_popup_anchor(window.findChild(QObject, transport_opener))
                popup_position = (popup.property('x'), popup.property('y'))
                capture('ready')
                original_session = owner._session
                owner._session = deepcopy(original_session)
                owner._session['broadcast']['playback']['position_ms'] += 750
                owner.changed.emit()
                QTest.qWait(60)
                assert popup.property('opened') and not intents
                assert (popup.property('x'), popup.property('y')) == popup_position
                capture('open-playback-menu-survives-position')
                owner._session['broadcast']['playback']['item_id'] = 'synthetic-new-track'
                owner.changed.emit()
                assert not popup.property('opened') and not intents
                QTest.qWait(180)
                capture('playback-menu-closes-on-track-change')
                owner._session = original_session
                owner.changed.emit()
                QTest.qWait(60)
                click(transport_opener)
                assert visual(window.contentItem(), 'sessionPlaybackToggle') is None
                click('sessionPlaybackFavorite'); intents.pop()()
                owner.transport.playback_favorite.assert_not_called()
                QTest.qWait(60)
                click('sessionPlaybackFavorite'); intents.pop()()
                owner.transport.playback_favorite.assert_called_once()
                assert owner.transport.playback_favorite.call_args.args[1] is True
                capture('favorite-sent'); drain()
                click('sessionPlaybackClose')
                click('sessionExpandTrackArtwork')
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
                owner.transport.playback_command.side_effect = SessionError('uncertain')
                click('sessionPlaybackNext'); intents.pop()()
                assert owner.state['playback_control']['status'] == 'uncertain' and not reads
                count = owner.transport.playback_command.call_count
                assert not owner.playbackCommand(owner.state['session_id'], owner.state['playback']['item_id'], 'next')
                capture('uncertain-no-replay')
                click('trackArtworkPlaybackRefresh'); assert len(reads) == 1
                drain(); assert owner.transport.playback_command.call_count == count
                owner.transport.playback_command.side_effect = None
                click('sessionPlaybackPrevious'); assert len(intents) == 1
                click('closeTrackArtwork')
                intents.pop()()  # No GUI tick/exit-animation wait may authorize queued dispatch.
                assert owner.transport.playback_command.call_count == count
                capture('closed-before-dispatch')
                screen.setProperty('historical', True); QTest.qWait(40)
                assert heading.property('visible')
                assert heading.property('text') == TRANSLATIONS[language]['session_history']
                capture('heading-session-archive')
                screen.setProperty('historical', False); drain()
                click(transport_opener)
                backend.cfg.music_backend_capabilities = {'supports_favorites': False}; owner.changed.emit(); QTest.qWait(60)
                assert not window.findChild(QObject, 'sessionPlaybackFavorite').property('visible')
                capture('favorite-unsupported')
                click('sessionPlaybackClose')
                click('sessionExpandTrackArtwork')
                # Exercise real streamed command transport under existing real Qt controls.
                owner.transport.playback_command = SessionTransport.playback_command.__get__(owner.transport, SessionTransport)
                for mode in ('declared-oversize', 'streamed-oversize', 'exact-boundary'):
                    size = JSON_CONTROL_BYTES + (0 if mode == 'exact-boundary' else 1)
                    base = b'{"success":true,"padding":""}'
                    raw = base[:-2] + b'x' * (size - len(base)) + base[-2:]
                    bounded_response = Mock(status_code=200, headers={})
                    if mode == 'declared-oversize':
                        bounded_response.headers = {'Content-Length': str(size)}
                    bounded_response.iter_content.side_effect = lambda *, chunk_size: (
                        raw[i:i + chunk_size] for i in range(0, len(raw), chunk_size))
                    bounded_calls = []
                    class BoundedSession:
                        def __enter__(self): return self
                        def __exit__(self, *args): bounded_response.close.assert_called_once()
                        def request(self, *args, **kwargs):
                            assert self.trust_env is False and kwargs['stream'] is True
                            bounded_calls.append((args, kwargs))
                            return bounded_response
                    with patch('requests.Session', BoundedSession):
                        click('sessionPlaybackNext'); assert len(intents) == 1
                        intents.pop()()
                    QTest.qWait(60)
                    assert len(bounded_calls) == 1, (mode, len(bounded_calls))
                    assert len(reads) == (1 if mode == 'exact-boundary' else 0), (mode, len(reads))
                    bounded_response.json.assert_not_called()
                    assert owner.state['session_id'] and window.property('trackArtworkOpen')
                    if mode == 'exact-boundary':
                        assert owner.state['playback_control']['status'] != 'uncertain'
                    else:
                        assert owner.state['playback_control']['status'] == 'uncertain'
                        assert not owner.playbackCommand(owner.state['session_id'], owner.state['playback']['item_id'], 'next')
                    if mode == 'declared-oversize': bounded_response.iter_content.assert_not_called()
                    capture(mode)
                    if mode == 'exact-boundary': drain()  # Existing successful-command owner read, no write replay.
                    if mode != 'exact-boundary':
                        click('trackArtworkPlaybackRefresh'); assert len(reads) == 1
                        drain()
                    assert len(bounded_calls) == 1
                screen.setProperty('draft', 'Synthetic private draft before denial')
                response = Mock(status_code=401 if width == 720 else 403)
                response.json.side_effect = ValueError('Synthetic malformed denial body')
                denial_calls = []
                class DenialSession:
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                    def request(self, *args, **kwargs):
                        assert self.trust_env is False
                        denial_calls.append((args, kwargs))
                        return response
                owner.transport.playback_command = SessionTransport.playback_command.__get__(owner.transport, SessionTransport)
                token = backend.cfg.device_token
                with patch('requests.Session', DenialSession):
                    click('sessionPlaybackNext'); assert len(intents) == 1
                    intents.pop()()
                QTest.qWait(60)
                assert not owner.state['session_id'] and owner.state['error'] == 'denied'
                assert not screen.property('draft') and not window.property('trackArtworkOpen')
                assert backend.cfg.paired and backend.cfg.device_token == token
                assert len(denial_calls) == 1 and not reads
                response.json.assert_not_called()
                assert heading.property('visible') and not progress.property('visible')
                capture('malformed-http-denial-withdrawn')
                owner.setForeground(False); QTest.qWait(60)
                assert not popup.property('visible') and not owner.state['playback_control']['available']
                assert not meter.property('animating')
                capture('foreground-withdrawn')
                if language == 'en':
                    window.setProperty('activeScreen', 'more')
                    backend.cfg.screen_timeout_seconds = 1
                    backend.screenTimeoutChanged.emit()
                    QTest.qWait(1150)
                    assert window.property('screenBlanked')
                    with patch('djconnect_pi.app.subprocess.run') as display_command:
                        backend._apply_playback(Playback(title='Next track', artist='Next artist',
                                                         uri='fixture:track:2', image_url=art_source, is_playing=True))
                    assert display_command.call_args_list[-1].args[0] == ['xset', 'dpms', 'force', 'on']
                    assert window.property('activeScreen') == 'session' and not window.property('screenBlanked')
                    assert window.property('trackArtworkOpen')
                    assert visual(window.contentItem(), 'expandedTrackTitle').property('text') == 'Next track'
                    QTest.qWait(4300)
                    assert window.property('trackArtworkOpen')
                    for _ in range(17):
                        if not window.property('trackArtworkOpen'):
                            break
                        QTest.qWait(100)
                    assert not window.property('trackArtworkOpen') and window.property('activeScreen') == 'session'
                    backend._apply_playback(Playback(title='Next track', artist='Next artist',
                                                     uri='fixture:track:2', image_url='', is_playing=True))
                    assert not window.property('trackArtworkOpen')
                    backend.cfg.screen_timeout_seconds = 0
                    backend.screenTimeoutChanged.emit()
                    backend._apply_playback(Playback())
                if language == 'en':
                    for destination in ('queue', 'playlists', 'more'):
                        window.setProperty('activeScreen', destination)
                        backend._apply_playback(Playback(title=destination, uri='fixture:' + destination,
                                                         image_url=art_source))
                        assert window.property('activeScreen') == destination
                        assert not window.property('trackArtworkOpen')
                    window.setProperty('activeScreen', 'session')
                    backend._apply_playback(Playback(title='New track', uri='fixture:session', image_url=art_source))
                    assert window.property('trackArtworkOpen')
                    window.setProperty('activeScreen', 'more')
                    assert not window.property('trackArtworkOpen')
                if width == 720 and language == 'en':
                    window.setProperty('activeScreen', 'now')
                    QTest.qWait(80)
                    click('nowTrackArtwork')
                    assert window.property('activeScreen') == 'control' and not window.property('trackArtworkOpen')
                    click('controlTrackMetadata')
                    assert not window.property('trackArtworkOpen')
                backend.shutdown(); delete(window); delete(engine); delete(backend)
                app.processEvents()
        network.assert_not_called()
    errors = [x for x in warnings if any(word in x for word in ['Error:', 'ReferenceError', 'TypeError', 'Binding loop', 'Cannot assign', 'QGridLayoutEngine'])]
    (output/'readback.json').write_text(json.dumps({'captures': captures, 'warnings': warnings, 'errors': errors,
        'proof': 'Real Qt mouse buttons/controller; original native frame bytes replayed at original clock. Backend metadata, commands and owner playback-state updates synthetic; no network/provider/ARM/install/physical effects.'}, indent=2))
    assert not errors, errors[:10]
    print(json.dumps({'actual_views': len(captures), 'errors': errors}))


if __name__ == '__main__':
    main()
