# Shared page toolbars

Pinned Apple UI e106a467 DJConnectRootView.swift places refresh/connection at
the trailing action edge, Queue/Playlist search separately at leading, and Ask
DJ clear with leading feature controls. Large iPad navigation titles sit below
action chrome. Glass capsules group actions; there is no single glass slab
behind the entire heading.

PageToolbar.qml applies this structure to existing Pi actions: a large title
below separated leading/trailing groups on tablet, one compact title/action row
below 900px. Existing refresh callbacks, busy/disabled predicates and accessible
names remain. The added connection button opens only the same connectionType
text already exposed by the Session information pop-out; it makes no backend
call. Leaving a page closes the local pop-out synchronously. All new labels use
existing five-locale keys. No new server, media, playback or lifecycle command.

| Pages | Current shared source |
| --- | --- |
| Now Playing, Track Insight, Discover, Music DNA | Trailing connection/refresh with existing busy state |
| Ask DJ | Existing confirmed clear action leading; connection/refresh trailing |
| Queue, Playlists | Trailing connection/refresh; existing list actions unchanged |
| Control | Existing refresh plus read-only connection |
| More, Settings, Games | Shared title chrome; no invented feature buttons |
| About | Shared title and local Close; header pinned above its scroll area |
| Legal, Privacy, Feedback | Existing More/back action leading; title below on tablet |
| DJ Session/current/saved history | Existing specialized grouped Session toolbar preserved |

Settings title is also pinned above its scroll area. Shared Glass preference,
Pi profile defaults, Inter, Mood/artwork tint and interaction feedback apply.
Empty groups are omitted. Primary page content and existing bottom navigation
remain separate from the header.

This is structural/material alignment of existing Pi actions, not completion of
all Apple feature affordances. Missing Ask DJ search, Queue/Playlist search,
Track Insight share/standalone Mood controls and other absent Apple actions
remain explicit functional gaps. Log/update/pairing/startup/confirmation utility
flows retain their existing dedicated chrome. Native SF geometry, native Liquid
Glass and physical/full-app GPU acceptance are not claimed. The official EADB
rc.5 installation is unchanged; this is a distinct rc.6 source candidate.
