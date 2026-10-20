# Shared Pi Apple experience adoption

Owner request, 20 October 2026: bring the Apple experience to the Pi10, including
menus, pages, navigation, icon meanings, copy and server interactions. This is a
consumer implementation objective; visual alignment alone is not parity.

## Primary visual reference and current checkpoint

The owner selected **iPad in portrait**, not the wide Mac layout, as the primary
reference. Source inspection and a colour-only pass were insufficient. The next
visual implementation must follow actual portrait cards, glass buttons, effects,
spacing, page hierarchy and navigation, then map them to 1200x1920 Pi10.

The actual installed Mac app was viewed on 20 October: live DJ Session, Mood and
Presence segmented glass popovers, speech-preferences popover and Now Playing.
Private reference captures are under `/private/tmp/pi-apple-visual-reference`.
These prove Mac observations only. Device Hub sees the attached physical iPad Pro
on iPadOS26.7.1, but screen access currently says **Unlock Your iPad**. The available
repository iPad screenshot set is dated July and is deliberately not treated as a
current portrait reference. No device unlock, new pairing or Apple install occurs.

The colour work is **provisional WIP** in the isolated
`codex/pi-ipad-experience` branch; no new PR, merge, release or Pi install has
been performed. Its current checks pass (439 tests, 32 real QML page fixture views,
plus 40 localized shared-settings fixtures before final control refinements).
These checks do not qualify the owner-requested glass design or full parity.
Colour/Mood decisions and navigation layout must be revisited against the iPad
reference before presenting a final candidate.

## Source baseline and scope

Read-only comparison: clean Apple source `9df57f3fd96aeab6624407b1e4c07490125a6565`,
`Sources/DJConnectUI/DJConnectRootView.swift`, `SessionTimelineScreen.swift`,
`NativeSessionMomentsView.swift`, `ProfileDJSettingsEditor.swift`,
`DJConnectAppModel.swift`; `Sources/DJConnectCore/DJConnectClient.swift` and the
Session Runtime/History/Media/Artwork/Presence transports. This source comparison
is not installed Apple acceptance. Pi starting point is protected
`5dc6d7f2a8efe212b5b4222e9ffb049606886e98`, installed as rc.4 before this change.

Core remains contract authority. Pi retains `client_type=raspberry_pi`, explicit
Profile resolution, server-owned shared settings and no client-side planner.
The owner explicitly selected a full app with explicit authorized Profile mapping,
then clarified that **both Pi profiles are full apps using one shared codebase**;
the absent DJ Session must be added to both. The earlier Pi assessment's reduced
shared-wall scope is not the selected implementation target. Native layout adapts
between 720x720 and 1200x1920, while Session/transport/authorization code stays
shared. Microphone/PTT/local speech remain a separate hardware/product boundary;
no such capture or playback is silently enabled. There is no new Core,
Apple or other consumer source writer here.

## Actual gap inventory

| Apple experience | Pi rc.4 | Required outcome |
| --- | --- | --- |
| DJ Session is initial destination | Now Playing is initial destination; no Session page | Session-first landing and touch navigation |
| Start/reconnect/end a Profile-owned Session | No corresponding Pi transport/actions | Existing Core start/active/end routes, explicit input, confirmed results, stale-context rejection |
| Live Session moments, playback, Persona, Mood, Presence | Playback and independent Ask DJ screens; six-field settings editor | Same effective Session projection, moment ordering, source labels and interaction affordances |
| Saved Sessions and timeline | Absent | Server-authorized history, pagination, resume/live separation and deletion confirmation |
| Session media/artwork/forecast/reaction affordances | Absent | Advertised Core contracts only; preserve attribution, expiry and denial states |
| Now Playing, queue, playlists | Present | Compare command payloads, output selection, progress and search/selection semantics |
| Ask DJ | Read-only history and structured actions | Align conversation rendering/actions within selected Pi capabilities |
| Track Insight, Discover and Music DNA | Present, separate views | Compare returned sections/actions, privacy state and empty/error handling |
| Mac sidebar and compact Apple tabs | Pi bottom bar plus More | Match the observed iPad portrait navigation with equivalent destinations and selected/back state; retain compact-device layout |
| Settings, logs, About, legal, privacy, feedback | Settings/logs/About exist; other destinations not equivalent | Same human copy/meaning, five locales, device-specific options clearly separated |
| Feature icons and Brand V2 chrome | Core artwork imported, mixed legacy chrome | Consistent Pi colours now; semantic icon/page/copy inventory still to implement |
| Native speech, permissions and device integrations | Pi intentionally lacks local voice/microphone | Respect explicit Pi product decision; HA speaker delivery remains server-owned |

