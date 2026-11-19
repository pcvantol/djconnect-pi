from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
import requests

from djconnect_pi.config import Config
from djconnect_pi.ha import HAClient
from djconnect_pi.shared_settings import (
    FIELDS,
    SettingsError,
    SharedSettingsClient,
    operation_id,
    snapshot_response,
)

FIXTURES = Path(__file__).parent / "fixtures" / "shared_settings"


def fixture(name="active"):
    return json.loads((FIXTURES / (name + ".json")).read_text())


def response(body, status=200):
    return SimpleNamespace(status_code=status, json=lambda: deepcopy(body))


@pytest.fixture
def owner(monkeypatch):
    cfg = Config(
        ha_url="http://ha.local:8123",
        paired=True,
        device_token="fixture-token",
        device_id="djconnect-raspberry-pi-0123456789ab",
    )
    get = Mock(return_value=response(fixture()))
    monkeypatch.setattr(requests, "get", get)
    return SharedSettingsClient(lambda: cfg), cfg, get


@pytest.mark.parametrize(
    "name", ["active", "defaults", "legacy_unknown", "unavailable_voice"]
)
def test_delivered_producer_snapshots_decode_without_changing_values(name):
    data = fixture(name)
    assert snapshot_response(data) == data


def test_uuid7_and_owner_read_have_exact_closed_identity(owner):
    client, cfg, get = owner
    cfg.explicit_profile_id = "not-authority"
    cfg.mood = 99
    state = client.read()
    assert UUID(operation_id()).version == 7
    assert get.call_args.kwargs["params"] == {
        "contract_version": 3,
        "device_id": cfg.device_id,
        "client_type": "raspberry_pi",
    }
    assert get.call_args.kwargs["headers"] == {
        "Authorization": "Bearer fixture-token",
        "Accept": "application/json",
    }
    assert "binding" not in state and "snapshot" not in state
    assert cfg.mood == 99


def test_legacy_unknown_mood_stays_a_proposal_and_requires_six_explicit_choices(
    owner, monkeypatch
):
    client, _, get = owner
    get.return_value = response(fixture("legacy_unknown"))
    patch = Mock()
    monkeypatch.setattr(requests, "patch", patch)
    state = client.read()
    assert state["selection_required"] is True
    assert state["active"] is True
    with pytest.raises(SettingsError, match="selection_required"):
        client.update({"voice": {"kind": "provider_default"}}, state["edit_token"])
    patch.assert_not_called()


def test_atomic_full_acceptance_captures_original_session_and_never_writes_local_config(
    owner, monkeypatch
):
    client, cfg, get = owner
    original = fixture("legacy_unknown")
    get.return_value = response(original)
    state = client.read()
    changes = deepcopy(state["values"])
    changes["presence"] = "music_only"
    sent = []

    def accept(url, **kwargs):
        sent.append(kwargs["json"])
        get.return_value = response(fixture())
        return response(
            {
                "success": True,
                "accepted": True,
                "operation_id": kwargs["json"]["operation_id"],
            }
        )

    monkeypatch.setattr(requests, "patch", accept)
    before = deepcopy(cfg.__dict__)
    client.update(changes, state["edit_token"])
    body = sent[0]
    assert set(body) == {
        "contract_version",
        "device_id",
        "client_type",
        "binding",
        "operation_id",
        "patch",
        "expected_defaults_revision",
        "expected_session",
    }
    assert set(body["patch"]) == FIELDS
    assert body["binding"] == original["binding"]
    assert (
        body["expected_defaults_revision"] == original["snapshot"]["defaults_revision"]
    )
    assert body["expected_session"] == {
        k: original["snapshot"]["session"][k]
        for k in ("session_id", "generation", "revision")
    }
    assert cfg.__dict__ == before


def test_no_session_patch_uses_null_session_and_only_the_explicit_field(
    owner, monkeypatch
):
    client, _, get = owner
    data = fixture("defaults")
    assert data["snapshot"]["session"] is None
    get.return_value = response(data)
    state = client.read()
    patch = Mock(
        side_effect=lambda *args, **kw: response(
            {
                "success": True,
                "accepted": True,
                "operation_id": kw["json"]["operation_id"],
            }
        )
    )
    monkeypatch.setattr(requests, "patch", patch)
    client.update({"mood": "party"}, state["edit_token"])
    assert patch.call_args.kwargs["json"]["expected_session"] is None
    assert patch.call_args.kwargs["json"]["patch"] == {"mood": "party"}


def test_draft_never_transfers_to_successor_session_after_background_read(
    owner, monkeypatch
):
    client, _, get = owner
    old = client.read()
    successor = fixture()
    successor["snapshot"]["session"]["generation"] = "successor"
    get.return_value = response(successor)
    client.read()
    patch = Mock()
    monkeypatch.setattr(requests, "patch", patch)
    with pytest.raises(SettingsError, match="conflict"):
        client.update({"mood": "party"}, old["edit_token"])
    patch.assert_not_called()


def test_lost_patch_response_is_resolved_once_and_current_read_wins_over_old_receipt(
    owner, monkeypatch
):
    client, _, get = owner
    state = client.read()
    patch = Mock(side_effect=requests.Timeout())
    monkeypatch.setattr(requests, "patch", patch)

    def receipt(url, **kwargs):
        oid = kwargs["json"]["operation_id"]
        current = fixture()
        current["snapshot"]["session"]["settings"]["presence"] = "presenter"
        get.return_value = response(current)
        return response(
            {
                "success": True,
                "contract_version": 3,
                "phase": "accepted",
                "receipt": {
                    "accepted": True,
                    "operation_id": oid,
                    "snapshot": fixture()["snapshot"],
                },
            }
        )

    post = Mock(side_effect=receipt)
    monkeypatch.setattr(requests, "post", post)
    result = client.update({"presence": "talkative"}, state["edit_token"])
    assert result["values"]["presence"] == "presenter"
    assert patch.call_count == 1
    assert (
        post.call_args.kwargs["json"]["operation_id"]
        == patch.call_args.kwargs["json"]["operation_id"]
    )
    assert get.call_count == 2


