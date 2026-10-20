"""Closed, ephemeral Session projections. Historical rows never become live grants."""
from __future__ import annotations

from datetime import UTC, datetime
from itertools import pairwise
from urllib.parse import urlsplit

from .session_transport import SessionError, identifier

HISTORY_KINDS = {"playback_observed", "dj_moment", "conversation_user", "conversation_dj", "dj_publication", "dj_silence"}
ARCHIVE_BASES = {"cc0_normalized_fields_v1", "runtime_authored_direction_v1", "owner_metadata_narration_v1", "public_artist_narration_v1"}


def timestamp(value):
    try:
        result = datetime.fromisoformat(value)
        if result.tzinfo is None:
            return None
        return result.timestamp()
    except (AttributeError, ValueError, TypeError):
        return None


def safe_link(value):
    if not isinstance(value, str) or len(value) > 4096 or any(c.isspace() or ord(c) < 32 for c in value):
        return ""
    try:
        url = urlsplit(value)
        return value if url.scheme == "https" and url.hostname and not url.username and not url.password else ""
    except ValueError:
        return ""


def text(value, maximum=32768):
    return value if isinstance(value, str) and len(value) <= maximum else ""


def active_session(response):
    if not isinstance(response, dict) or response.get("success") is not True:
        raise SessionError("invalid")
    session = response.get("session")
    if session is None:
        return {}
    if not isinstance(session, dict):
        raise SessionError("invalid")
    session_id = identifier(session.get("session_id"))
    if not isinstance(session.get("runtime_state"), str) or session.get("runtime_state") not in {"opening", "active", "ending", "ended", "interrupted"}:
        raise SessionError("invalid")
    broadcast = session.get("broadcast")
    if not isinstance(broadcast, dict) or not isinstance(broadcast.get("session"), dict) or broadcast["session"].get("session_id") != session_id:
        raise SessionError("invalid")
    if session["runtime_state"] in {"ended", "interrupted"}:
        return {}
    return session


def session_playback(session):
    """Only the current Runtime's renderer-safe observation, never global/history data."""
    if not session or session.get("runtime_state") != "active":
        return {}
    snapshot = session.get("broadcast")
    if (not isinstance(snapshot, dict) or not isinstance(snapshot.get("session"), dict)
            or snapshot["session"].get("session_id") != session.get("session_id")):
        return {}
    playback = snapshot.get("playback")
    if not isinstance(playback, dict) or playback.get("state") not in ("playing", "paused"):
        return {}
    if not text(playback.get("item_id"), 256) or timestamp(playback.get("updated_at")) is None:
        return {}
    source = playback.get("source_url")
    # Released Core emits either no source or one canonical Spotify track URL.
    if source is not None and not isinstance(source, str):
        return {}
    source = source or ""
    if source:
        parts = urlsplit(safe_link(source))
        track = parts.path.removeprefix("/track/")
        if (parts.hostname != "open.spotify.com" or parts.netloc != "open.spotify.com"
                or parts.query or parts.fragment or not parts.path.startswith("/track/")
                or len(track) != 22 or not track.isascii() or not track.isalnum()):
            return {}
    result = {key: text(playback.get(key), 256) for key in ("title", "artist", "album", "target_name")}
    if not any(result[key].strip() for key in ("title", "artist", "album")):
        return {}
    result.update(state=playback["state"], item_id=playback["item_id"], source_url=source,
                  requires_spotify_attribution=bool(source))
    duration, position = playback.get("duration_ms"), playback.get("position_ms")
    if type(duration) is int and duration > 0 and type(position) is int and position >= 0:
        current = min(position, duration)
        result.update(progress=current / duration,
                      time_label=f"{current // 60000}:{current // 1000 % 60:02d} / {duration // 60000}:{duration // 1000 % 60:02d}")
    return result