## Delivery and acceptance sequence

1. **Colour foundation:** shared Pi Brand V2 tokens across native pages, standard
   controls/popups, portal, updater and games chrome. Immutable artwork and arcade
   object colours retained. Contrast and actual QML fixture rendering qualified.
2. **Session lifecycle and navigation:** adopt Core contracts, Session-first
   destination and iPad-portrait-aligned Pi10 navigation. No empty buttons or local invented Session state.
3. **Session presentation and saved history:** moments/media/history with owner
   scope, identity/generation/revision fences, ordering, expiry and reconnect.
4. **Remaining screen parity:** systematically reconcile every menu destination,
   action, icon meaning and localized string against the pinned Apple source.
5. **Connected/installed proof:** paired HA and named Profile; cross-client start,
   reconnect, shared edits, successor Session, end, denial/offline and restart;
   actual 1200x1920 installed screenshots and physical touch acceptance.

Each phase must identify the exact source candidate, tests and remaining gaps.
An imported logo, mock screen, green test suite or installed package does not
close this inventory. The rc.4 Pi was unpaired and HA reported `not_configured`;
that is a connected-acceptance prerequisite, not proof of a Pi session feature.

## Current producer and portrait evidence refresh

Read-only live remote main verification: Core `8b221d07fe2215d9516d18fe92c832332c7a16ab`,
Apple `e106a467011b9ea84d301a81c4e07251314cc6dd`. Apple moved from9df57f3 during
reference preparation; its intervening diff changes only binary-intake qualification
Tools/docs, with no app/UI source delta. An isolated unsigned Debug build succeeded.
An iPad Pro11 simulator on iPadOS27.0 runs the actual app's explicit `review_demo`
fixture in Dutch/portrait,1668x2420. This is native simulator UI, not live HA proof.
The original physical iPad and installed Mac app are not replaced.

Observed stable views: DJ Session, More, Now Playing, Track Insight and Settings.
Private captures are in `/private/tmp/pi10-ipad-portrait-reference`; initial captures
of some pages hit the launch overlay and are retained as such. `*-ready.png` are the
post-launch page captures. The chosen geometry is a five-tab floating glass bar:
DJ Session, Now Playing, Track Insight, Discover, More. More contains two-column
rounded glass cards in row order: Ask DJ/Previous sessions, Music DNA/Queue,
Playlists/Games, Settings/About, Legal/Privacy, Feedback. Session toolbar controls
form a transparent leading capsule; connection/refresh form a separate trailing
capsule; the composer floats immediately above the navigation. The Mac's persistent
sidebar is not the portrait reference. iPad pop-out interaction is still to be
captured directly; the actual Mac Mood/Presence/voice popovers and shared SwiftUI
sources were observed but are not labelled iPad visual acceptance.

Core contract audit identified history representation2 (including publication and
silence rows), separate live `native_delivery` deadline grants, explicit Profile
onboarding, start/active/end, typed history-open, tail/anchor pagination, source
withdrawal and generation/context fences. The initial shared Session transport,
projection and Qt adapter are WIP; no protected merge/release/installed or end-to-end
parity is claimed. No Core or Apple source has been mutated by this consumer work.


## Shared-target checkpoint, 20 October 2026

Both deployment targets are full apps. They load the same `Main.qml`,
`SessionScreen.qml`, `FeatureIcon.qml`, `SessionController`, Session transport and
Profile-bound projections. Release-profile conditionals select canvas dimensions,
type, spacing and motion only; they do not define separate feature implementations.
The existing compact app pages remain reachable. New Session work applies to both.

Current local evidence: 461 tests passed; 36 actual QML fixture captures cover the
720x720 compact and 1200x1920 portrait targets, including Session and history.
These are offline/source checks, not installed or connected acceptance. The More
screen now has a two-column glass layout and the first eight iPad destinations in
matching order; the floating bar has the five iPad tabs. The owner additionally
requested the actual white iOS Session menu glyph: `DJSessionMenuSymbol.qml` ports
the repository-owned `DJPersonaMark` geometry from Apple e106a467 exactly, rather
than using the coloured application artwork as a feature symbol. Final render
verification of that icon is recorded separately from the preceding 461-test run.

