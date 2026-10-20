"""Explicit feedback draft opening must never export private app state."""
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.i18n import translate


@pytest.mark.parametrize("language", ["en", "nl", "de", "fr", "es"])
@pytest.mark.parametrize("opened", [True, False])
def test_feedback_opens_only_localized_static_draft_not_private_context(language, opened):
    cfg = SimpleNamespace(language=language, device_token="private-device-secret", ha_url="http://private-ha.invalid",
                          active_profile_id="private-profile", device_id="private-device", private_session=True)
    backend = SimpleNamespace(cfg=cfg, _session={"body": "private-session-text"})
    with patch("djconnect_pi.app.QDesktopServices.openUrl", return_value=opened) as browser:
        assert DJConnectBackend.openFeedbackIssue(backend) is opened
    browser.assert_called_once()
    url = browser.call_args.args[0].toString()
    parsed = urlsplit(url)
    assert (parsed.scheme, parsed.netloc, parsed.path, parsed.fragment) == ("https", "github.com", "/pcvantol/djconnect-pi/issues/new", "")
    assert parse_qs(parsed.query) == {"title": [translate(language, "feedback_issue_title")],
                                      "body": [translate(language, "feedback_issue_template")]}
    assert all(private not in url for private in ("private-device", "private-ha", "private-profile", "private-session-text"))