def live_moments(session, now=None, *, spotify_attribution_available=False):
    now = datetime.now(UTC).timestamp() if now is None else now
    if not session or session.get("runtime_state") != "active":
        return []
    session_id = session["session_id"]
    snapshot = session.get("broadcast", {})
    authority = snapshot.get("native_delivery")
    if not isinstance(authority, dict) or authority.get("schema_version") != 1 or authority.get("session_id") != session_id or authority.get("revocation_scope") != "session" or not authority.get("revision"):
        return []
    current_id = authority.get("current_moment_id")
    if current_id is not None and not isinstance(current_id, str):
        return []
    if not isinstance(authority.get("revision"), str) or type(authority.get("schema_version")) is not int:
        return []
    if not isinstance(snapshot.get("dj_moments"), list) or len(snapshot["dj_moments"]) > 512:
        return []
    if not isinstance(authority.get("admissions"), list) or len(authority["admissions"]) > 512:
        return []
    flow_object = snapshot.get("session_flow")
    if not isinstance(flow_object, dict) or not isinstance(flow_object.get("items"), list):
        return []
    # The original server order is preserved. No sorting or locally invented Flow.
    flow = flow_object["items"]
    flow_ids = [item.get("moment_id") for item in flow if isinstance(item, dict) and item.get("item_type") == "dj_moment"]
    admitted_flow = authority.get("active_flow_moment_ids", [])
    if not isinstance(admitted_flow, list) or len(admitted_flow) > 512 or any(not isinstance(value, str) for value in admitted_flow):
        return []
    ids = ([current_id] if current_id else []) + [value for value in admitted_flow if value in flow_ids and value != current_id]
    result = []
    for moment_id in dict.fromkeys(ids):
        matches = [a for a in authority.get("admissions", []) if isinstance(a, dict) and a.get("moment_id") == moment_id]
        moments = [m for m in snapshot.get("dj_moments", []) if isinstance(m, dict) and m.get("moment_id") == moment_id]
        if len(matches) != 1 or len(moments) != 1:
            continue
        grant, moment = matches[0], moments[0]
        if type(grant.get("requires_spotify_attribution", False)) is not bool:
            continue
        current = moment_id == current_id
        if grant.get("qualification") != "qualified" or grant.get("executable_actions") != [] or grant.get("current_display_allowed" if current else "active_flow_display_allowed") is not True:
            continue
        if moment.get("session_id") != session_id or not text(moment.get("content")):
            continue
        intent = moment.get("presentation_intent")
        if not isinstance(intent, dict) or not isinstance(intent.get("visibility"), str) or intent.get("visibility") not in {"owner_only", "session_shared", "public_broadcast"}:
            continue
        if "source_expires_at" not in grant or "display_expires_at" not in grant:
            continue
        source_expiry = timestamp(grant.get("source_expires_at"))
        display_expiry = timestamp(grant.get("display_expires_at"))
        if grant.get("source_expires_at") is not None and (source_expiry is None or now >= source_expiry):
            continue
        if current and (display_expiry is None or now >= display_expiry):
            continue
        attribution = moment.get("source_attribution") or {}
        if not isinstance(attribution, dict):
            continue
        links = [safe_link(attribution.get(key)) for key in ("url", "url_previous") if attribution.get(key)]
        if any(not value for value in links):
            continue
        if grant.get("requires_spotify_attribution") and (not spotify_attribution_available or not current or not links or not any(urlsplit(value).hostname == "open.spotify.com" for value in links)):
            continue
        result.append({"moment_id": moment_id, "title": text(moment.get("title"), 512),
            "body": moment["content"], "current": current, "source_links": links,
            "source_provider": text(attribution.get("provider"), 128),
            "source_license": text(attribution.get("license"), 256),
            "requires_spotify_attribution": grant.get("requires_spotify_attribution") is True,
            "display_expires_at": grant.get("display_expires_at"),
            "source_expires_at": grant.get("source_expires_at")})
    return result


def history_page(response, *, session_id=None, now=None):
    now = datetime.now(UTC).timestamp() if now is None else now
    if not isinstance(response, dict) or response.get("success") is not True or response.get("schema_version") != 2 or response.get("history_contract_version") != 2:
        raise SessionError("invalid")
    if session_id is None:
        sessions = response.get("sessions")
        if not isinstance(sessions, list) or len(sessions) > 50:
            raise SessionError("invalid")
        ids = set()
        for header in sessions:
            if not isinstance(header, dict) or not isinstance(header.get("revision"), str) or not header["revision"]:
                raise SessionError("invalid")
            value = identifier(header.get("session_id"))
            if value in ids:
                raise SessionError("invalid")
            ids.add(value)
        return response
    header = response.get("session")
    if not isinstance(header, dict) or header.get("session_id") != session_id:
        raise SessionError("invalid")
    if not isinstance(response.get("revision"), str) or not response["revision"]:
        raise SessionError("invalid")
    # Cursors are opaque, but malformed values must never become navigation state.
    cursor = response.get("next_cursor")
    if cursor is not None and (not isinstance(cursor, str) or not cursor or len(cursor) > 8192 or any(ord(c) < 32 for c in cursor)):
        raise SessionError("invalid")
    entries = response.get("entries")
    if not isinstance(entries, list) or len(entries) > 50:
        raise SessionError("invalid")
    seen = set()
    for row in entries:
        if not isinstance(row, dict):
            raise SessionError("invalid")
        entry_id = identifier(row.get("entry_id"))
        if (row.get("session_id") != session_id or entry_id in seen
                or type(row.get("order")) is not int or row["order"] < 0
                or not isinstance(row.get("kind"), str) or row["kind"] not in HISTORY_KINDS):
            raise SessionError("invalid")
        seen.add(entry_id)
        deadline = timestamp(row.get("retained_until"))
        if deadline is None or deadline <= now or timestamp(row.get("occurred_at")) is None:
            raise SessionError("unavailable")
        if row.get("historical_view_only") is not True or row.get("current_display_allowed") is not False:
            raise SessionError("invalid")
        if row["kind"] == "dj_moment" and (not isinstance(row.get("archive_basis"), str) or row["archive_basis"] not in ARCHIVE_BASES):
            raise SessionError("invalid")
        if row["kind"] in {"dj_publication", "dj_silence"} and (row.get("text") is not None or row.get("speech_available") is not False):
            raise SessionError("invalid")
    if any(a["order"] >= b["order"] for a, b in pairwise(entries)):
        raise SessionError("invalid")
    return response