Outstanding: the full Session feature inventory above, real profile authorization,
connected/cross-client behavior, ARM installation and physical touch acceptance.
No full-parity, release or deployment claim is made by this checkpoint.


### Unified interface decision

The owner explicitly authorized one entire interface for both Pi deployment
targets. The compact target receives DJ Session through the same screen/controller
as Pi10. Shared glass material and rounded controls now apply to both the main
app and its separate updater UI. Profile-specific branches retain hardware canvas,
spacing/type and ambient-motion limits; they do not remove destinations or features.
The 4-inch client retains its existing pages and device utility actions.


### Compact reference: iPhone mini

The owner selected iPhone (mini) as the design reference for the 4-inch target;
Pi10 retains iPad portrait. This changes responsive presentation, not feature
ownership or shared code. A dedicated iPhone13mini iOS27.0 simulator
`45BE4D93-465E-4AF2-BD4D-2B81AA868257` runs the existing Apple Debug build with
`review_demo`, Dutch locale and Session routing. Its actual 1080x2340 screenshot
is `/private/tmp/pi4-iphone-mini-reference/dj-session.png`; it is simulator/fixture
reference, not connected or physical acceptance.

The compact Session toolbar now places overflow and primary actions in a leading
capsule, with connection/refresh in a trailing capsule. Overflow exposes Persona,
Presence, voice preferences and saved Sessions. Both targets share the local
vinyl fallback (adapted from Apple's `AlbumArtworkPlaceholder`) without borrowing
Now Playing artwork or inventing a Session image grant. The Session content
scrolls above the persistent five-tab navigation. No microphone or local speech
capability is inferred from the reference screenshot. Text composer, authorized
media and remaining Session contracts still require implementation/qualification.


Compact checkpoint readback: 51 relevant tests passed after the last UI changes,
36 actual QML page captures passed with no QML errors, and the settings fixture
matrix passed 40 cases across five locales and two formats. Durable local preview
files are under the task visualization directory `pi-iphone-mini-design`.
The shared app is still an uncommitted candidate in the isolated worktree; no Pi
installation was performed by these reference/presentation checks.


### History search/navigation and attribution checkpoint

The shared Session screen now uses the existing advertised search-v1/history2
contract. Search is scoped to one selected Session, preserves server ordering,
validates echoed query/revision, bounded pages and UTF-16 highlight ranges, and
never manufactures a complete result count. Opening a result revalidates its exact
Session/entry via the navigation-only route and then requests the anchor window.
No start/end/playback command is used. Late results after leaving the view or
changing Profile are discarded; historical-query errors cannot end/replace the
active Runtime. Session input and pop-outs are cleared on context invalidation.

The shared touch keyboard supports letters, accents, symbols, selection replacement
and surrogate-safe backspace. It only edits the field; submitting is explicit.
The UI keeps accepted body text plain, supplies original/previous/revision source
links and shows Spotify attribution only with the packaged original Apple logo
and an exact safe Spotify source URL. Body rendering that requires attribution
waits for the actual local image renderer. The image is a byte-for-byte import
from Apple e106a467, recorded in branding/SPOTIFY_ATTRIBUTION_SOURCE.json.

Evidence: 463 tests passed, 13 skipped; the real QML preview covers40 views on
both target sizes, including retained history, the search popup, accented touch
input/backspace and private-input withdrawal. Existing HTTP, WebSocket and fixture
security tools passed. The security fixture initially hit sandbox loopback EPERM;
it passed under the normal approved local-test execution, not against live HA.
Local wheel SHA256 bf6794410e3b318b97c99d110f52f7e76cece70883c7678bb867e37c0fb59de0;
nine required Session/controller/keyboard/attribution files matched source bytes.
This remains local package/fixture evidence, not a release or installation.

Still open: live HA/Profile acceptance, full timeline paging/reading-position
behavior, search highlighting, text composer/contextual exchange, native
media/artwork/forecast/reactions, remaining Apple destinations and full visual
polish. Core and Apple retain their own writers and pending producer work; no
unpublished contract was adopted for this checkpoint.


### Draft review checkpoint #111

The shared candidate is now in draft PR111. The first source checkpoint was
3351e5a2b815416296af72e1a985cfcea5da4c53. Subsequent fixes align imports/UTC parsing
with Ruff0.16.0, keep the Qt application alive in tests, narrow malformed-input
exception handling and validate terminal/transition Session states. Opening/ending
states have truthful localized labels; ended/interrupted Sessions cannot remain as
an active Session. The initial CodeQL finding was a substring hostname assertion
in the synthetic test; it now checks the parsed hostname exactly, without suppressions.

Latest local results: 480 tests passed; Ruff0.16.0 passed;44 actual QML page views
passed, including opening/ending states and private-input withdrawal. The final
local wheel b48b7284c2969f26e5489d3e1c21e0f7de6a801562439e66d9e36b77aca7ecb4
matched all56 packaged Python/QML/JS/PNG source files. Earlier package/test receipts
above remain historical checkpoints. GitHub checks for the follow-up candidate
must be read independently; draft review does not authorize release or installation.

### Overnight history revalidation and reading checkpoint

PR111 head1ac0a8a passed every applicable GitHub check, including both Python
runs and CodeQL. This follow-up adds explicit first/next server-cursor pages to
saved Session detail, replacing each bounded page rather than accumulating old
private prose. Refresh revalidates the current page; a revoked cursor falls back
to the visible entry's fresh anchor window. Revision mismatch, denial, expiry or
an unavailable window cannot leave stale historical prose visible. Capability
withdrawal clears timeline, search, Session list and cursors. No navigation or
refresh path sends a Session/playback mutation.

Foreground detail revalidates every15 seconds and on explicit refresh. The view
restores retained entry identity and pixel offset after layout; opening a search
result scrolls to its selected entry. The actual QML exercise exposed a layout
race, fixed by restoring after the next layout frame. History detail now returns
to the saved Session list before leaving the history destination. First/next copy
is present in all five locales. Existing Profile/view-epoch fences remain active.

Local qualification:491 tests passed; Ruff0.16.0 passed;46 actual QML views passed
on720x720 and1200x1920, including synthetic long-history layout replacement on
both. Visual review confirms readable source cards and toolbar/navigation space;
these remain offline fixtures, not Apple/live/physical acceptance. Hostverify is
MATCH. Local wheel4e45f4d773f7c12cf575411ecbe5f0a50a80859ce191f6c4a2531a74e6276349
matches all56 packaged source files. Evidence: pi-history-reading checkpoint in
the task visualization directory; previous receipts are preserved.

Still open: backward/continuous timeline navigation, search highlighting,
monotonic expiry hardening, full native source/media admission qualification,
text composer/context, media/forecast/reactions and remaining Apple pages. The
bounded page reader is functional forward traversal, not full Apple Flow parity.
Dates still need presentation matching Apple. Glass uses the current native Qt
translucent fallback; true backdrop effects remain a design gap. No merge,
release, install, pairing, HA service effect or credential use occurred here.

### Overnight expiry and foreground checkpoint

All applicable remote checks on b9d494582a6c0a643eb2462bc786270e833c42b1 passed.
The next bounded change closes a local expiry gap: raw live projections could
previously render again after the wall clock moved backwards. A process-local,
thread-safe UTC floor now advances by elapsed time and also checks actual UTC.
Linux/Pi uses suspend-inclusive BOOTTIME where available; the Mac fixture uses
monotonic time. A forward clock correction stays conservative. This mechanism
never changes server deadlines and does not replace a synchronized host clock.
It remains alive across Profile invalidation and background transitions.

Current/Flow sources, retained history and search/navigation decoding all use
that same floor. Original presentation expiry still allows separately admitted
Flow recall until source expiry; no history row becomes a current grant. The
GUI checks deadlines again after queued worker delivery. App background/focus
loss clears ephemeral Session content, cursors and late results, blocks new
Session actions/refreshes while inactive, then performs a fresh read on return.
It does not end the server Session or replay a prior write. Qt application-state
wiring is in the actual app entry point; live platform focus/suspend remains to
be qualified on hardware.

Local evidence:497 tests passed; Ruff0.16.0 passed;52 actual QML views passed.
The synthetic current-native-grant fixture renders through the real controller
and QML, disappears after elapsed expiry despite a one-hour UTC rollback, and
clears on background on720x720 and1200x1920. Additional tests cover re-fetch,
retained-history/search expiry, allowed Flow recall before source expiry and
late GUI delivery. These are synthetic negative/renderer checks, not a released
producer, authenticated HA, ARM, installed or physical qualification. Hostverify
MATCH. Wheel80a8a7fcaef7247e9ec5a307aaa8d149d36a9476157b77a7b5c3ce86940d7990
matches all57 packaged sources. Evidence is preserved in pi-expiry-safety under
the task visualization directory.

Remaining gaps above still apply: full native source/media admission and actual
foreground/suspend behavior need producer/hardware qualification; continuous
history navigation, highlighting/date presentation, text composer/context,
remaining native pages and backdrop glass effects are unfinished. No merge,
release, installation, pairing or HA service operation is included.

### Pinned producer frames and Moment-first visibility checkpoint

All applicable remote checks on b1b450a9b6f02cddf4a45d0ed269615b3a5a9a29 passed.
Native decoding is now checked against the unchanged published Core expressive
fixture at protected8b221d07:200 actual Runtime snapshots across five families,
five languages and four Personas, with two frames per sequence. SHA256 matches
Core's original pin: d6dae495c0ba1540ff4803ff33d84f789062bb2fcdc433147f245af89622dc64.
Tests preserve complete body/title and both original source links, current/Flow
identity, rejected admissions, source expiry and subscription withdrawal. The
fixture is synthetic/source-shaped producer Runtime evidence, not a live provider
or authenticated Pi capture. Per-Moment grants remain authoritative: some genre
frames contain admitted internal Direction, while unqualified genre copy stays
hidden. No client inference from family, title or prose grants rights.

Actual shared QML views render six NL producer cases on both form factors,
including original Spotify attribution. They revealed that the decorative vinyl
and introductory card pushed accepted text below the compact viewport. These
fallbacks now appear only when there are no admitted contributions. Accepted
current/Flow content starts directly under the Session title; toolbar controls
and More/history navigation remain available. Layout checks verify the first
actual card begins in the upper half of the visible scroll region at both sizes.
This is a bounded Moment-first improvement, not completion of artwork/player UX.

Evidence:702 full local tests passed; the final producer subset205 passed;
Ruff0.16.0 passed;64 actual QML views passed, including grant/expiry/background,
source-family render/denial and history reading position. Hostverify MATCH.
Wheelbfba463df3954ba33cc08a51e896e4b24672557149528c158ad763858b20acee
matches all57 packaged sources. Evidence is in pi-native-producer under the task
visualization directory. No ARM/install/live/physical claim is made.

Core has a specific consumer handoff question for the released Ask DJ text
capability/version gate, request/response fixtures and raspberry_pi authorization.
The existing Pi advertisement remains readonly_actions until this adoption is
implemented and verified; no source/model operation or new Core writer was
requested. No response has yet been consumed. Other native source/media families,
continuous history, highlights/dates, composer/context, remaining pages and real
glass backdrop effects remain open. No merge, install, pairing or HA change.

### History date and literal-search presentation checkpoint

All applicable checks on fa3a97e3d8b6b9c127eff91e07ed3a169934a4a6 passed.
Saved Session dates now use the selected app locale and local timezone, replacing
raw ISO strings in the Session list and entry cards. The format is a stable i18n
key in en/nl/de/fr/es. Invalid or timezone-less values remain blank; equivalent
UTC/offset inputs display the same instant. Server-owned factual prose is not
reformatted or translated by this presentation change.

Search results now emphasize the exact server UTF-16 ranges. Ranges are checked
against character boundaries, merged when overlapping, and rendered with generated
bold/underline tags only. Every body fragment is HTML-escaped and line breaks
are preserved. Original accepted text remains unchanged in state; no local query
matching, semantic rewriting, model call or source fetch occurs. The native Qt
text document test proves literal image markup, emoji and newline round trips;
actual QML screenshots show the malicious-looking image tag as text. Attribution
and Spotify renderer readiness still fence the body.

Local validation:710 full tests passed, Ruff0.16.0 passed,86 actual QML views
passed, including dates and search in all five locales on both sizes plus literal
markup/emoji rendering. Hostverify MATCH. Local wheel
79107fb101ba7142a3167de3e6757308cd8347c32b1175d0ff782f111bcab139
matches all57 packaged sources. Evidence is in pi-history-polish under the task
visualization directory. These are local fixture/package proofs, not ARM,
installed, live Profile/HA or physical acceptance.

The protected Core source was also checked for selected single/bulk history
removal: the design explicitly forbids advertising before complete producer
qualification, and current main has neither delete capability nor implementation.
No delete control/request was invented. The prior specific Ask DJ consumer gate
question remains pending; no repeat ping or producer WIP adoption occurred.
Continuous/backward history, composer/context, additional media/source families,
forecast/reactions, remaining Apple destinations and backdrop effects remain open.
No merge, release, installation, pairing or HA operation occurred.

### Active Session text composer and confirmed-history checkpoint

All applicable checks on48f85a07e032191d63b4d2989694476fdee55fc6 passed. The
released producer was independently resolved in protected Core8b221d07: existing
POST ask_dj/message, contextual dialogue capability/version1, history entries2,
canonical raspberry_pi validation and Profile authorization. The observed,
sanitized sixteen-case handoff fixture is copied unchanged; SHA256
9be892d55c8aaee4871e54ac68ed04945fb0676ce5472e2091a83ee66b2151a8.
It pins runtimec21dc337 and the protected contextual-dialogue source readback;
it does not qualify installed Pi or authorize a new provider call. No Core WIP
was imported, no model/provider was called and no real HA command was sent.

Both sizes now share an active-Session text composer, touch keyboard and send
icon. It requires explicit/current matching Profile, private owner privacy,
known personal/household type, non-ephemeral mode and the exact published gates.
A deliberate send carries one fresh client_message_id, exact Session and optional
selected Moment or retained entry. audio_response is never; no local speech,
image/media fetch or returned semantic/action payload is executed by the client.
The server may interpret an explicitly submitted control request through its
existing authority; these tests exercised only synthetic transports.

Receipt validation binds resolved owner, client identity, exact context, text
input and turn/entry IDs. Only a fresh, validated history2 read supplies visible
conversation rows. Body/role/input/turn are checked; unrelated history Moments
never become current chat. Exact returned entry IDs plus matching client/turn and
both roles are required before the new answer is marked visible. An older chat
cannot satisfy a new receipt. Accepted-but-unavailable history is distinguished
from unconfirmed delivery. No optimistic user/assistant bubble or write replay
exists. A possible write timeout remains uncertain. Profile/background changes
discard late results; selected-source expiry clears the reference and draft.
Acceptance status and draft do not migrate to a replacement Runtime. Empty vinyl
and introductory cards also yield to confirmed conversation text.

The local capability advertisement now reports text/free input; voice/audio
remain false. The separate old Ask DJ history/actions destination still has no
composer. The owner's full-app selection supersedes the old readonly Pi baseline
for this draft. Core consumer documentation must be reconciled by its own writer
before protected release; Pi does not write into Core. This is not authority to
merge/install or to claim complete contextual client acceptance.

Validation:730 full tests passed, Ruff0.16.0 passed, HTTP/WebSocket/security
fixtures each returned0 and hostverify MATCH. The broad QML regression rendered86
views after composer integration; the final dedicated real-controller/QML harness
rendered24 composer views on both sizes, including all five languages, explicit
send/readback, selected published Moment/retained entry, source withdrawal and
private-draft clearing. Its transport is explicitly synthetic. The copied Core
receipt is separately exercised by the decoder unit test. Local wheel
1701c8688f9291cbb7fc7a91bbdf687d4e15414fa265536e503c5d43271c7b2f
matches all57 packaged sources. Evidence is in pi-session-composer under the task
visualization directory. No ARM/live/installed/physical/model qualification.

Open: standalone and private-ephemeral composition, rich response choices/actions,
full conversation paging/receipt reconciliation and reply scroll/reading polish.
Transport is currently serialized: a pending question temporarily blocks other
Session actions, including end; source expiry/background invalidation still run.
That concurrency/UX gap must be fixed before claiming parity. Other media/source
families, artwork/forecast/reactions, remaining destinations and backdrop effects
remain open. No merge, release, install, pairing or HA operation occurred.
