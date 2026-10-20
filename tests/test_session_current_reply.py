"""Synthetic native grant + unchanged released response prose; no live/model calls."""
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

import pytest
from test_session_composer import setup_composer
from test_session_controller import clock_fixture

from djconnect_pi.session_current_reply import current_reply, moment_reference
from djconnect_pi.session_projection import timestamp

pytest_plugins = ["test_session_controller"]


def setup_reply(owner):
    setup_composer(owner)
    host = clock_fixture(owner)
    fixture = next(row for row in json.loads((Path(__file__).parent / "fixtures/session_core/contextual-dialogue-v1.json").read_text())["fixtures"] if row["case"] == "active-credit")
    def answer(binding, request):
        response = deepcopy(fixture["body"])
        response.update(owner_profile_id=binding.resolved_profile_id, client_message_id=request["client_message_id"])
        response["conversation"]["context"] = {"session_id": request["session_id"],
            "selected_moment": {"session_id": request["session_id"], "moment_id": request["selected"]["moment_id"]}}
        return response
    owner.transport.question = Mock(side_effect=answer)
    owner.selectMoment("s1", "m1")
    return host, fixture, answer


def send(owner, backend):
    assert owner.sendQuestion("Who composed this?")
    backend.jobs.pop()()


def test_selected_live_credit_renders_current_text_without_history_read_or_media(controller):
    owner, backend = controller
    _, fixture, _ = setup_reply(owner)
    before = owner.transport.timeline.call_count
    send(owner, backend)
    reply = owner.state["current_reply"]
    assert reply["text"] == fixture["body"]["text"]
    assert reply["question_text"] == "Who composed this?"
    assert reply["display_sources"][0]["license"] == "CC0-1.0"
    assert owner.state["question_status"] == "current_answer"
    assert owner.transport.timeline.call_count == before
    assert owner._question_receipt == {} and not owner.state["conversation"]
    assert set(reply) == {"text", "question_text", "reply_id", "session_id", "reference", "display_sources", "requires_spotify_attribution", "spotify_source_url"}


@pytest.mark.parametrize("mutation", ["revision", "style", "expiry", "withdrawal", "foreground", "new_question", "end"])
def test_current_reply_does_not_survive_source_or_scope_withdrawal(controller, mutation):
    owner, backend = controller
    host, _, _ = setup_reply(owner)
    send(owner, backend)
    assert owner.state["current_reply"]
    if mutation == "revision": owner._session["broadcast"]["native_delivery"]["revision"] = "r2"
    if mutation == "style": owner._session["selected_mood"] = "party"
    if mutation == "expiry": host.tick = 3600
    if mutation == "withdrawal": owner._session["broadcast"]["native_delivery"]["admissions"] = []
    if mutation == "foreground": owner.setForeground(False)
    if mutation == "new_question": owner.sendQuestion("Another question")
    if mutation == "end": owner.end("s1")
    owner._expire()
    assert not owner.state["current_reply"]


def test_gui_getter_expiry_still_notifies_next_tick_and_rollback_does_not_revive(controller):
    owner, backend = controller
    host, _, _ = setup_reply(owner)
    send(owner, backend)
    changed = Mock();owner.changed.connect(changed)
    host.tick = 3600
    assert not owner.state["current_reply"]
    assert owner._current_reply_dirty
    host.wall -= 10000
    owner._expire()
    assert changed.call_count and not owner.state["current_reply"]


def test_pending_reply_cannot_revive_after_observed_revision_changed_back(controller):
    owner, backend = controller
    _, _, answer = setup_reply(owner)
    def delayed(binding, request):
        owner._session["broadcast"]["native_delivery"]["revision"] = "r2";owner._expire()
        owner._session["broadcast"]["native_delivery"]["revision"] = "r1"
        return answer(binding, request)
    owner.transport.question.side_effect = delayed
    send(owner, backend)
    assert not owner.state["current_reply"] and not owner.state["conversation"]
    assert owner.transport.question.call_count == 1


@pytest.mark.parametrize("mutation", ["role", "text", "basis", "license", "owner", "receipt", "error"])
def test_malformed_or_unqualified_response_does_not_render(controller, mutation):
    owner, backend = controller
    _, _, answer = setup_reply(owner)
    def malformed(binding, request):
        response = answer(binding, request)
        if mutation == "error": response["error"] = "provider_failed"
        if mutation == "role": response["assistant_message"]["role"] = "system"
        if mutation == "text": response["assistant_message"]["text"] = "different"
        if mutation == "basis": response["conversation"]["model_source_basis"] = "raw_text"
        if mutation == "license": response["sources"][0]["license"] = "unknown"
        if mutation == "owner": response["owner_profile_id"] = "foreign"
        if mutation == "receipt": response["conversation"]["entry_ids"] = ["historical-id"]
        return response
    owner.transport.question.side_effect = malformed
    send(owner, backend)
    assert not owner.state["current_reply"]
    assert owner.state["question_status"] in {"uncertain", "accepted_unavailable"}


def test_live_reply_requires_original_finite_reference_and_retains_literal_prose(controller):
    owner, _ = controller
    _, _, answer = setup_reply(owner)
    request = {"text": "Literal <img> 🎧\nQuestion", "session_id": "s1", "client_message_id": "synthetic-reply", "selected": {"kind": "selected_moment", "session_id": "s1", "moment_id": "m1"}}
    request["live_reference"] = moment_reference(owner._session, request["selected"], now=owner._clock.now())
    response = answer(owner.transport.binding(), request)
    response["text"] = response["assistant_message"]["text"] = "Literal <img> 🎧\nCurrent text"
    projected = current_reply(response, owner.transport.binding(), request, owner._session, now=owner._clock.now())
    assert projected["text"] == response["text"]
    assert projected["question_text"] == request["text"]
    assert projected["reference"]["deadline"] == timestamp("2026-10-20T01:00:00Z")
    owner._session["broadcast"]["native_delivery"]["admissions"][0]["display_expires_at"] = "2026-10-20T02:00:00Z"
    assert not current_reply(response, owner.transport.binding(), request, owner._session, now=owner._clock.now())


@pytest.mark.parametrize("question", [None, True, "", "   ", "x" * 4001])
def test_current_response_rejects_missing_or_unbounded_local_question(controller, question):
    owner, _ = controller
    _, _, answer = setup_reply(owner)
    request = {"text": question, "session_id": "s1", "client_message_id": "synthetic-reply",
        "selected": {"kind": "selected_moment", "session_id": "s1", "moment_id": "m1"}}
    request["live_reference"] = moment_reference(owner._session, request["selected"], now=owner._clock.now())
    from djconnect_pi.session_transport import SessionError
    with pytest.raises(SessionError):
        current_reply(answer(owner.transport.binding(), request), owner.transport.binding(), request, owner._session, now=owner._clock.now())


def test_current_question_uses_exact_local_request_not_server_echo(controller):
    owner, backend = controller
    _, _, answer = setup_reply(owner)
    def foreign_echo(binding, request):
        response = answer(binding, request)
        response["user_message"] = {"role": "user", "text": "Foreign returned prompt"}
        return response
    owner.transport.question.side_effect = foreign_echo
    prompt = "Literal <img> 🎧\nLocal question"
    assert owner.sendQuestion(prompt)
    backend.jobs.pop()()
    shown = owner.state["current_reply"]
    assert shown["question_text"] == prompt
    shown["question_text"] = "Mutated GUI snapshot"
    assert owner.state["current_reply"]["question_text"] == prompt
    owner.setForeground(False)
    assert not owner.state["current_reply"]
