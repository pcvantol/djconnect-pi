"""Narrow current-response text projection; never historical or executable rights."""
import hashlib
import json

from .session_history_view import accepted_question, live_presentations, sources
from .session_projection import timestamp
from .session_transport import SessionError


def moment_reference(session, selected, *, now):
    if selected.get("kind") != "selected_moment" or selected.get("session_id") != session.get("session_id"):
        return {}
    moment = next((m for m in live_presentations(session, now=now) if m["moment_id"] == selected.get("moment_id")), None)
    if not moment:
        return {}
    deadlines = [timestamp(moment.get(k)) for k in ("source_expires_at", "display_expires_at") if moment.get(k) is not None]
    if not deadlines or any(value is None or value <= now for value in deadlines):
        return {}
    style = {key: session.get(key) for key in ("selected_mood", "selected_presence", "dj_persona", "persona_revision")}
    signature = hashlib.sha256(json.dumps([moment, style, session.get("broadcast", {}).get("native_delivery", {}).get("revision")], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"signature": signature, "deadline": min(deadlines), "selected": selected,
        "requires_spotify_attribution": moment["requires_spotify_attribution"], "spotify_source_url": moment.get("spotify_source_url", "")}


def current_reply(response, binding, request, session, *, now):
    receipt = accepted_question(response, binding, request)
    if receipt.get("history_scope") != "private_ephemeral" or receipt["entry_ids"] != [] or response.get("history_persisted") is not False:
        return {}
    reference = moment_reference(session, request.get("selected") or {}, now=now)
    if not reference or reference != request.get("live_reference"):
        return {}
    assistant = response.get("assistant_message")
    body = response.get("text")
    if (response.get("error") is not None or not isinstance(assistant, dict) or assistant.get("role") != "assistant"
            or not isinstance(body, str) or not body.strip() or len(body) > 32768 or assistant.get("text") != body
            or response.get("is_generated_text") is not True or response.get("text_source") != "generated"
            or response.get("model_processing_basis") != "qualified_dialogue_v1"
            or receipt.get("model_source_basis") != "cc0_normalized_fields_v1"):
        raise SessionError("invalid")
    attribution = sources(response)
    if not attribution or any(row["provider"] != "MusicBrainz" or row["license"] != "CC0-1.0" or not row["links"] for row in attribution):
        raise SessionError("invalid")
    return {"text": body, "reply_id": receipt["turn_id"], "session_id": request["session_id"],
        "reference": reference, "display_sources": attribution,
        "requires_spotify_attribution": reference["requires_spotify_attribution"], "spotify_source_url": reference["spotify_source_url"]}


def reply_valid(reply, session, *, now):
    return (bool(reply) and bool(reply.get("reference")) and reply.get("session_id") == session.get("session_id")
        and reply.get("reference") == moment_reference(session, reply.get("reference", {}).get("selected", {}), now=now))
