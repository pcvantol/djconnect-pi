from __future__ import annotations

from djconnect_pi.i18n import TRANSLATIONS, translate


def test_translation_languages_have_same_keys() -> None:
    assert set(TRANSLATIONS["nl"]) == set(TRANSLATIONS["en"])


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
