"""Read-only presentation of Core's private saved-session summary."""
from .session_projection import timestamp


def saved_session_summary(timeline):
    header = timeline.get("session", {})
    revision = timeline.get("revision")
    if not isinstance(revision, str) or not revision or header.get("revision") != revision:
        return []
    return archive_session_summary(header)


def archive_session_summary(header):
    revision = header.get("revision")
    summary = header.get("summary")
    if (header.get("read_only") is not True
            or header.get("lifecycle_status") not in ("ENDED", "INTERRUPTED")
            or not (isinstance(revision, str) and revision or type(revision) is int and revision >= 0)
            or not isinstance(summary, dict)
            or summary.get("schema_version") != "djconnect-session-history-summary/1"
            or type(summary.get("session_revision")) is not type(revision)
            or summary.get("session_revision") != revision or summary.get("state") != "final"):
        return []
    as_of = summary.get("as_of")
    if timestamp(as_of) is None:
        return []

    definitions = [
        ("tracks_observed", "accepted_playback_observed_entries", "session_summary_tracks"),
        ("moments_published", "semantic_publication_commit", "session_summary_moments"),
        ("mood", "confirmed_symbolic_mood_elapsed_intervals", "session_summary_mood"),
    ]
    if summary.get("moments_retained") is not None:
        definitions.insert(2, ("moments_retained", "retained_readable_entries", "session_summary_retained"))

    result = []
    for key, basis, label in definitions:
        metric = summary.get(key)
        if (not isinstance(metric, dict) or "value" not in metric or metric.get("basis") != basis
                or metric.get("state") != "final" or type(metric.get("revision")) is not type(revision)
                or metric.get("revision") != revision or metric.get("as_of") != as_of):
            return []
        value, coverage = metric["value"], metric.get("coverage")
        if key == "tracks_observed" and metric.get("observation_scope") != "stage_1_media_identity_changes_not_occurrences":
            return []
        if coverage in ("unknown", "withdrawn"):
            if value is not None:
                return []
        elif key == "mood":
            if coverage == "complete":
                if value not in ("chill", "groove", "energy", "party", "mixed"):
                    return []
            elif coverage != "partial" or value is not None:
                return []
        elif coverage not in ("complete", "partial") or type(value) is not int or not 0 <= value <= 2**53 - 1:
            return []
        result.append({"label": label, "value": value, "coverage": coverage})
    return result
