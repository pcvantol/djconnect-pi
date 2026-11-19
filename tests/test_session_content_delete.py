"""Synthetic original-scope consent and isolated HTTP seams; no real erasure."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import UTC, datetime

import pytest
from test_session_history_delete import NOW, OP

from djconnect_pi import session_content_delete as content
from djconnect_pi.session_transport import SessionError

pytest_plugins = ["test_session_history_delete"]

CAPS = {
    "capabilities": {"session_content_delete": True},
    "contract_versions": {"session_content_delete": 1},
}
TARGET = {"kind": "entry", "session_id": "saved", "target_id": "entry-original"}


def preview(binding, **changes):
    data = {
        "success": True,
        "schema_version": 1,
        "owner_profile_id": binding.profile_id,
        "target": TARGET,
        "confirmation_id": "confirmation-original",
        "created_at": datetime.fromtimestamp(NOW, UTC).isoformat(),
        "expires_at": datetime.fromtimestamp(NOW + 300, UTC).isoformat(),
        "unit": {
            "kind": "exchange",
            "session_id": "saved",
            "target_id": "exchange-original",
        },
        "affected_entries": [
            {
                "session_id": "saved",
                "entry_id": "entry-original",
                "disposition": "remove",
            },
            {
                "session_id": "saved",
                "entry_id": "dependent",
                "disposition": "unavailable",
            },
        ],
        "removed_message_ids": ["user-message", "dj-message"],
        "unavailable_message_ids": ["dependent-message"],
        "affected_moments": [],
        "fenced_request_count": 1,
        "music_playback_undone": False,
    }
    data.update(changes)
    return data


def intent(wire, monkeypatch):
    client, _, _, _ = wire
    monkeypatch.setattr(content, "operation_id", lambda: OP)
    p = content.ContentPreview.parse(
        preview(client.binding()), client.binding(), content.target(TARGET), now=NOW
    )
    return content.ContentIntent.confirmed(p, 4, CAPS, now=NOW, confirmed=True)


def receipt(i):
    p = i.preview
    return {
        "success": True,
        "schema_version": 1,
        "state": "completed",
        "deleted": True,
        "owner_profile_id": p.binding.profile_id,
        "operation_id": i.operation,
        "confirmation_id": p.confirmation,
        "request_digest": i.digest,
        "unit": content.wire_target(p.unit),
        "affected_entries": [
            dict(zip(("session_id", "entry_id", "disposition"), row, strict=True))
            for row in p.entries
        ],
        "removed_message_ids": list(p.removed),
        "unavailable_message_ids": list(p.unavailable),
        "music_playback_undone": False,
    }


def test_prepare_has_closed_identity_no_implicit_profile_and_no_uuid(wire):
    client, cfg, request, response = wire
    cfg.private_session = True
    response.body = preview(client.binding())
    client.prepare_content_delete(client.binding(), TARGET)
    body = request.call_args.kwargs["json"]
    assert body == {
        "device_id": cfg.device_id,
        "client_type": "raspberry_pi",
        "contract_version": 1,
        "target": TARGET,
    }
    assert (
        request.call_args.kwargs["headers"]["X-DJConnect-Profile-ID"]
        == cfg.active_profile_id
    )
    assert request.call_args.kwargs["allow_redirects"] is False
    assert request.call_args.kwargs["stream"] is True
    response.json.assert_not_called()
    response.close.assert_called_once()


def test_one_confirmed_post_exact_receipt_does_not_require_prepare_only_fields(
    wire, monkeypatch
):
    client, _, request, response = wire
    i = intent(wire, monkeypatch)
    values = i.claim(client.binding(), 4, CAPS, now=NOW)
    response.body = receipt(i)
    client.delete_content(client.binding(), i, values)
    assert request.call_count == 1
    assert request.call_args.args[1].endswith("/session/content/delete")
    assert request.call_args.kwargs["json"] == {
        **values,
        "device_id": client.binding().device_id,
        "client_type": "raspberry_pi",
    }
    with pytest.raises(SessionError, match="uncertain"):
        i.claim(client.binding(), 4, CAPS, now=NOW)


@pytest.mark.parametrize(
    "state", ["unknown", "pending", "expired_unknown", "completed"]
)
def test_original_readonly_status_without_post_or_renewal(wire, monkeypatch, state):
    client, _, request, response = wire
    i = intent(wire, monkeypatch)
    response.body = {
        "success": True,
        "schema_version": 1,
        "owner_profile_id": i.preview.binding.profile_id,
        "state": state,
        "definitive": state == "completed",
        "operation_id": i.operation,
        "confirmation_id": i.preview.confirmation,
        "request_digest": i.digest,
    }
    if state == "completed":
        response.body["receipt"] = receipt(i)
    assert client.content_delete_status(client.binding(), i) == state
    assert request.call_count == 1 and request.call_args.args[0] == "GET"
    assert set(request.call_args.kwargs["params"]) == {
        "device_id",
        "client_type",
        "contract_version",
        "operation_id",
        "confirmation_id",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("success", 1),
        ("schema_version", True),
        ("owner_profile_id", "foreign"),
        ("target", {**TARGET, "target_id": "other"}),
        ("confirmation_id", ""),
        ("unit", {"kind": "exchange", "session_id": "other", "target_id": "x"}),
        ("expires_at", "2099-01-01T00:00:00Z"),
        ("created_at", "2099-01-01T00:00:00Z"),
        ("fenced_request_count", True),
        ("fenced_request_count", -1),
        ("fenced_request_count", 1001),
        (
            "affected_entries",
            [{"session_id": "saved", "entry_id": "x", "disposition": "unknown"}],
        ),
        ("removed_message_ids", ["same", "same"]),
        ("unavailable_message_ids", ["dj-message"]),
        ("music_playback_undone", True),
    ],
)
def test_preview_rejects_wrong_original_scope(wire, field, value):
    client, _, _, _ = wire
    with pytest.raises(SessionError):
        content.ContentPreview.parse(
            preview(client.binding(), **{field: value}),
            client.binding(),
            content.target(TARGET),
            now=NOW,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("state", "pending"),
        ("deleted", 1),
        ("schema_version", True),
        ("owner_profile_id", "foreign"),
        ("operation_id", "new"),
        ("confirmation_id", "renewed"),
        ("request_digest", "other"),
        ("affected_entries", []),
        ("removed_message_ids", []),
        ("unavailable_message_ids", []),
        ("music_playback_undone", True),
    ],
)
def test_wrong_receipt_never_confirms_completion(wire, monkeypatch, field, value):
    i = intent(wire, monkeypatch)
    data = receipt(i)
    data[field] = value
    with pytest.raises(SessionError):
        i.receipt(data)


@pytest.mark.parametrize("value", [False, 1, None, "true"])
def test_capability_is_not_a_truthy_grant(value):
    data = deepcopy(CAPS)
    data["capabilities"]["session_content_delete"] = value
    assert not content.supported(data)


def test_original_deadline_and_atomic_claim(wire, monkeypatch):
    i = intent(wire, monkeypatch)
    binding = i.preview.binding

    def claim(_):
        try:
            return i.claim(binding, 4, CAPS, now=NOW)
        except SessionError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(v is not None for v in pool.map(claim, range(16))) == 1
    expired = intent(wire, monkeypatch)
    with pytest.raises(SessionError):
        expired.claim(binding, 4, CAPS, now=NOW + 300)


@pytest.mark.parametrize("status", [401, 403])
def test_denial_before_any_json_body(wire, status):
    client, _, request, response = wire
    response.status_code = status
    with pytest.raises(SessionError, match="denied"):
        client.prepare_content_delete(client.binding(), TARGET)
    assert request.call_count == 1
    response.iter_content.assert_not_called()


def test_closed_route_cannot_be_used_as_arbitrary_effect(wire):
    client, _, request, _ = wire
    with pytest.raises(SessionError):
        client._request(
            client.binding(),
            "POST",
            "command",
            {"contract_version": 1, "target": TARGET},
            content_delete=True,
        )
    request.assert_not_called()


@pytest.mark.parametrize("value", [1, "true", False, None])
def test_confirmation_is_exact_boolean_before_transport(wire, monkeypatch, value):
    client, _, request, _ = wire
    i = intent(wire, monkeypatch)
    values = {
        "contract_version": 1,
        "confirmation_id": i.preview.confirmation,
        "operation_id": i.operation,
        "confirmed": value,
    }
    with pytest.raises(SessionError):
        client.delete_content(client.binding(), i, values)
    request.assert_not_called()
