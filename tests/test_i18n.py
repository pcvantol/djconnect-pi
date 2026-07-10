from __future__ import annotations

import re
from importlib.resources import files
from string import Formatter

from djconnect_pi.i18n import SUPPORTED_LANGUAGES, TRANSLATIONS, locale_for_language, normalize_language, translate
from djconnect_pi.web_portal import PORTAL_I18N_KEYS


def test_translation_languages_have_same_keys() -> None:
    expected = set(TRANSLATIONS["en"])
    assert set(TRANSLATIONS) == set(SUPPORTED_LANGUAGES)
    for language in SUPPORTED_LANGUAGES:
        assert set(TRANSLATIONS[language]) == expected


def test_translation_placeholders_match_english() -> None:
    formatter = Formatter()
    expected = {
        key: {field for _, field, _, _ in formatter.parse(value) if field}
        for key, value in TRANSLATIONS["en"].items()
    }
    for language in SUPPORTED_LANGUAGES:
        actual = {
            key: {field for _, field, _, _ in formatter.parse(value) if field}
            for key, value in TRANSLATIONS[language].items()
        }
        assert actual == expected


def test_qml_translation_keys_exist() -> None:
    qml_root = files("djconnect_pi.qml")
    qml_text = "\n".join(
        qml_root.joinpath(name).read_text(encoding="utf-8")
        for name in ("Main.qml", "GamesPanel.qml", "UpdateProgress.qml")
    )
    keys = set(re.findall(r'(?:root\.tr|djconnect\.t|updater\.t|updater\.tf)\("([^"]+)"', qml_text))
    assert keys <= set(TRANSLATIONS["en"])


def test_web_portal_translation_keys_exist_for_all_languages() -> None:
    for language in SUPPORTED_LANGUAGES:
        assert set(PORTAL_I18N_KEYS) <= set(TRANSLATIONS[language])


def test_language_normalization_defaults_to_english() -> None:
    assert normalize_language("") == "en"
    assert normalize_language("it_IT") == "en"
    assert normalize_language("de_DE.UTF-8") == "de"
    assert normalize_language("fr-FR") == "fr"


def test_transport_locale_uses_bcp47_values() -> None:
    assert locale_for_language("en") == "en-GB"
    assert locale_for_language("nl") == "nl-NL"
    assert locale_for_language("de_DE.UTF-8") == "de-DE"
    assert locale_for_language("fr-FR") == "fr-FR"
    assert locale_for_language("es") == "es-ES"
    assert locale_for_language("it_IT") == "en-GB"


def test_user_facing_translation_updates() -> None:
    assert translate("nl", "high") == "Beste"
    assert translate("nl", "dj_response") == "DJ-antwoord"
    assert translate("nl", "reboot_device") == "Apparaat herstarten"
    assert translate("nl", "shutdown_device") == "Apparaat uitschakelen"
    assert translate("nl", "check_updates") == "Controleer op updates"
    assert translate("nl", "demo_mode") == "Demomodus"
    assert translate("nl", "more") == "Meer"
    assert translate("nl", "game_asteroids") == "Meteor Run"
    assert translate("nl", "pairing_hint") == "Koppelgegevens voor Home Assistant"
    assert translate("nl", "track_insight_summary") == "Samenvatting"
    assert translate("nl", "track_insight_why_it_fits_you") == "Waarom dit bij je past"
    assert translate("nl", "track_insight_confidence") == "Zekerheid"
    assert translate("nl", "music_dna_match") == "Music DNA-match"
    assert translate("nl", "music_dna_disable_confirm_message") == "Music DNA stopt met leren van je luistergedrag en wist het bestaande profiel meteen in Home Assistant."
    assert translate("nl", "websocket_fast_path") == "Home Assistant WebSocket snelle route"
    assert translate("nl", "local_websocket_fast_path") == "Lokale WebSocket snelle route"
    assert translate("nl", "no_diagnostics") == "Geen diagnostiek beschikbaar"
    assert translate("en", "more") == "More"
    assert translate("en", "websocket_fast_path") == "Home Assistant WebSocket fast path"
    assert translate("en", "pairing_hint") == "Pairing details for Home Assistant"
    assert translate("en", "game_pacman") == "Maze Chase"
    assert translate("de", "play_now") == "Jetzt abspielen"
    assert translate("de", "track_insight_summary") == "Zusammenfassung"
    assert translate("de", "websocket_fast_path") == "Home Assistant WebSocket-Schnellpfad"
    assert translate("fr", "unknown") == "Inconnu"
    assert translate("fr", "track_insight_energy") == "Énergie"
    assert translate("fr", "websocket_fast_path") == "Chemin rapide WebSocket Home Assistant"
    assert translate("es", "local_only") == "Solo local"
    assert translate("es", "track_insight_why_it_fits_you") == "Por qué encaja contigo"
    assert translate("es", "websocket_fast_path") == "Ruta rápida WebSocket de Home Assistant"
