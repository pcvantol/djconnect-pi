"""Read-only search/navigation and attribution presentation over Core history2."""
from copy import deepcopy
from html import escape
from importlib.resources import files
from urllib.parse import urlsplit

from .session_projection import history_page, live_moments, safe_link, text
from .session_transport import SessionError, identifier


def page_cursor(value):
    if value is None or value == "":
        return ""
    if not isinstance(value, str) or len(value) > 8192 or any(ord(c) < 32 for c in value):
        raise SessionError("invalid")
    return value


def sources(subject):
    """Keep supplied attribution, including original revision and previous URLs."""
    result = []
    raw = []
    for key in ("source_attribution", "qualified_fact_attribution"):
        item = subject.get(key)
        if item:
            raw.append(item)
    extra = subject.get("sources", [])
    if not isinstance(extra, list) or len(extra) > 16:
        raise SessionError("invalid")
    for item in raw + extra:
        if not isinstance(item, dict):
            raise SessionError("invalid")
        provider, license = text(item.get("provider"), 256), text(item.get("license"), 256)
        links = []
        for key in ("url", "revision_url", "url_previous"):
            if item.get(key):
                value = safe_link(item[key])
                if not value:
                    raise SessionError("invalid")
                if value not in links:
                    links.append(value)
        row = {"provider": provider, "license": license, "links": links}
        if row not in result:
            result.append(row)
    return result


def presented_history(response):
    result = deepcopy(response)
    for row in result.get("entries", []):
        row["display_sources"] = sources(row)
        row["spotify_source_url"] = spotify_source(row)
    return result


def _highlighted_text(body, marks):
    # Called only after server UTF-16 ranges passed exact character-boundary validation.
    indices = {0: 0}
    offset = 0
    for index, char in enumerate(body):
        offset += len(char.encode("utf-16-le")) // 2
        indices[offset] = index + 1
    spans = sorted((indices[mark["start_utf16"]], indices[mark["start_utf16"] + mark["length_utf16"]]) for mark in marks)
    merged = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    fragments = []
    previous = 0
    for start, end in merged:
        fragments.extend((escape(body[previous:start]), "<b><u>", escape(body[start:end]), "</u></b>"))
        previous = end
    fragments.append(escape(body[previous:]))
    # The only generated tags are emphasis and line breaks. User markup stays literal.
    return "".join(fragments).replace("\n", "<br>")


def search_page(response, session_id, query, *, now=None):
    if (not isinstance(response, dict) or response.get("session_id") != session_id
            or response.get("query") != query or not isinstance(response.get("revision"), str)
            or not response["revision"] or type(response.get("complete")) is not bool):
        raise SessionError("invalid")
    matches = response.get("matches")
    if not isinstance(matches, list) or type(response.get("returned_count")) is not int or response["returned_count"] != len(matches):
        raise SessionError("invalid")
    history_page({**response, "session": {"session_id": session_id}, "entries": matches}, session_id=session_id, now=now)
    cursor = page_cursor(response.get("next_cursor"))
    if response["complete"] == bool(cursor):
        raise SessionError("invalid")
    total = response.get("total_count")
    if total is not None and (type(total) is not int or total < len(matches) or not response["complete"]):
        raise SessionError("invalid")
    for row in matches:
        marks = row.get("highlights")
        body = text(row.get("text"))
        if not isinstance(marks, list) or not 1 <= len(marks) <= 100:
            raise SessionError("invalid")
        boundaries = {0}
        offset = 0
        for char in body:
            offset += len(char.encode("utf-16-le")) // 2
            boundaries.add(offset)
        for mark in marks:
            if (not isinstance(mark, dict) or type(mark.get("start_utf16")) is not int
                    or type(mark.get("length_utf16")) is not int or mark["length_utf16"] <= 0
                    or mark["start_utf16"] not in boundaries
                    or mark["start_utf16"] + mark["length_utf16"] not in boundaries):
                raise SessionError("invalid")
    result = deepcopy(response)
    result["matches"] = presented_history({"entries": matches})["entries"]
    for row in result["matches"]:
        row["highlighted_text"] = _highlighted_text(row["text"], row["highlights"])
    return result


def opened_entry(response, session_id, entry_id, *, now=None):
    if (not isinstance(response, dict) or response.get("navigation_only") is not True
            or type(response.get("read_only")) is not bool):
        raise SessionError("invalid")
    entry = response.get("entry")
    if not isinstance(entry, dict) or entry.get("entry_id") != identifier(entry_id):
        raise SessionError("invalid")
    history_page({**response, "revision": response.get("session", {}).get("revision"), "entries": [entry]}, session_id=session_id, now=now)
    return response


def live_presentations(session, *, now=None):
    result = []
    for card in live_moments(session, now=now, spotify_attribution_available=files("djconnect_pi.qml").joinpath("spotify-attribution.png").is_file()):
        raw = next(row for row in session["broadcast"]["dj_moments"] if isinstance(row, dict) and row.get("moment_id") == card["moment_id"])
        try:
            card["display_sources"] = sources(raw)
            card["spotify_source_url"] = spotify_source({**raw, "requires_spotify_attribution": card["requires_spotify_attribution"]})
        except SessionError:
            continue
        result.append(card)
    return result


def spotify_source(subject):
    if subject.get("requires_spotify_attribution") is not True:
        return ""
    playback = subject.get("playback") or {}
    if not isinstance(playback, dict):
        raise SessionError("invalid")
    candidates = [playback.get("source_url")] + [url for row in sources(subject) for url in row["links"]]
    for candidate in candidates:
        value = safe_link(candidate)
        if value and urlsplit(value).hostname == "open.spotify.com":
            return value
    raise SessionError("invalid")


def accepted_question(response, binding, request):
    """Validate acceptance only; never turn transient media/actions into retained rights."""
    conversation = response.get("conversation")
    expected = {"session_id": request["session_id"]}
    selected = request.get("selected") or {}
    if selected:
        key = "entry_id" if selected["kind"] == "selected_entry" else "moment_id"
        expected[selected["kind"]] = {"session_id": selected["session_id"], key: selected[key]}
    if (response.get("success") is not True or response.get("owner_profile_id") != binding.resolved_profile_id
            or response.get("client_message_id") != request["client_message_id"]
            or not isinstance(conversation, dict) or type(conversation.get("schema_version")) is not int
            or conversation["schema_version"] != 1 or conversation.get("input_type") != "text"
            or conversation.get("context") != expected):
        raise SessionError("uncertain")
    try:
        identifier(conversation.get("turn_id"))
    except SessionError:
        raise SessionError("uncertain") from None
    entries = conversation.get("entry_ids")
    if not isinstance(entries, list) or len(entries) > 2 or len(set(map(str, entries))) != len(entries):
        raise SessionError("uncertain")
    try:
        for entry in entries:
            identifier(entry)
    except SessionError:
        raise SessionError("uncertain") from None
    return conversation


def conversation_entries(page):
    rows = []
    for row in page["entries"]:
        if row["kind"] not in {"conversation_user", "conversation_dj"}:
            continue
        expected_role = "user" if row["kind"] == "conversation_user" else "assistant"
        if (row.get("role") != expected_role or not isinstance(row.get("text"), str)
                or len(row["text"]) > 32768 or row.get("input_type") not in {"text", "voice"}):
            raise SessionError("invalid")
        identifier(row.get("turn_id"))
        rows.append(row)
    return presented_history({"entries": rows})["entries"]
