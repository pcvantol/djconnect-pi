from __future__ import annotations

import re
from importlib.resources import files
from string import Formatter

from djconnect_pi.i18n import SUPPORTED_LANGUAGES, TRANSLATIONS, normalize_language, translate


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


def test_language_normalization_defaults_to_english() -> None:
    assert normalize_language("") == "en"
    assert normalize_language("it_IT") == "en"
    assert normalize_language("de_DE.UTF-8") == "de"
    assert normalize_language("fr-FR") == "fr"


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
    assert translate("en", "more") == "More"
    assert translate("en", "pairing_hint") == "Pairing details for Home Assistant"
    assert translate("en", "game_pacman") == "Maze Chase"
    assert translate("de", "play_now") == "Jetzt abspielen"
    assert translate("fr", "unknown") == "Inconnu"
    assert translate("es", "local_only") == "Solo local"