def test_unresolved_operation_never_issues_a_second_patch(owner, monkeypatch):
    client, _, _ = owner
    state = client.read()
    patch = Mock(side_effect=requests.Timeout())
    monkeypatch.setattr(requests, "patch", patch)
    monkeypatch.setattr(
        requests,
        "post",
        Mock(
            return_value=response(
                {"success": True, "contract_version": 3, "phase": "not_accepted"}
            )
        ),
    )
    with pytest.raises(SettingsError, match="uncertain"):
        client.update({"mood": "party"}, state["edit_token"])
    current = client.read()
    assert current["operation_pending"] is True
    with pytest.raises(SettingsError, match="uncertain"):
        client.update({"mood": "chill"}, current["edit_token"])
    assert patch.call_count == 1


@pytest.mark.parametrize(
    "status,category",
    [(401, "denied"), (403, "denied"), (409, "conflict"), (426, "unsupported")],
)
def test_denial_and_conflict_require_readback_and_do_not_clear_pairing(
    owner, monkeypatch, status, category
):
    client, cfg, get = owner
    state = client.read()
    patch = Mock(return_value=response({"success": False}, status))
    monkeypatch.setattr(requests, "patch", patch)
    with pytest.raises(SettingsError, match=category):
        client.update({"mood": "party"}, state["edit_token"])
    assert cfg.paired and cfg.device_token == "fixture-token"
    assert client.projection() == {}
    assert patch.call_count == 1 and get.call_count == 1


def test_reassigned_identity_during_read_never_exposes_old_settings(owner):
    client, cfg, get = owner

    def reassign(*args, **kwargs):
        cfg.active_profile_id = "new-profile"
        return response(fixture())

    get.side_effect = reassign
    with pytest.raises(SettingsError, match="denied"):
        client.read()
    assert client.projection() == {}


def test_unavailable_saved_output_and_voice_are_not_rewritten(owner):
    client, _, get = owner
    data = fixture("unavailable_voice")
    get.return_value = response(data)
    state = client.read()
    expected = (data["snapshot"]["session"] or {}).get("settings") or data["snapshot"][
        "defaults"
    ]
    assert state["values"] == expected
    assert state["voice_available"] is False


def test_ha_legacy_numeric_mood_and_output_are_absent_after_shared_adoption(owner):
    _, cfg, _ = owner
    cfg.mood = 75
    ha = HAClient(cfg)
    ha.shared_settings.managed = True
    assert "mood" not in ha._base_payload()
    assert "X-DJConnect-Mood" not in ha._headers()
    assert "mood" not in ha._ask_dj_payload()
    assert "dj_announcement_output" not in ha._ask_dj_payload()


@pytest.mark.parametrize(
    "field,value",
    [
        ("ha_speaker", "media_player.private"),
        ("pipeline", "private"),
        ("profile_id", "another"),
        ("autoplay", True),
    ],
)
def test_ha_only_and_profile_authority_fields_cannot_be_patched(owner, field, value):
    client, _, _ = owner
    state = client.read()
    with pytest.raises(SettingsError, match="rejected"):
        client.update({field: value}, state["edit_token"])


def test_paired_startup_never_forwards_legacy_choices_before_first_owner_read():
    cfg = Config(
        paired=True,
        ha_url="http://ha",
        device_token="fixture",
        mood=95,
        dj_announcement_output="ha_speaker",
    )
    client = HAClient(cfg)
    assert client.shared_settings.managed is False
    assert "mood" not in client._base_payload()
    assert "mood" not in client._ask_dj_payload()
    assert "dj_announcement_output" not in client._ask_dj_payload()
    assert "X-DJConnect-Mood" not in client._headers()


def test_malformed_patch_response_is_resolved_by_receipt_without_replaying(
    owner, monkeypatch
):
    client, _, _ = owner
    state = client.read()
    malformed = SimpleNamespace(
        status_code=200, json=Mock(side_effect=ValueError("private body"))
    )
    patch = Mock(return_value=malformed)
    monkeypatch.setattr(requests, "patch", patch)

    def accepted(url, **kwargs):
        return response(
            {
                "success": True,
                "contract_version": 3,
                "phase": "accepted",
                "receipt": {
                    "accepted": True,
                    "operation_id": kwargs["json"]["operation_id"],
                },
            }
        )

    receipt = Mock(side_effect=accepted)
    monkeypatch.setattr(requests, "post", receipt)
    assert client.update({"presence": "talkative"}, state["edit_token"])["values"]
    assert patch.call_count == receipt.call_count == 1



def test_settings_read_rejects_scope_revoke_regrant_even_when_owner_is_same(owner):
    client, cfg, get = owner
    scope = ["profile-owner", True, 1]
    client.owner_context = lambda: tuple(scope)
    original = client.context()
    def delayed(*args, **kwargs):
        scope[2] += 2
        return response(fixture())
    get.side_effect = delayed
    with pytest.raises(SettingsError, match="denied"):
        client.read()
    assert client.context() != original
    assert cfg.active_profile_id == ""
    assert "owner_context" not in get.call_args.kwargs["params"]
