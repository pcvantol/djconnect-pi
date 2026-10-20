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

The shared app is now under draft review in PR111 on codex/pi-ipad-experience.
The dated checkpoints below record the current implementation and qualification;
the original rc.4 gap table remains an installed-baseline comparison. Source,
fixture/package and simulator proof do not qualify installed/live/physical Apple
parity. No merge, release, Pi install or new pairing has been performed by this
nightly work. Full functional/visual parity remains open.

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

### 2026-10-20 — Session control during text generation

The serialized-question gap above is now closed in source. One bounded question
worker is separate from two bounded Session-control workers and the existing UI
worker. Refresh remains available during a question. End can supersede a pending
read, without allowing a duplicate lifecycle write. Explicit question-in-flight
state separately disables duplicate sends. Shutdown withdraws foreground authority
and cancels queued work without claiming that an already started POST was cancelled.

Question, current-read and display-context tickets prevent an old reply/read from
replacing newer Runtime/capability state. A question worker never replaces Runtime
from its receipt-check snapshot. Concurrent current reads lead to a fresh read,
never a POST replay. Source expiry, capability withdrawal, replacement Runtime,
background/Profile invalidation, End and denial revoke old private results. A
question still queued when its authority is revoked is not sent. A started POST
may complete on the server; its late result cannot revive the ended Session.

The existing native Apple simulator captures were compared again with the actual
shared QML at720x720 and1200x1920: floating composer above the five tabs, top End
and refresh remain reachable. This comparison covers control placement and the
pending/ended states, not pixel/design or complete functional parity. Remaining
visual gaps include the native toolbar glyph/order details, playback metadata
composition, richer glass/backdrop effects and other Apple destinations.

Receipt reconciliation after concurrent refresh remains conservative: content is
read again, while the delivery status may remain accepted_unavailable until a
future exact-receipt reconciliation implementation. Reply scrolling, continuous
Flow, standalone/private-ephemeral composition and rich choices/actions remain
open. Apple explicitly acknowledged the review request but has not started the
Pi review; it retained its own Golden/VibeCast work. Core registered the canonical
Pi capability-document discrepancy as a separate owner dependency. No repeat
pings or producer-source changes were made.

Validation at this checkpoint:739 full tests passed; Ruff0.16.0 on src/tests
passed; hostverify MATCH. The real QML regression rendered86 views and the final
controller/composer harness rendered30 views, including the three concurrency
states on both sizes, without QML errors. Local wheel SHA256
b8a40aa6533f2089f1d808d632f5e90bee4f6278bb4f98fec5de40e937e91488
matches all57 packaged sources. Evidence is in pi-session-concurrency under the
task visualization directory. These are local synthetic transport/source/package
results, not live HA/Profile, ARM, installed, physical or complete Apple parity.
The prior ddc4650 head's applicable CI passed; the next head needs independent
remote-check readback. PR111 remains draft; no merge/install/pairing/HA/model work.

### 2026-10-20 — Exact receipt reconciliation and reply reading

The concurrent-refresh status gap above is now closed for a complete admitted
history pair. The controller retains one bounded, RAM-only validated receipt
(Session/client-message/turn/two entry IDs), never the transient response body.
A later current history read may confirm it only with both exact typed text rows,
roles and nonempty bodies. A partial pair, wrong identity or voice row does not
confirm a text send. Unknown delivery without a receipt remains uncertain; this
change adds neither an identity guess nor automatic POST replay. Context/End/
capability/source/background withdrawal still clears the receipt. Confirmation
metadata expires at its original earliest row deadline, without refetch renewal.
Expiry clears metadata and expired text before emitting the changed state.

A first exact confirmation emits one reply anchor. Shared QML waits for layout,
then brings that answer into the viewport above the composer and tabs. Ordinary
refreshes and repeated confirmation do not trigger another focus change. A touch
drag while waiting cancels following, preserving the user's older reading. The
actual shared QML harness covers a long conversation, refresh pixel position and
Qt-injected touch movement on both720x720 and1200x1920. The existing native Apple
reference captures remain design references; no new Apple runtime or live Pi
interaction was claimed.

This is bounded reply/read polish, not complete Flow. Backward/continuous
conversation paging, missing-pair anchor reconciliation, standalone/private-
ephemeral composition, rich choices/actions and other native media/destinations/
backdrop effects remain open. New source/media authority has not been invented.
Core protected main8b221d07 is unchanged and its separate document reconciliation
remains open. Apple continues its own work; no Pi review has been received. The
preceding5c8a8ab head passed all applicable CI checks (24 successes,4 conditional
skips); this new candidate requires its own remote-check readback.

Validation:751 full tests passed, Ruff0.16.0 src/tests passed and hostverify MATCH.
The broad actual-QML regression rendered86 views; the final dedicated composer
harness rendered36 views without QML errors, including long-conversation focus,
refresh position and injected touch cancellation on both sizes. Local wheel
SHA256 e46a0a3d4d75c895f7f62a84b2306476a40d926a5a15252f837846848cb7c040
matches all57 packaged sources. Evidence: pi-session-receipt-reading under the
task visualization directory. These are synthetic transport/source/package/local
Qt results, not ARM, installed, live HA/Profile, physical touch or full Apple
parity. No merge, release, install, pairing, HA operation or model call occurred.

### 2026-10-20 — Exact answer anchors and active chronological history

A validated receipt whose complete pair is absent from a fresh tail can now
probe the existing owner anchor endpoint. Receipt ID order is not assumed to be
timeline order: discovery is bounded to at most both exact IDs once per receipt.
Only a complete typed text pair confirms. The anchor must echo the exact ID and
bounded window/scan envelope. Tail and anchor revision must agree; canonical
ID/order conflicts are refused. Qualified same-revision rows merge in order,
retaining unrelated fresh tail rows and without changing the separate loaded
history detail. No history row is promoted into a current native Moment.

Once displayed outside the tail, the answer anchor is revalidated with current
reads so its body does not silently fall out on the next refresh. A withdrawn or
denied read does not preserve old prose. Discovery failure is not endlessly
reprobed; a future valid tail may still confirm the exact pair. Revision drift
stays unconfirmed instead of guessing, merging grants or retrying a POST. There
is no new endpoint, producer WIP, local source admission or write replay.

The active Session now exposes “Read from the beginning” through the shared
history destination and its existing first/next server pages. Actual QML testing
found and repaired a navigation/view-epoch race by entering history before
launching its scoped read. Generic read-only history wording is present in all
five locales and does not mislabel an active Session as saved. This provides
access to older active text and contributions; it is not continuous/backward
Flow paging or a claim of complete Apple navigation/design parity.

The preceding9eea469 head passed all applicable CI checks (24 successes and4
conditional skips). Core protected main8b221d07 is unchanged. No new Pi review
or released producer handoff was received; the canonical capability-document
dependency remains with Core. No repeat lane pings, model calls, HA operations,
merge, release, installation or pairing occurred.

The final screen review also corrected the detail title to “Session history” and
uses the actual user/DJ role on conversation cards, with stable locale keys.
Validation:761 full tests passed, Ruff0.16.0 src/tests passed and hostverify MATCH.
The final broad QML regression rendered86 views and the dedicated controller/QML
harness rendered40 views without QML errors, including actual history navigation
and exact anchored answer recovery on both sizes. Local wheel SHA256
56bea5e567fe338b61e77231bf96b19d3eb6c0140af13ca25100768838847df1
matches all57 packaged sources. Evidence: pi-session-answer-anchors-final under
the task visualization directory; earlier attempts/checkpoints are preserved.
This is local synthetic transport/source/package/Qt proof, not ARM, installed,
live HA/Profile, physical touch or complete Apple acceptance. PR111 stays draft.

### 2026-10-20 — Fresh previous-page navigation

Shared chronological history now has a localized Previous contributions control.
It reissues the existing server read for an earlier page instead of displaying a
cached body. At most32 RAM-only cursor/window descriptors are retained. Signed
cursors remain opaque; only Core authorizes returned Profile/Session/revision,
retention and source projections. No credentials or cursor signing material is
stored, and the separate current Session is not ended or replayed.

An invalid old cursor or changed revision causes one fresh read of the currently
visible entry, clearing the previous trail. A missing/withdrawn anchor or denied
read cannot revive old text. First-page navigation, detail close, Profile or
background invalidation, capability withdrawal and context errors clear prior
navigation. Ordinary same-page revalidation retains a still-valid trail. Existing
read tickets/view epochs reject late previous results, including End priority.

Actual shared QML exercises the previous button and freshly restored first page
on both sizes and renders its label in all five languages. Explicit previous-page
navigation starts at the top of that page; per-page old pixel restoration and
continuous/backward Flow stitching remain open. This is a bounded chronological
pager improvement, not full Apple history/interaction parity. Native media,
remaining destinations, toolbar/playback composition and backdrop effects also
remain open.

The preceding4b3db8b head passed all applicable CI checks (24 successes/4
conditional skips). Core protected main8b221d07 remains unchanged; its separate
WIP/source-budget improvements are not adopted. No Pi review/released producer
handoff was received. No repeat lane pings, Core/Apple writes, model calls, HA
operations, merge, release, installation or pairing occurred.

Validation:770 full tests passed, Ruff0.16.0 src/tests passed and hostverify MATCH.
Final broad actual-QML regression:86 views; final controller/composer/history
harness:52 views, including previous controls in five languages on both sizes,
with no QML errors. Local wheel SHA256
084b4f3d9433117c94bb842146e6971aea08055d38577d7d68f32b15aac909c9
matches all57 packaged sources. Evidence: pi-session-history-previous under the
task visualization directory. This is local synthetic transport/source/package/
Qt proof, not ARM, installed, live HA/Profile, physical or complete Apple
acceptance. Earlier evidence remains preserved. PR111 remains draft.

### 2026-10-20 — Native Session toolbar composition and scoped pop-outs

Read-only Apple protected main e106a467 and actual iPhone mini/iPad portrait
review_demo simulator captures establish the active toolbar order. Compact Pi
now shows More, Mood, Presence, Persona and End; Voice moves into More. Expanded
Pi shows Search, Mood, Presence, Persona, Voice and End. The optional Apple
VibeCast handoff is not added without qualified Pi authority. Active-only settings
and connection controls disappear in historical/empty contexts; refresh remains
in the trailing capsule. See branding/SESSION_TOOLBAR_REFERENCE.json.

Mood, Presence and Persona symbols follow confirmed settings3 values, with
server Runtime fallback only for Mood/Presence and neutral unknown symbols.
These are Pi-owned Canvas equivalents, not exported or pixel-identical SF assets.
The exact white Session tab mark stays unchanged. Presenter/festival microphone
shapes denote DJ style; no capture or audio capability is introduced.

Open choices capture Session/Profile/edit_token. Context replacement closes
transients. A queued option click also checks active lifecycle, exact scope/token,
settings availability and no pending operation before dispatch. Thus a stale menu
cannot write into a replacement/ending Session or across a token change.

Validation:770 full tests passed; Ruff0.16.0 src/tests passed; hostverify MATCH.
Final actual QML:86 broad regression views plus84 dedicated controller views,
including thirteen glyph variants, three pop-outs and stale queued-click no-write
checks on both sizes. Preview tools pause only automatic fixture polling timers;
explicit controller reads and layout timers remain exercised. Production polling
is unchanged. Local wheel SHA256
7f666f39e2de0790d994401f7606c246048021936a187a2fe62b2e88da70cece
matches all57 packaged sources. Evidence: pi-session-toolbar under the task
visualization directory, including native offline simulator references.

Parent a084845 passed all applicable CI (24 successes/4 conditional skips).
Core protected main8b221d07 remains unchanged; its idle ea91fad7 WIP is not a
released handoff. No new Apple Pi review was received. No repeat pings, producer
writes, model/HA operations, merge, release, installation or pairing occurred.
This is local fixture/source/package/design proof, not ARM/live/installed or
physical acceptance. Playback metadata composition, exact native glyph fidelity,
complete Flow, rich interactions/media, remaining destinations and real backdrop
glass remain open. PR111 remains draft; full Apple parity is not claimed.

### 2026-10-20 — Current Runtime playback metadata

The shared Session now renders title, artist, album, observed progress/time and
optional output name from its own broadcast.playback. Protected Core8b221d07
RendererSafePlaybackProjection defines these renderer-safe observations; Apple
protected e106a467 NativeSessionMomentsView.musicDetails supplies the visual
hierarchy. No global playback/status or historical entry is substituted. Only
active, exactly matching Session snapshots, playing/paused state, nonempty item
identity and a zoned updated_at enter this closed projection. Ending/idle/invalid
snapshots and context/background invalidation remove it. This observation is
separate from Moment native_delivery source/display grants, not a new grant.

The optional released source_url is validated as an exact canonical HTTPS Spotify
track link. Invalid source identity withdraws the projection. Spotify metadata
waits for the existing packaged attribution logo's renderer-ready fence and opens
its original validated source. All metadata is bounded plain text. Progress is
clamped observed server position, never a locally advancing clock or full-listen
claim. Optional output name comes from this same snapshot; global volume/output
is not mixed in. No artwork URL, up-next data, provider fetch or playback write is
exposed. Native artwork/gestures/favorites, volume and complete header composition
remain open. Admitted Moments retain priority above this card so their previously
verified first contribution stays above the fold on the compact screen.

Validation:771 full tests passed, including all200 unchanged protected producer
frames and malformed state/source/timing checks. Ruff0.16.0 src/tests passed;
hostverify MATCH. Broad QML regression86 views passed; the final dedicated
controller harness adds actual scrolled metadata in all five languages, both
sizes, a separately labelled synthetic paused/output variant and ending withdrawal
(98 views total, no QML errors). Original producer fixture bytes are unchanged.
Local wheel SHA256
517f48914d50a9a44e304a8628ec7f61f2bd1561d26134f6b091b2bd51dc79bb
matches all57 sources. Evidence: pi-session-playback-final under task visualizations.
Visual review corrected the progress fill to white; earlier captures are retained.
Native offline simulator references remain preserved in pi-session-toolbar.

All applicable checks on parent638f335 passed (24 successes/4 conditional skips).
No new concrete review/handoff was received. Core main remains8b221d07, its
separate WIP is not adopted; Apple keeps its own lane. PR111 remains draft.
These are local decoder/fixture/render/package/design results, not live Profile,
HA, ARM, installed or physical acceptance. Full Apple parity, continuous Flow,
rich interactions/media and real backdrop glass remain open. No merge, release,
installation, pairing, HA effect, producer write or model request occurred.

### 2026-10-20 — Previous-page entry and pixel-position restoration

Forward navigation may now add the currently visible retained entry ID and its
finite bounded pixel offset to the existing maximum32 RAM-only page descriptors.
No body, title, credentials or media is cached. Previous still reissues the same
owner server read; the private reading metadata is stripped before transport.
Only a same-revision fresh page that still contains the retained entry can emit
its restore instruction. Revision/cursor fallback uses the fresh visible anchor
and drops the old position. Missing/expired entries never restore old text or
force a stale position. Existing context/Profile/foreground/view-ticket fences
and navigation-trail withdrawal remain unchanged.

Shared QML restores after layout and clamps against the new content height.
Context/view withdrawal cancels pending position timers; active touch dragging
also stops or suppresses a queued restore. First/next without a remembered
position still starts at the page beginning. This improves explicit Previous
navigation, not continuous/backward Flow stitching, arbitrary forward revisit
history or full Apple reading parity. No producer contract or write changed.

Validation:778 full tests passed, Ruff0.16.0 src/tests passed, hostverify MATCH.
New controller cases cover fresh exact-entry restoration, metadata exclusion
from requests, NaN/infinite/boolean/excessive offsets, missing entries and revision
fallback. Actual QML presses Next/Previous on long fresh pages and proves equal
entry+pixel offset after replacement on720x720 and1200x1920. Dedicated harness:
102 views; broad regression:86 views, no QML errors. Local wheel SHA256
859cca49a35fd5813c7ac38d2f564dc3047d51fb5e0cd03965f3ee670f208dc1
matches all57 packaged sources. Evidence: pi-session-page-position under task
visualizations. Earlier evidence is preserved. These are local synthetic read/
source/package/Qt results, not live HA/Profile, ARM, installed or physical touch.

Parent645f62a passed all applicable CI (24 successes/4 conditional skips). The
only PR inline comment is the earlier synthetic URL-test CodeQL finding, already
fixed on the earlier committed head. Core protected main remains8b221d07; its
own source-selection WIP continues and is not a release. Apple reports separate
current/source Session identities in its own work; no Pi review/handoff arrived.
No repeat pings, other-lane writes, model/HA work, merge, release, install or
pairing occurred. PR111 remains draft. Full Flow, rich interactions/media,
remaining pages, native backdrop effects and hardware/live acceptance stay open.

### 2026-10-20 — Read-only Forecast v1 text subset

The same Session UI now has Flow/Outlook selection on both sizes when the paired
active Runtime advertises exact session_forecast/version1. It consumes the
existing owner-bound broadcast.session_forecast; no new endpoint, generation,
Planner, lookup, playback command or automatic write is added. Source authority
is protected Core8b221d07 SESSION_FORECAST_V1.md, capability_contract.py and
session_forecast.py. This is a Pi text adoption of that released contract, not a
claim of finished Apple Forecast layout, imagery or joint/live acceptance.

The closed receiver requires matching active Session/snapshot, explicit supported
capability, bounded integer revision, original zoned issued/deadline (maximum120s),
nominal900s and supported0/900 semantics, at most three typed known sections and
bounded plain text. Current anchors must match the same Runtime playback item
and original source link. Current/intention/conditional-target labels stay
distinct; server order/title/body are preserved. Imagery and unknown/internal
fields never leave the receiver. Canonical Spotify current context waits on the
existing packaged-logo readiness fence with its original clickable source.

Lower revisions withdraw displayed text. Expired/withdrawn/invalid frames cannot
revive at the same revision; equivalent reads cannot extend the earliest accepted
deadline. Existing elapsed-time UTC floor governs expiry, including GUI state
reads. Subscription revocation, capability loss, replacement, background and
binding invalidation withdraw content. This projection is not retained history,
a Moment grant, queue promise or locally advancing fifteen-minute countdown.
Flow/Forecast toggling preserves composer input and Flow scroll position; explicit
question send returns to Flow. User-facing labels use stable keys in all five
languages. Native artwork/artist imagery remains unimplemented, without fetches.

Twenty unchanged pure producer projections were realized by the exact released
ForecastProjection/realize code in a temporary package with explicitly synthetic
semantics and fixed clocks: five languages/four Personas. Fixture SHA256
ad66e5a07d983edef8597dd65c8331c6cf59e5b18e4b3f3c90b4a65bc4a1f2b2.
forecast-provenance.json records source byte hashes and exact construction.
These are pure expression/projection fixtures, not Runtime/Planner, provider,
model or live owner-admission proof; no Core WIP/export or producer write used.

Validation:809 full tests passed; Ruff0.16.0 src/tests passed; hostverify MATCH.
Tests cover immutable prose/role/source preservation, expiry/rollback, original
deadline retention, revision rollback, wrong Session/anchor, malformed claims,
subscription/capability withdrawal and controller active-read/GUI expiry.
A GUI state read that expires text retains a pending change notification for the
next deadline tick; its test prevents a getter from swallowing visible withdrawal.
Actual QML:114 dedicated views (five-language Forecast/toggle/draft/Flow-position
and expiry on both sizes) plus86 broad regression views, no QML errors.
Local wheel SHA256
09711965c5605a2760e7104252b0a177ef2b2f046c736292faf1bcbd3ce0289b
matches all58 packaged sources. Evidence: pi-session-forecast-final under task
visualizations; earlier source/captures/checkpoints retained.

Parente86c969 passed all applicable CI (24 successes/4 conditional skips). Core
protected main8b221d07 remains unchanged; other-lane WIP and budget stay untouched.
No new concrete Pi review/released handoff arrived. PR111 remains draft. Full
Flow/continuous history, rich actions, media/native artwork, remaining Apple pages,
real backdrop glass and live Profile/HA/ARM/installed/physical acceptance remain
open. No merge, release, install, pairing, HA effect or model/provider call occurred.

### 2026-10-20 — Typed historical playback cards

Shared chronological history now follows the protected Apple playbackDescription
field hierarchy: observed-playback heading, title, artist, album, original source
attribution and localized observation time. The heading translations are pinned
to Apple e106a467 Localizable.strings for en/nl/de/fr/es. Protected Core8b221d07
session_history_projection.project_entry supplies the typed playback contract.
This does not assert a full listen, repeat count or current playback authority.

Only playback_observed with exact observed_playing_not_full_listen coverage and
bounded string fields receives the typed presentation. Invalid coverage/shape is
refused; empty metadata keeps the original text fallback. Original body, canonical
entry/order, retention and source fields are unchanged, including search text and
UTF-16 highlights. Typed fields are plain text; literal markup/emoji stays literal.
The existing Spotify renderer-ready fence applies before fields appear. No
historical image/progress/queue/current grant, command or provider fetch is added.
Expiry removes the complete retained row and its derived display fields.

Validation:816 full tests passed; Ruff0.16.0 src/tests passed; hostverify MATCH.
New tests cover exact field/source/body preservation, no current promotion,
unsupported/malformed coverage/field bounds and empty-text fallback. Dedicated
actual QML:128 views, including synthetic history2 observed-playback transport
through the real controller, all five languages/both sizes, fully scrolled card
and retention withdrawal. Broad QML:86 views, no errors. The playback row is an
explicit synthetic consumer fixture; existing pinned producer bytes are unchanged
and it is not represented as a new Runtime/provider export. Local wheel SHA256
64f9ed2b903e9196c16b1c6a850fab99e8561257b1aab3df5a1227e8143a68ac
matches all58 sources. Evidence: pi-session-history-playback-final under task
visualizations; earlier first-fold captures are preserved.

Parent654eea8 passed all applicable CI (24 successes/4 conditional skips). Core
main8b221d07 remains unchanged; no new concrete Pi review/handoff arrived. No
producer writes, repeat lane pings, model/HA effects, merge, release, install or
pairing occurred. PR111 stays draft. Source/fixture/package/Qt proof is not ARM,
installed/live Profile/HA or physical acceptance. Complete Flow/media/backdrop
and remaining Apple destinations stay open. Screen review also identifies a
navigation gap: current-Session history still selects More, and detail Back goes
through the archive list. Preserve current versus archive origin in the next
bounded navigation fix; no historical row should become current authority.

### 2026-10-20 — Current-history origin and scoped navigation reads

History entered from the active Session now uses a local session-history route,
keeps the Session tab selected and returns directly to Flow with its unsent text.
Archive history remains under More: detail Back returns to the archive list and
list Back returns to More. Search/open keeps the navigation origin independently
of the original entry Session. A foreign retained Session opened from Flow does
not replace Runtime Session identity or acquire current/media/write authority.
Profile/background/context withdrawal leaves the appropriate empty root view.

Actual UI testing found an ordering problem beyond tab selection: a visibility-
triggered poll or an already pending read could capture the old view epoch before
navigation completed and prevent the chosen history page from loading. Both
entrypoints now use one bounded local read intent with exact Profile, kind and
current-Session guard. They navigate/clear old detail, wait for prior control work,
then launch the existing owner read on the next UI turn. Polling yields until that
read starts. View/Profile/context loss cancels the intent, including before any
worker submission. Empty-page Refresh chooses the same origin; it cannot silently
open the archive from current history. No new route is sent to Core and no write
is retried. Existing transport binding, view/generation and revision fences stay.

Clearing already-empty search/selection state no longer emits recursive GUI
changes; clearing search still advances the view ticket fence. This removes
binding loops without letting late results through. Both preview tools now also
fail on Binding loop detected, in addition to their existing QML-error checks.
The native fixture injector clears old selection before changing a synthetic
Session, matching the actual controller rather than creating a spurious loop.

Validation:817 full tests passed; Ruff0.16.0 src/tests passed; hostverify MATCH.
The existing menu source check was updated to the common archive handler; the new
controller test proves empty clears retain the fence without redundant changes.
Actual QML:152 dedicated views plus86 broad regression views, no errors or binding
loops. Both sizes exercise current/detail/back/tab/draft, real archive menu/list/
detail/back, navigation-only owner open+anchor reads for current and foreign
entries, unchanged active Runtime identity, queued-read cancellation and foreground
withdrawal. Transports are synthetic; the pending executor is deliberately held
and drained to expose stale-read races. Local wheel SHA256
b43ad7e7e4e5bc2bbc732ee432eeb00f54241bb5735235ef70c18a7312d69068
matches all58 sources. Evidence: pi-session-history-navigation under task
visualizations; intermediate failing probes and previous evidence are retained.

Parent3fa6b38 passed all applicable CI (24 successes/4 conditional skips). Core
protected main8b221d07 remains unchanged and no new concrete Pi review/handoff
arrived. No other-lane writes, repeat pings, model/provider/HA effects, merge,
release, install or pairing occurred. PR111 remains draft. This is local source/
fixture/package/Qt qualification, not live Profile/HA, ARM, installed or physical
acceptance. Continuous Flow, Flow-position restoration across history navigation,
media/actions, remaining Apple destinations and native backdrop design stay open.


### 2026-10-20 — Return from current history to the same Flow contribution

Current-history navigation now remembers one bounded RAM-only reading descriptor:
Session, Profile, Moment/conversation kind, exact visible ID and finite pixel
offset. Search/open from Flow captures the same origin position. No old prose,
source grant or historical body is cached. After layout, return locates the ID
only in the current admitted Moment or retained conversation model and clamps the
scroll offset. A withdrawn/missing ID falls back to the top. This covers visible
Moment/conversation cards; playback-only, empty and Forecast positions are not
remembered by this descriptor.

Archive entry, leaving Session, Profile/Session change and foreground/context
withdrawal clear the descriptor and pending timer. A Flow touch drag cancels the
queued restoration. History scrolling deliberately preserves the independent
Flow descriptor. Reply-following is stopped when capturing the reading position,
so an old reply timer cannot override the explicit navigation return. Neither a
new server read contract nor a timeline order/grant is inferred from position.

Validation:817 tests passed in the qualified host environment; Ruff0.16.0
src/tests passed; hostverify MATCH. Actual QML:160 dedicated controller views plus
86 broad regression views, no errors/binding loops. Both sizes exercise exact
entry/pixel restoration, withdrawal fallback and injected Qt history-touch drag;
the native Moment branch captures an ID from the unchanged released producer
fixture. Existing foreground navigation probes also verify descriptor withdrawal.
Local wheel SHA256
6bac8c059997dd95a35432a579b4b6839cc4ea7012af5ddcc448af32b50de1b0
matches all58 packaged sources. Evidence: pi-session-flow-return under task
visualizations. Earlier evidence remains intact. The first restricted test run
had804 passes/13 environment skips; the qualified run above has817 passes.

Parent3aa4d6d passed all applicable CI (24 successes/4 conditional skips). Core
protected main8b221d07 and Apple e106a467 are unchanged. Core recorded its own
historical-website/voice-route WIP checkpoint aad9a3df; this Pi change neither
adopts it nor adds voice. No new Pi review or released handoff arrived. PR111
stays draft; no merge, install, pairing, HA/model/provider action occurred.
Source/fixture/package/local Qt-touch proof is not ARM, installed/live Profile/HA
or physical acceptance. Continuous Flow/server windows, remaining Apple pages,
media/actions and real backdrop effects remain open.


### 2026-10-20 — Bounded fresh search pages and visible-result revalidation

An open search now requests revalidation every15 seconds. One local intent waits
for an already-running control read, bound to the same Profile, Session and query;
closing/editing/context withdrawal cancels it. The worker checks foreground/view
before each GET, including between pages. Closing the popup clears its private
query/results. No write, generation, provider call or replay is introduced.

Search More and revalidation both re-read all displayed pages from the first
owner query, following only freshly returned cursors. Pages publish atomically;
old result bodies are never appended from a cache. Every page must retain the
same revision and strictly increasing, non-overlapping entry IDs/orders. Cursor
cycles, revision drift, malformed pages or denial withdraw the old result set.
A new query can read the changed revision afresh; failure does not auto-replay.
Only existing protected Core8b221d07 historical_projection_query.async_search_entries
and advertised text-search1/history2 are used. No Core WIP is adopted.

The local scan budget is five pages per query (transport requests20 rows each).
More hides at that bound while server complete remains false; five-language copy
asks the user to refine the query. Incomplete/empty scan windows never claim a
complete search. This is an explicit bounded consumer limitation, not unlimited
Apple search parity. A surviving visible result restores its ID/pixel after
layout; missing IDs fall back to the top and dragging cancels queued restore.
A same-Session/revision history background check preserves the independently
revalidated search. Changed revision/scope clears it.

Validation:827 qualified full tests passed; Ruff0.16.0 src/tests passed; hostverify
MATCH. Ten added tests cover fresh previous-page reads/body withdrawal, revision/
identity/order/cursor conflicts, denied pages, scan budget/reset, cancellation
before and between reads, and same-revision history coexistence. Actual QML:
176 dedicated views plus86 broad regression views without errors/binding loops.
Both formats show five localized limit labels, literal markup/highlights/sources,
retention replacement with exact reading position, the actual timer callback
waiting behind a held read, close-before-dispatch cancellation and denial. Initial
fixture probes are retained: they attempted search while a visibility poll was
still busy; the final harness waits for the UI's existing enabled condition.
Local wheel SHA256
041a8a14cfe87c86bbcc33c91b009b02b1d85efd810a16012ec25592c3e19990
matches all58 sources. Evidence: pi-session-search-revalidation under task
visualizations. This is local synthetic transport/source/package/Qt proof, not
ARM, installed/live Profile/HA or physical acceptance.

Parentabb8bcd passed all applicable CI (24 successes/4 conditional skips). Core
protected main8b221d07 and Apple e106a467 are unchanged. Core recorded its own
583f6e65 test-only WIP checkpoint/327 Golden steps; no producer release or new Pi
review arrived. No other-lane writes, repeated pings, model/provider/HA action,
merge, release, installation or pairing occurred. PR111 remains draft. Continuous
Flow/server windows, standalone/private-ephemeral composer, media/actions, remaining
Apple pages and real backdrop effects stay open.


### 2026-10-20 — Privacy/legal destinations and adaptive More navigation

Both targets now expose Privacy and Legal as real shared destinations under More,
with a selected More tab, glass cards, scrollable content and explicit Back.
The common menu order follows protected Apple e106a467 MoreView; compact uses
one column and portrait tablet three, following its adaptive grid intent. Logs
precedes About and the Pi-specific Control utility follows the common destinations.
Feedback is still absent; logs retain Pi visibility policy rather than silently
adopting Apple's diagnostic flag. Privacy/shield and document glyphs are Pi-owned
semantic equivalents, not exact SF Symbol geometry.

The Privacy page describes explicit Profile authority, Pi-local pairing/settings,
RAM-only Session/search withdrawal, no Pi Spotify credentials, and the existing
no-microphone/no-local-DJ-audio behavior. It does not import Apple's private-storage,
APNs or blanket personal-data assertions. Existing Apple independence, trademark
and AI/Assist notices are reused unchanged in all five locales. OSS text describes
Python/Qt/PySide and the existing MIT project licence; an explicit user click can
open the source licence. This is product information, not a new legal agreement
or a complete third-party notice inventory. No network is fetched by opening the
pages and the external licence link is not automatically opened in the fixtures.
Provenance: docs/branding/INFORMATION_PAGE_REFERENCE.json.

Validation:827 tests passed, Ruff0.16.0 src/tests passed, hostverify MATCH.
Actual QML:116 broad views including five-language menu/Back/selected-tab checks,
scrolled page ends and both menu sizes;176 Session/composer regression views.
No QML errors/binding loops. The existing static menu test now expects the adaptive
grid/order; the first preview import-shadowing error and superseded fixed-grid
assertion are retained in diagnostics. Local wheel SHA256
48d5694d2d9cca702555e21fc1624157888db47e65982736dee15a7646952c6d
matches all59 packaged sources, including InformationPage.qml. Evidence:
pi-information-destinations under task visualizations. This is local source/
fixture/package/Qt evidence, not ARM, installed/live or physical acceptance.
Apple More/privacy/legal alignment here uses pinned source and existing design
references; no new native More-screen screenshot or exact visual parity is claimed.

Parenta15799a passed all applicable CI (24 successes/4 conditional skips). Protected
Core8b221d07/Apple e106a467 remain the selected references. No other-lane writes,
producer contract, model/provider/HA effect, merge, release, installation or pairing
is included. PR111 stays draft. Continuous Flow, standalone/private-ephemeral
composition, rich actions/media, feedback, remaining Apple pages and actual
backdrop/SF fidelity remain open.


### 2026-10-20 — Current-only live-Moment credit replies

Protected Core8b221d07 ask_dj/service.py explicitly disables archive persistence
for selected_moment. The pinned active-credit response therefore has
history_scope private_ephemeral, history_persisted false and zero entry IDs.
The former Pi receipt/history2-only path could not show this successful answer.
The existing contextual dialogue contract permits accepted current responses;
its source/owner/clear/lifecycle rules remain authoritative.

The shared client now renders a narrow current-only text subset: an exact accepted
owner/client/turn/context receipt, private_ephemeral/zero entries, matching bounded
root/assistant generated text, qualified_dialogue_v1, cc0_normalized_fields_v1 and
explicit MusicBrainz CC0 source links. It requires an originally selected admitted
Moment with a finite original source/display deadline and identical fresh/current
reference. Body, source links and declared attribution are preserved; all returned
media, actions and unrelated fields are excluded. Unsupported private responses
remain accepted_unavailable. This is not general private-mode or standalone chat.

One RAM-only answer is marked Current answer · not saved. It is separate from
retained conversation and is never appended to history or treated as a new native
Moment. New question, End, Profile/binding/background/context withdrawal remove it.
An observed native revision/style/reference change invalidates pending questions,
even if the revision later changes back. Current reference identity/signature and
the original earliest finite deadline must still match at receipt/GUI admission
and expiry. Getter withdrawal preserves a dirty notification for the next tick;
clock rollback cannot revive it. A concurrent refresh owns Runtime and may not be
overwritten by the question worker. Spotify dependency keeps the packaged logo/
renderer-ready fence. The new card receives focus only for the explicit own send;
existing touch cancellation remains active.

Validation:845 full tests passed, Ruff0.16.0 src/tests passed, hostverify MATCH.
Eighteen new tests cover exact original prose/CC0 attribution, no history/media
promotion, source/revision/style/expiry/scope withdrawal, GUI getter/tick/rollback,
observed revision-change-back and malformed/error/foreign receipts. Actual QML:
186 dedicated views plus116 broad regression views without errors/binding loops.
Five labels on both formats use the unchanged released response prose, with only
explicitly synthetic transport/context identities adapted; no new producer Runtime
or content-quality claim. Initial fixture failures (unrun question worker, late
local deepcopy import, language change during a held old-language poll) remain in
diagnostics. Final harness drains prior reads before each locale change and runs
the explicit question worker. Local wheel SHA256
ca34bb0d84b9937bdd6530479389bcbac820625b6f4e17abbbfce01198a67497
matches all60 packaged sources. Evidence: pi-session-current-reply under task
visualizations. Fresh read-only screenshots from the already booted iPhone-mini
and iPad reference simulators preserve native Session design comparison; no Apple
build/install, live model, provider or HA action was performed.

Parent72e54df passed all applicable CI (24 successes/4 conditional skips). Core
was asked once for protected-source clarification of broader private/standalone
lifetime/readback; that answer/review remains pending. The implemented subset uses
the existing finite selected-Moment grant and does not infer broader rights.
Core remains in its own Wikidata/website WIP, not adopted here. General ephemeral
mode, standalone, dependent follow-up responses without an explicit live selection,
other source bases, current-reply reading descriptors, complete Flow/media and
remaining Apple/native design parity remain open. PR111 remains draft; no merge,
release, Pi install, pairing or live/ARM/physical acceptance is included.


### Current-only reply reading position — 20 October follow-up

Returning from current history now also restores a still-valid current-only
answer's card and pixel offset. The existing single RAM-only descriptor stores
only Session/Profile, kind, receipt turn ID and finite bounded offset. It does
not retain body, source grant or deadline, and cannot reauthorize a response.
The state getter must still admit the live reference at restoration; a withdrawn
or replaced ID falls back to the top. Existing Profile/Session/foreground clearing
and touch-drag cancellation apply. Capturing the position also stops queued
current-answer focus so it cannot override the return position.

Actual QML probes cover both720x720 and1200x1920: same reply identity/pixel on
return and source-body withdrawal while away. The long reading probe explicitly
repeats synthetic response text to place the reply alone in the viewport; the
five-language original released-prose probes remain unchanged. Initial tablet
fixture failure is preserved: a short response legitimately left the previous
Moment visible first, so its descriptor was selected. No product navigation or
rights were changed to satisfy that fixture.

Validation:845 full tests passed, Ruff0.16.0 src/tests passed, hostverify MATCH.
Final QML:190 dedicated controller views plus116 broad views without errors or
binding loops. Local wheel a307d4d3ff7b7471e00acd3cfe1c1ee42abd4b8e3cad0ed7a970d2f5b0b32b94
matches all60 packaged sources. Evidence: pi-session-current-reply-position under
task visualizations. Parent e513693 passed
all applicable CI (24 successes/4 conditional skips). This follow-up needs its own
CI readback. General private/standalone chat, user bubble, playback-only/Forecast
positions and continuous Flow remain open. No Core/Apple WIP, new contract, model,
HA, provider, installation, merge or physical acceptance is included.


### Own question beside the current-only answer — 20 October

The confirmed current-only response now carries the exact bounded local request
text. A trailing glass user card, capped at85% of available width, precedes the
DJ answer and uses the existing five-language You label. This follows the role
separation/alignment of protected Apple e106a467 AskDJMessageBubble; geometry and
PlainText are Pi adaptations, not an exact native markdown/effects claim. Source
provenance: docs/branding/CURRENT_QUESTION_REFERENCE.json.

The question is not a returned server echo or a historical entry. It is retained
only in the same single RAM-only current-reply object as its admitted answer.
Receipt/source/style/revision/deadline/Profile/Session/foreground gates continue
to govern the whole pair. New question, End or withdrawal removes both. Reading
position/focus uses their shared container and receipt identity. No pending or
uncertain question bubble, new archive write, transport field, microphone/audio,
standalone/private-session gate or automatic replay is introduced.

Six new tests check missing/non-string/empty/oversized question rejection and an
exact local prompt despite a foreign server user-message echo. Snapshot mutation
cannot change the retained prompt. Existing expiry and scope tests withdraw the
entire object. The native QML harness checks literal image markup/emoji/newline,
PlainText, bounded user-card width and atomic blanking in all five locales on
both canvases, while retaining earlier reply-return/reading probes. A PySide
QQuickText enum conversion limitation in the first harness is preserved in
diagnostics; the final check evaluates the enum within QML itself.

Validation and package results are recorded in pi-session-current-question under
task visualizations. Parent d8e1d463 passed all applicable CI (24 successes/4
conditional skips); the new head requires independent checks. This is confirmed
selected-Moment credit UX only, not general ephemeral or standalone parity.


Final local result:851 full tests passed, Ruff0.16.0 src/tests passed, hostverify
MATCH.190 dedicated QML views plus116 broad views without errors/binding loops.
Wheel c218e31f1b345367eaddfa33174403881511e1656396bb2729ab5cba98a4202c
matches all60 packaged sources. Both actual canvas captures were visually checked;
this specific user-card comparison uses pinned Apple source and existing offline
Session simulator references, not a newly staged native conversation screenshot.
No live, ARM, installed or physical proof is inferred.


### Local question while a request is pending — 20 October

A submitted Session question now appears immediately as a trailing glass user
card with the existing five-language Sending label. It is explicitly local input,
not a receipt, generated answer or retained history. One RAM-only object contains
only bounded text, current Session and unique client_message_id, with its binding
kept private in the controller. No transport or producer contract changes.

It exists only while that single bounded question worker is pending. Current
Profile/Session/privacy/foreground and the original selected-Moment reference
continue to gate display. Getter and deadline tick withdraw it before painting
when scope/source is lost; queued revoked requests are not submitted. End clears
it while an already started POST may still finish server-side. Completion clears
pending input atomically before current-only or retained confirmation. Failure or
uncertain delivery removes the bubble and keeps existing status/revalidation
behavior; no replay, synthetic answer or historical insertion occurs.

Only an explicit own submit can focus the pending card after layout. Existing
touch cancellation and history navigation suppress following. Pending cards do
not add a reading-position descriptor, uncertain-turn history or new rights.
The confirmed user/answer pair and its receipt-ID/pixel restoration remain intact.
Visual role/shape follows the existing pinned Apple user-card reference, with Pi
PlainText and85% width adaptation; this is not exact native effects parity.

Six new tests cover exact local input before dispatch, immutable snapshots,
combined scope/source/End withdrawal before queued POST, and uncertain completion
without replay after refresh. Actual QML holds the question worker explicitly in
all five languages on both canvases, checks literal markup/emoji/newline and
PlainText, then completes acceptance and verifies pending withdrawal. End probes
also require the visible pending card and its text to be empty.

Final local results and package proof are preserved in pi-session-pending-question
under task visualizations. Parent7064194 passed all applicable CI (24successes/
4conditional skips). The new head needs independent checks. Complete Flow,
uncertain-turn retention, broader private/standalone contexts and live/ARM/
installed/physical acceptance remain open; no install/merge/HA/model action.


Local verification:857 full tests passed, Ruff0.16.0 src/tests passed, hostverify
MATCH. The first complete QML run passed200 dedicated views plus116 broad views.
A later added assertion exposed a synthetic worker-selection race: holding the
question across a fixture poll made the shared mock executor's last submission a
control read. Final harness captures the actual question worker before waiting;
product behavior was not relaxed. Final readback/diagnostic and the byte-matched
wheel4084340b9be3ddb1ac3b0ca444727d987076c880d7281a1a9e04755d5b68723e
(all60 packaged sources) are preserved with the checkpoint evidence.

Final qualified QML run:200 dedicated views and116 broad views passed with no
errors/binding loops. Both pending layouts were visually inspected, including
local literal markup, separate Sending state and absence of a fabricated answer.
This remains synthetic local Qt/design proof only.


### Session header retention — 20 October

Audit confirmed a consumer gap: list headers survived locally after Session
retention elapsed, and a detail could outlive its parent Session if its individual
entries had later retained_until dates. Protected Core8b221d07 already returns
retention_days on the owner Session list. Its public_session has no separate
wire expiry. The released session_retained rule uses ended_at, interrupted_at or
created_at plus that explicit policy for ENDED/INTERRUPTED; OPENING/ACTIVE remain
exempt. Core persistence restricts policy to integer1..90. Source hashes and
provenance: docs/branding/HISTORY_HEADER_RETENTION_REFERENCE.json.

The Pi now validates and derives a local deadline from those exact fields, with
zoned timestamps and no assumed90-day fallback. Nonempty malformed/missing-policy
responses are unavailable rather than retained indefinitely; empty lists require
no invented deadline. Original response bytes/producer fixtures are unchanged.
List results are rechecked after the GUI queue using the existing monotone clock.
An expired/invalid response clears old list data/cursors without changing current
Runtime or replaying any write.

A header deadline removes its list row and cursor locally. Opening detail from a
known list header carries the earliest known parent deadline into the ephemeral
read window; the entire timeline/search/trail withdraws at that deadline, even if
individual rows last longer. Selected historical context withdraws with it; a
dirty notification ensures the next GUI tick clears its draft even if a getter
already removed the model. Repeated page reads do not extend a known detail's
parent deadline. This does not invent a deadline for direct search/open responses
that contain no retention policy, and is not policy-change/revocation polling or
full session-list revalidation. Those owner reads remain necessary.

Thirteen new tests cover all four lifecycle states, invalid policy bounds/types,
unknown/unzoned headers, original body preservation, delayed GUI admission,
parent-before-entry expiry, rollback/refetch refusal and selected-context notify.
Actual QML probes read a synthetic policy-bound archive list and longer-lived
entry window, expire the parent, and verify list/detail/cursor/context/draft
withdrawal in all five locales on both canvases. Existing native/retained grants
remain separate; no server contract, history write, delete, pairing or audio path.

Validation/package results are preserved under pi-session-header-retention.
Parent4a5a260 passed all applicable CI (24successes/4conditional skips); the new
head requires independent checks. No Core WIP was consumed; its separate current
retention work is not released evidence. Local proof is not HA/Profile/ARM,
installed or physical acceptance. PR111 stays draft.

Local final result:870 full tests, Ruff0.16.0 src/tests and hostverify MATCH.
220 dedicated QML views plus116 broad views passed without errors/binding loops.
Wheel398b3131bac21e2bdb33fe82e55c0b6536f15a80f09be276ed3623927c71e81f
matches all60 packaged sources. List/detail withdrawal was visually inspected
on the actual fixture canvases; no new native simulator or live provider claim.

A final context-fence regression clears the deferred historical-selection notice
when context is invalidated or a new Moment/entry is explicitly selected. An old
header-expiry notification cannot wipe a newer context's draft. Two causal tests
bring the full result to872 passed; updated source/package/QML receipts are kept
with the same evidence directory. No permissions or server writes are broadened.

Final fenced wheel SHA256 475ad76d09c55f1e55f0810263700f4f6460f43b9396bd97701f2737c34a4793 matches all60 packaged sources.


### Pending status copy — final bounded night polish

The Sending caption is no longer duplicated in both the pending question card
and composer dock. Only the dock's Sending copy is hidden while the pending
card is actually visible. When history/Forecast hides that card, dock status
remains available; confirmed, failed and uncertain states are not suppressed.
No transport, lifetime, server contract, string or write behavior changes.

The actual QML harness holds a question, verifies the dock copy is hidden, then
completes acceptance and checks that status returns. A separate synthetic
uncertain response in every locale/layout must leave the dock warning visible,
without a pending or fabricated answer. Broader parity/live/ARM/install gates
remain open. The last full Python suite on parent e87bd08 is872 passed and its
applicable CI passed (24successes/4conditional skips). This QML-only change uses
actual render checks and package verification; no redundant local Python suite
is attributed to the new head. New-head CI is independent.

Final polish verification:230 dedicated actual QML views plus116 broad views,
no errors/binding loops; Ruff0.16.0 src/tests passed and hostverify MATCH.
Wheel dfd6b13d5085413b4b12fd74d18d233126ca39ebade2db13134b6e666c67ffc5
matches all60 packaged sources. Pending/uncertain captures were visually checked
on both canvases. Evidence: pi-session-sending-polish under task visualizations.


### Fresh multi-page archive list — six-hour continuation

The archive already polled every15seconds, but refreshHistory reopened the first
page and discarded loaded pages/reading position. The controller also appended
cached earlier headers on More. The shared client now re-reads every displayed
page from the first owner GET, using only cursors from that new traversal. More
and periodic/manual refresh replace the whole visible list atomically. No old
header survives solely because it was loaded on an earlier page.

Every fresh page requires the same owner revision and explicit retention policy/
revision. Descending created_at/session_id key order, unique IDs, cursor cycles,
per-page20-row bounds and existing expiry are validated. Scope/view/Profile/
foreground loss stops before/between GETs and rejects late GUI results. Conflict,
invalid response or denial withdraws old list data/cursors. No immediate retry
loop or write replay occurs; a later ordinary timer tick can request a new first
page after a failed read. GUI admission still rechecks expiry; known earlier
header deadlines are not extended by refetch.

One local Profile-bound archive-read intent waits for existing control work and
cancels when navigation/context changes. The existing15s timer uses it; active
history still uses its separate owner detail revalidation. Revalidation/More
remember only the first visible Session ID and finite bounded pixel offset, then
resolve against the newly admitted rows after layout. Missing ID -> top; dragging
cancels restoration. Archive rows and More are disabled during their read so taps
cannot silently target a busy controller. No header/body cache is added to the
reading descriptor.

This slice bounds reads and UI memory to5pages of20headers. At the bound the
original server cursor remains incomplete, More is hidden and five-language copy
says the server has additional sessions. It is an explicit consumer limitation,
not complete older-archive/window paging or full Apple parity. Producer authority
is unchanged; source provenance: docs/branding/ARCHIVE_REVALIDATION_REFERENCE.json.

Thirteen new synthetic transport tests qualify fresh earlier-page replacement,
body/header withdrawal, revision/policy/ID/order/cursor conflicts and denial,
100-row aggregate GUI admission, max-page behavior, scope cancellation, Profile
loss between pages, original deadline clamping and wire-row limits. Actual QML
uses real More/timer/navigation on both canvases and all locales, checking limit
copy, changed server rows, retained ID/pixel, missing-anchor top and queued cancel.
Initial diagnostics are preserved: an uncertain-question fixture submitted while a control read was busy; a header deadline assertion ignored ISO microsecond rounding. The final harness drains scoped reads and compares deadline precision appropriately. An actual archive reading-position shift led to layout polishing before capture/restore and a single active-read guard. Stale More clicks at the bound are rejected. Partial local header expiry retains the displayed-page budget for the next fresh traversal; no product rights or admission checks were relaxed.

Source/fixture/package/Qt proof remains separate from HA/Profile/ARM/installed/
physical acceptance. No Core/Apple WIP, model call, history write or new endpoint.
Existing producer8b221d07 remains pinned while other lanes work independently.

Final qualification:885 full Python tests passed, Ruff0.16.0 src/tests passed, hostverify MATCH.262 dedicated actual QML views plus116 broad views completed without errors/binding loops. Both archive layouts were visually inspected. Local wheel597df779624ff595642cd1229ce32d10b830500338bc98ed21ea415bb4667d6f matches all60 packaged source files. Evidence: taskvisualizations/pi-session-archive-freshness. These are local synthetic transport/source/package/Qt results, not ARM, installed or live acceptance.

### Conversation read cancellation between owner requests

The receipt/history route already rejected late GUI publication, but could still
issue a tail or second exact-anchor GET after foreground/Profile loss or End had
superseded its worker. Each conversation GET now checks the captured owner binding,
foreground, its bounded worker ticket and (for a question) question generation,
both before and after the read. The post-acceptance Runtime read is checked before
dispatch too. Refresh and question workers use the same guard; no POST is retried.
An already started request can finish remotely; this does not claim transport
cancellation or cancellation of a server-side question. Ordinary navigation does
not revoke an otherwise valid running question. Existing retained rows can remain
while End is pending; a superseded reader cannot replace them.

Eighteen synthetic controller cases withdraw authority after the active read,
after the tail and after the first anchor, for both question completion and later
read-only reconciliation. Foreground loss, Profile replacement and End are distinct
cases. They assert the exact stopped request sequence, no late new answer and one
explicit POST. An initial refresh fixture accidentally withdrew the contextual
capability; it was corrected to retain the original supported capabilities rather
than loosening the product gate. An initial End assertion confused previously
visible retained rows with a newly published result; the final assertion checks
that a superseded reader cannot change those rows.

This is a bounded consumer safety fix, not continuous Flow, broader private reply
lifetime, a new producer handoff or live cancellation acceptance. Core/Apple WIP
remains untouched. All preceding parity gaps remain open.

Final local qualification for read cancellation:903 full tests passed;66 composer tests; Ruff0.16.0 src/tests passed.262 actual QML views on both formats/all locales completed without errors/binding loops, including existing late-End and receipt reconciliation flows. UI source is unchanged; this is no new visual parity claim. Local wheel157e10199dceb42996aeadc7fef96d2d465157f55a74367a0d8a9336bd1a60af matches all60 packaged sources. Proof: taskvisualizations/pi-session-conversation-read-fences. No ARM/installed/live/physical claim.

### Typed retained contributions in current Flow

Current Flow previously discarded all history2 rows except conversation_user and
conversation_dj. The same fresh owner tail now supplies a separate Saved
contributions/read-only section with playback_observed, admitted historical
dj_moment, dj_publication metadata, dj_silence and conversation roles in canonical
server order. A tail is bounded to20 entries; an exact receipt anchor can contribute
up to20 additional same-revision entries, with canonical identity/content/order
conflicts rejected. Original text, attribution links, dates and retained_until
remain owner-authoritative. Publication/silence placeholders never acquire body
or speech. Native Moments remain a separate independently admitted surface; no
history row becomes current playback, a native grant, media, action or speech.

The readonly history capability controls reading; contextual free-input capability
continues to control composition independently. A client can therefore read valid
retained rows with its composer disabled. Receipt confirmation still uses only
the exact two typed conversation roles/identities, not other retained content.
All retained rows are withdrawn with existing context/Profile/foreground/history
capability and GUI-queue/tick expiry fences. Only metadata reading descriptors
are preserved; the current window is RAM-only. Existing Flow return/scroll logic
resolves any retained card by exact entry ID in the fresh model.

SessionRetainedEntry.qml is shared by Flow and the historical timeline. It keeps
the observed-playback field hierarchy, literal PlainText, source/revision links,
packaged-logo readiness and dates. The historical-screen Ask-about selection stays
there; no new actionable button or authority is inferred for a Flow row. A stable
five-language key labels the separate readonly section. This improves coverage,
not continuous/backward Flow: older chronology still uses the existing explicit
history screen, and native/current cards are not interleaved into an invented
retained timeline order.

Actual screen review found that a released historical Spotify source can lack
the native requires_spotify_attribution flag. Historical Spotify provider/links
now impose the existing packaged-logo+valid-source readiness fence too, including
on the historical screen. A missing qualifying Spotify link fails closed; a
malformed explicit flag is rejected. This is an additional display restriction,
not a new grant. Existing original producer fixture bytes remain unchanged.
Provenance: docs/branding/RETAINED_FLOW_REFERENCE.json.

Initial diagnostics remain separate: a missing Theme import in the extracted
component was fixed; a synthetic traversal incorrectly started at QQuickWindow
rather than its screen item and was corrected. Tests that expected no native
Moments were corrected to explicitly remove native grants from their synthetic
Runtime; historical data is not used to infer their absence. The old long-chat
fixture used26 rows for a20-row request; it now uses18 older+2 new rows. No product
bound or source/admission check was loosened for fixtures.

Core has supplied local documentary review material802c1cce/833c76b2 concerning
full Profile-authorized Pi feature parity and hardware/capability-based audio
availability. It is not a protected consumer release and is not adopted here.
The explicit standalone private response lifetime gap remains open; no20minute
RAM-idle timer is used as a display grant. No audio activation, producer write,
model call, merge, installation or live/physical acceptance follows from this slice.

Final retained Flow qualification:922 full tests passed, including13 new typed-Flow cases and6 historical Spotify attribution cases. Ruff0.16.0 src/tests passed; hostverify MATCH.292 dedicated actual QML views plus116 broad views on both formats/all locales completed without errors/binding loops. Both format captures were visually inspected; the repaired Spotify logo is visible on the mixed retained surface. Local wheelbc6ecf1509307c2c472404e97d157ad602c80d76d151b55dea88e155d9def6e7 matches all61 packaged source files including SessionRetainedEntry.qml. Evidence: taskvisualizations/pi-session-retained-flow. Source/synthetic transport/Qt/package proof only; no live Profile/HA/ARM/installed/physical acceptance. Earlier intermediate test/package/render results and diagnostics are kept separately, not promoted to final source proof.

### Older/newer archive windows beyond100

The former absolute100-header access limit is replaced with bounded read windows.
More still expands the current window through at most5pages of20headers. Older
opens the existing owner next_cursor as the start of another window; Newer reads
the earlier window again. No earlier header bodies are kept. At most32 RAM-only
request descriptors hold start cursor, page budget, original revision/policy
scope, prior keyset boundary and optional visible Session ID/finite pixel offset.
Most recent sessions remains reachable directly even after the return trail's
oldest descriptors are dropped. There is no absolute count of older windows.

Each window refresh re-reads all its displayed pages starting at that window's
server cursor, using fresh subsequent cursors. Same owner/revision/retention
policy, strict keyset order/unique IDs and existing expiry checks still apply.
Local reading metadata never enters the transport. A conflict on a non-first
window causes one fresh first-page GET and clears the old trail/reading target;
five-language copy explains the reset to newest. Denial/malformed data is never
treated as permission to fall back. Empty scan windows have honest local copy.
No session-list anchor endpoint, backward cursor or new producer grant is added.

The actual older/newer/newest buttons share both formats. New windows start at
top; Newer restores only a still-present ID/pixel after fresh layout. Opening a
detail remembers a metadata-only list position; Back queues a scoped fresh read
of that exact archive window before restoring it. Pending reads are cancelled
when the view/Profile/context is left. clearArchive clears list bodies, cursors
and navigation metadata without ending the current Session or replacing its
Runtime. Existing retained detail/source lifetime remains independent.

Thirteen controller cases cover beyond100 access,5-page fresh return, revision/
policy/cursor reset, denial/no fallback, repeated boundary validation, invalid
reading coordinates, missing-ID top, late read after close and bounded32-trail
traversal with direct newest recovery. The real QML probe drives the buttons,
15s polling, detail Back/read position, reset copy and stale click after close.

### Cross-client Forecast revision/scope review

Apple's concrete PR162 review identified a matching Pi defect: same-revision
Forecast text could be re-projected under new Runtime Mood/Presence/Persona/
playback context. Pi now binds accepted content to the existing public fields
selected_mood/mood_revision, selected_presence/presence_revision, dj_persona/
persona_revision, locale, session_direction and exact playback item/source.
No new wire field or producer contract was introduced. The original validity
ceiling/expiry, text-only subset and capability/version gates remain unchanged.

Equivalent repeated reads keep their original deadline. A changed body/title/
summary/order/state or Runtime scope under the same Forecast revision withdraws
it; an older frame cannot seed a new scope. Known Runtime style values cannot
change under the same counter, and independently observed style revision floors
block rollback even if another field is unknown. A Forecast revision observed
with unknown/invalid scope becomes a non-renderable floor, not a grant. Only a
fresh higher admitted revision can recover in the confirmed scope. Ordinary
playback progress/updated_at/paused observations do not fabricate a new scope.

Pure released20-projection fixture bytes remain unchanged. Tests/Qt previews add
explicit synthetic public Runtime-style envelopes, not a new producer Runtime
claim. This correction was communicated to Apple with exact protected Core8b
source references and no contract-change proposal, model call, budget transfer
or install/deploy implication. The native imagery catalogue at3cfa5512 reported
by Apple is not adopted as Pi media permission. Provenance and owning consumer
review: docs/branding/ARCHIVE_WINDOWS_FORECAST_SCOPE_REFERENCE.json and Pi PR111.

Current Core capability-doc checkpoints802c1cce/833c76b2/45d3eead/512a8c3c remain
local review material. Their broader full-app/hardware-capability product
reconciliation is not a protected consumer release or audio activation here.
Standalone private answer lifetime remains an independent Core contract gap.

Actual tablet review caught early list-position restoration after a short detail
layout changed to a longer archive list. Restoration now waits for stable layout
and content extent, verifies the applied position, and stops after at most8
32ms timer attempts. A missing entry falls back to top; touch/view/Profile changes
cancel immediately. Reset-to-newest copy was moved above the rows after actual
phone review found it below the fold. No body is stored in these descriptors.

The immutable Forecast comparison keeps a digest rather than a second prose copy,
and clears it/scope metadata on expiry/withdrawal. Explicit expired/withdrawn/empty
reads can keep their original revision and terminal state; this is invalidation,
not permission for changed ready content or same-revision renewal. Unknown scope
can retain only a non-renderable revision floor. Original pure producer bytes
remain unchanged; no image/audio grant is added.

Diagnostics are preserved separately: partial edit-template mismatch, archive
detail Back introducing a queued read before an old navigation fixture, QObject
versus visual delegate traversal, an absent search fixture model during mixed
locale/polling (not claimed as a confirmed live bug), actual tablet ID/pixel race,
and the old harness waiting for only its control reads rather than the new bounded
position phase. Fixtures now explicitly disable only automatic3s/15s running
bindings and invoke their actual callbacks; production polling behavior is
unchanged. The harness still permits at most3 control jobs and separately waits
for the bounded layout phase. Search/navigational assertions were not weakened.

Final combined qualification:962 full tests passed, including13 archive-window cases and54 pure Forecast receiver cases plus3 current-controller scope cases. Ruff0.16.0 src/tests passed; hostverify MATCH.386 dedicated actual QML views plus116 broad views completed without errors/binding loops on both formats/all five locales. Real QML buttons/timer callbacks prove beyond100 access, fresh window revalidation, ID/pixel restoration after detail, top-visible reset copy, context close, Forecast scope withdrawal/fresh recovery and Persona uncertainty. Local wheel9a8a7bd4ca0f7fe692ce18935d2285379a709336e7d4b86d4aeed3aa237eb45d matches all61 packaged sources. Source/synthetic transport/package/Qt proof only; no ARM/installed/live Profile/HA/physical acceptance.
Evidence: taskvisualizations/pi-session-archive-windows-forecast-scope.


### Ask about a retained contribution directly from current Flow

Saved-contribution cards now expose the existing localized Ask about action when
current explicit Profile/composer and attribution gates allow it. The actual
shared card opens the current composer without changing tabs, navigating to an
archive or replacing active Runtime. Existing unsent draft is preserved. It sends
the existing selected_entry reference with its original Session/entry IDs, while
conversation_context.session_id remains the active Session. The released Core
contract177–207 owns validation and placement; this adds no endpoint or permission.

The local selection records only its model origin, not body/grant data. A Flow
selection must still occur in fresh retained_flow for the current Session; an
old separate timeline cannot keep it alive. A detail-origin selection continues
to use its own fresh timeline. Source removal/expiry, Profile/foreground/capability
withdrawal and End clear pending/draft through existing fences. Original selected
ID/source is also checked immediately before a queued POST without waiting for a
GUI timer. A started server request may finish; there is no write replay or
fictional cancellation. Buttons disable during an existing question/control read.

Design comparison uses protected Applee106a467 SessionTimelineScreen525–551,
which selects the entry reference and focuses the active composer. Pi keeps its
explicit shared button and touch modal; exact native geometry, full Flow order,
media/actions and broad private/standalone lifetime remain open. Sources/hashes
are in docs/branding/RETAINED_FLOW_SELECTION_REFERENCE.json. All six-kind request
cases are explicitly synthetic; released producer bytes are unchanged.

Final retained Flow selection qualification:980 full tests PASS (18 new cases), Ruff0.16.0 src/tests PASS, current shared-root hostverify MATCH.426 dedicated actual QML views plus116 broad views completed without errors/binding loops on720x720 and1200x1920/all five languages. Both new composer layouts were visually inspected against existing native references and pinned Apple source; exact inline/native geometry and glass effects remain open. Wheel32edb508939bdccb7ec3b09a2592e935912c6ebaed5408da6878aff7139cc68f matches all61 packaged source files. Evidence: taskvisualizations/pi-session-retained-flow-selection. Source/synthetic transport/Qt/package only; no ARM/installed/live HA/Profile/physical qualification. Diagnostics preserve an initial test End call missing its required Session-ID argument, a fixture using single-result visual lookup as an iterator, and hostverify's obsolete default repository root; corrected explicit shared-root verification was MATCH. Product gates were not loosened for fixtures.


### Continuous reading within bounded saved-history windows

Current-session history and archive detail now have More when reading from the
chronological first page. It shows fresh first/next pages below one another,
through at most5 pages of20 rows. Each extension and15s/manual revalidation starts
a new owner read at the first page and replaces the entire visible prefix
atomically. No old first-page body is appended to a new later page. Same root
revision, canonical increasing order/unique IDs,20-row wire bounds and cursor
cycle checks are required. Any denial/conflict/malformed page clears the prefix.

At100 current bodies, localized copy points to the existing Next contributions
control. It continues beyond100 using Core's existing forward cursor. Previous
can re-read the former prefix and restore a still-retained ID/pixel; the existing
32-descriptor trail stores only page budget and reading metadata. Revision drift
uses the existing fresh visible-anchor fallback and clears the old trail. No
backward cursor or unlimited body cache is created. First remains available.
A non-renderable local marker can only come from this reader; unknown wire
_prefix_pages never changes the navigation budget.

Existing per-GET Profile/view/foreground/binding/control-ticket checks, GUI queue
expiry, source attribution, known parent retention and question-context fences
still govern. Runtime is not replaced by these reads. Native/current grants are
not mixed into the chronological saved prefix. This improves continuous retained
reading, not complete newest-first/native Flow interleaving or media/action rights.
Source hashes and limits: docs/branding/HISTORY_READING_WINDOWS_REFERENCE.json.

The latest protected Apple head observed via API is471fa6a4, PR159 Golden
integration release checks. It does not change this Pi history contract or
release PR162 imagery; it is not permission to run model/Golden/provider calls.
Pinned UI design remains e106a467 and protected Core remains8b221d07.

New host qualification issue: shared-root --verify now reports one required
maintenance.verification_artifact_retention DRIFT. A read-only inventory found
seven old ignored Core/receiver verification files (six videos and one preserved
zero-byte lock). They were not deleted/moved/modified; the Core owner received
one concrete report. This is kept separate from passing local product/Qt checks;
current host MATCH is not claimed, nor any release/install/live acceptance.

Final product/source check:1000 full tests PASS, including20 new history-prefix cases. Ruff0.16.0 src/tests PASS.100 focused actual current/archive history-window QML views plus426 Session/composer regression and116 broad views completed without errors/binding loops on both formats/all five locales. Both format reading/limit captures were visually inspected. Wheel a443092a4155b4e07aa41d75253c37a1ba9e03e087c0d54e6830c42fc60263f8 matches all61 packaged sources. Evidence: taskvisualizations/pi-session-history-reading-windows. Current host qualification is separately DRIFT for seven expired ignored Core/receiver verification files; no host MATCH, cleanup or qualified delivery is claimed. No ARM/installed/live HA/Profile/physical acceptance. Diagnostic fixture edit-template and QML return-type failures are preserved separately; final focused harnas uses QVariant correctly and hides only its fixture language toast.


### Current-artist Forecast pixels (bounded consumer subset)

The shared Forecast view can display one producer-granted current Spotify artist
image while the exact active Session is playing. Existing Forecast text admission,
explicit private personal/household Profile, owner binding and current item/source
are required. This does not enable the legacy private-session setting. The image
lives only in RAM and disappears on hide, source/scope/lifecycle/foreground loss
or the earlier original Forecast/asset deadline. Equal/lower changed revision
cannot rebind withdrawn pixels; reused asset expiry never extends. No new image
preparation POST, model/provider lookup or producer right is introduced.

The Forecast managed-art route is specifically headerless; a fresh transport sends
no bearer/device/Profile/cookie/netrc/proxy credentials. It uses only the configured
HA origin, refuses redirects and external/raw CDN URLs, and accepts bounded static
PNG/JPEG after MIME/magic/size/real Qt decode checks. Ordinary Session media/image
has a different paired-Profile authorization contract and is not loaded here.
One worker retains at most one latest desired request, with 32 attempts per Session
and no automatic poll retry. Already-started HTTP can finish after End; its pixels
cannot publish. QML receives a RAM data URI, disables caching, preserves aspect
ratio and displays the canonical Spotify source/packaged mark without crop/overlay.
Failure keeps Forecast text. New accessibility copy uses i18n in all five locales.

The 20 original protected Core8b Forecast frames are unchanged (SHA909c9bc4...),
replayed at their original expired fixture clock. Test bytes are the original
owned synthetic artist PNG from protected Core, not a licensed artist photograph.
The actual QML harness labels Runtime/revision/short-expiry overlays as synthetic;
it exercises real transport validation, image decoding, visibility and withdrawal
without network/HA/provider/model calls. Source hashes, route policy and limits
are in docs/branding/FORECAST_IMAGE_REFERENCE.json. Broader Session artwork,
contextual/upcoming/two-image Forecasts, media/actions and exact native layout are
still open. No ARM/install/live Profile/HA/physical acceptance is claimed.


Final current-artist image qualification:1072 full tests PASS (72 new image cases),
Ruff0.16.0 src/tests PASS.50 new image views +426 Session/composer +100 history-window
+116 broad actual QML views (692 total) passed without errors/binding loops on
720x720 and1200x1920/all five locales. Ready and expired captures were visually
inspected on both formats; original synthetic pixels are an opaque color block,
not a real artist photo/native visual fidelity claim. Wheel
fd6b8f76eb4124cb06d9cea8d269f1027bc6b0ccc0274b1abf602df9be447960
matches all62 packaged sources. Evidence: taskvisualizations/pi-session-forecast-images.
After a concrete Core-owner restoration receipt, independent qualified read-only
hostverify returned MATCH. The first restricted verification could not inspect
host configuration and reported11 differences/1unverified; both logs are retained.
Pi did no cleanup or changes to other-lane evidence. This supersedes the prior
retention DRIFT observation only for this fresh host readback. Draft source/package/
synthetic transport/Qt proof remains separate from ARM/install/live/physical proof.


### Forecast reading position during image changes

A late image or image-only expiry no longer pushes a currently read Forecast
section to another pixel. Before pixel mutation, one RAM-only descriptor records
Session/Profile, current Forecast revision, the existing section ID and finite
bounded offset. After layout it looks up only the still-admitted section, settles
within8x32ms and clamps/validates the position. No prose/pixel/grant is cached in
this descriptor. Top/image-only reading is not automatically followed. A new
revision, missing section, hide/context loss or touch movement cancels recovery.
Actual movement also cancels a queued callback; stale callbacks cannot restore it.
The original pixel/text expiry and authority gates are unchanged.

Three new notification-order tests prove capture precedes actual pixel insertion
and removal, including getter/tick expiry. Two additional real-file tests prove
the application log filter redacts relative/absolute managed Forecast URLs even
when urllib3 logs DEBUG messages without token/bearer marker words. Ordinary
request diagnostics remain readable. This repairs a concrete capability-link
leak in DEBUG logging; it changes neither transport auth nor grants.1077 full tests and Ruff0.16.0 src/tests
pass.90 actual image/reading views +426 Session/composer +100 history-window +116
broad views (732 total) pass without errors/binding loops on both formats/five
locales. Long reading fixtures repeat original prose to3000 chars per section,
explicitly synthetic within existing wire bounds. Real injected Qt touch proves
both active-drag suppression and queued cancellation; only the fixture extends
one layout callback to500ms so a real drag deterministically starts before it,
then restores the production32ms interval and tests a late callback. Initial
harness private-ID/visual traversal/short touch sampling diagnostics are retained.
A superseded broad run failed the existing fixed-delay current-reply pixel check;
its cause is unestablished. The closed-source run passes the same strict check
on both formats without changing its tolerance or wait; added geometry-only
diagnostics remain in the harness.
product gates were not weakened. Both format late/expired layouts were inspected. Explicit top-of-page and
unchanged-refresh assertions preserve position without introducing new follow.
Wheel bc24287d52644feda629c3fed83a53657ac31e7d9c77595a9d6f4a3db4b80342
matches all62 packaged sources. Evidence: taskvisualizations/pi-session-forecast-reading.
Host qualification last independently MATCH after owner evidence recovery; no
new cleanup, install, ARM/live HA/Profile/physical acceptance is inferred. The
README-only parent also adopts protected Brand V2 wordmarks and the explicit
full-app/Profile target without activating audio. New reading/source provenance:
docs/branding/FORECAST_READING_REFERENCE.json and README_REFERENCE.json.


### Prepared current-Moment artwork (shared compact/tablet client)

A current admitted native Moment may now show one already prepared Spotify
track/album/artist image, with original source link/logo and localized accessible
alt text. The consumer requires advertised session_artwork v1, explicit private
personal/household Profile, exact Session/current native ID and original finite
native/source grant, plus a typed prepared current-display media grant. Historical,
flow-only and playback-thumbnail metadata do not acquire current image rights.
There is no preparation POST, provider lookup, CDN fallback, playback/history
promotion or automatic retry. Unknown/loading/invalid artwork leaves native text.

The normal paired device/Bearer/Profile GET is restricted to the configured HA
session/media/image path and exact Session. Ambient cookies/netrc/proxy credentials,
redirects and fallback authentication are disabled. Forecast's existing managed
headerless route remains separate; only the pure static decoder and bounded worker
mechanics are shared. Original asset/native deadlines, equality-only revisions,
content/reference fences, withdrawal latches and context/foreground/End checks
remain mandatory. Static PNG/JPEG is bounded to2MiB,2048 per side/4M pixels and
must decode to its declared dimensions. Pixels stay RAM-only, without QML cache,
crop, overlay or animation. One worker/latest lease and32 attempts per Session are
bounded; an already started HTTP read may finish after withdrawal but cannot publish.
Managed paired-art paths are now also redacted from file/stderr DEBUG logs.

Pinned Apple e106a467 MomentCard places artwork before text. Its SessionArtworkView
uses an uncropped100pt maximum dimension, leading alignment, accessible alt text
and source branding. Pi adopts that order and100 logical-pixel maximum with its
existing glass card; exact SF/tint/backdrop/native pixel fidelity remains open.
Late insertion/expiry preserves the currently read native body by ID/pixel when
that body crosses the upper reading edge. The RAM-only descriptor stores no prose
or grant. Existing history-return descriptors and explicit question follow retain
priority; touch/context withdrawal cancels queued restoration. Actual startup
visibility is synchronized when a Session page starts already selected.

1147 full local tests (68 new artwork cases plus2 extra log-route variants), Ruff
src/tests and fresh host MATCH pass.120 actual Moment-art views +90 Forecast +426
Session/composer +100 history windows +116 broad views =852, across five languages
and both720x720/1200x1920 layouts, without errors/binding loops. Both ready/expired
format captures were inspected. Long reading text is explicitly synthetic repeated
12-character lines, bounded to3000 chars. Fixture artist current-display permission
is explicitly synthetic; the original flow-only permission is separately refused.
The unmodified protected transport file retains its old LOCAL_UNPUBLISHED label:
this is consumer conformance against protected implementation/capability, not fresh
Runtime/provider or narration qualification. Synthetic owned color pixels are not
artist-photo/album-license or exact visual-parity proof. Original200 native frames
and media transport bytes remain unchanged.

Wheel 0bbb3b0ab30c64624845f7f77baffa301880b8d99e2dc4573218d825486b59cb matches all63 packaged sources. Evidence:
taskvisualizations/pi-session-moment-artwork; provenance
SESSION_MOMENT_ARTWORK_REFERENCE.json and artwork-provenance.json. Diagnostics
retain the original flow-only fixture mismatch, startup visibility finding and
long-body test corrections (ordinary paragraph was too short on tablet; current
visual body must be re-resolved after model refresh). No product admission or pixel
tolerance was weakened. Earlier Forecast/history/composer evidence remains separate.

This is one prepared current native-image slice. Preparation, historical/flow-only
media, reactions/actions, contextual/upcoming/two-image Forecast, broad private
composer lifetimes, full Flow placement/order, full playback header/output controls,
exact native glass and hardware performance remain open. No merge/release/install,
pairing, HA/provider/model effects or ARM/installed/live/physical PASS is inferred.


### Feedback destination under More

Feedback now follows Privacy in the common Apple More order. Both Pi formats
show an explicit glass confirmation page with Back and the selected More tab,
localized in en/nl/de/fr/es. An explicit Open GitHub issue action opens a draft
for the verified issue-enabled Pi repository. It includes only a static localized
title and fill-in template. No device identity, Profile, Session body, logs or
other diagnostic snapshot is exported; no issue is submitted automatically.
An unavailable browser shows a localized status. Opening this page has no
network effect, and the native-sheet-to-Pi-page geometry remains an adaptation.

The protected Apple e106a467 MoreView/FeedbackPromptView and model URL/body
builders were read independently. Pi retains the explicit draft/review interaction
while adapting the target repository and omitting automatic app-context export.
Browser opening in tests is intercepted, including actual QML clicks; no real
browser, issue publication, private credential or HA/provider/model effect occurs.

1157 full tests and Ruff0.16.0 src/tests pass. Ten new tests verify exact encoded
query fields and no supplied private config/Session values for five languages,
including true/false browser outcomes.150 actual broad QML views (34 Feedback)
pass without errors/binding loops on720x720/1200x1920. They include actual menu,
Back/tab, draft-open and unavailable-browser states; both layouts were inspected.
The prior96d852Session/art/history/composer views remain separate qualification,
not added to this UI-only count. Wheel 766c12f2126238dfa48b2a70c36a7c4a3338a0fe6687f62a3a53127205f94bd8 matches all63 packaged sources.
Evidence: taskvisualizations/pi-feedback-destination; FEEDBACK_REFERENCE.json.
Initial test import ordering was corrected. Diagnostics retain equivalent
translation formatting rejected by the existing implicit-concatenation lint rule; final
format uses one literal per value, with no string changes or rule suppression.
Host last freshly qualified MATCH during parent96d source work; no repeat host
mutation, installation, ARM/live HA/Profile/physical acceptance is claimed.

A separate protected8b Persona touch-reaction audit confirms a dedicated paired
operation1 owner/epoch/receipt and confirmed Settings3 context/output are needed.
The existing settings3/operation receipt route is not that dispatch owner. A
future text-only reaction consumer is possible under its actual contract; this
page does not implement it or activate audio. No producer/API WIP was adopted.
General Session/Flow/media/private-lifetime and exact native/hardware gates stay
open. This feedback step does not merge, release, install or pair the shared app.


### Explicit preparation for one current native Moment

A shared Load image button now performs the existing owner-authorized preparation
for one exact current native Moment, only after an explicit click. It requires
artwork v1, explicit personal/household private Profile and the original finite
native/source reference. It neither guesses subject/account/CDN nor targets a
retained entry. It is independent of free-text input authority. The normal paired
POST contains only version1, Session and one original moment_id target plus normal
identity. No preparation is triggered by reads, visibility, reconnect or retry.

The POST response never grants local pixels. After its exact envelope/target is
checked, a fresh owner active GET must independently retain the same original
Session/current native reference. Only its bounded media metadata is imported;
Runtime values, conversation, selection and draft are not replaced. A fresh
validated source withdrawal clears only a still-original client context; a
superseded result cannot clear a newer one. Image ready/current/subject/attribution,
original native/asset deadlines and the existing paired byte decoder remain
mandatory. Flow-only/unsupported media keeps valid native text with typed feedback.
Malformed/unavailable/uncertain optional results preserve text/draft; owner denial
withdraws private context. Refresh never replays the POST. No new audio, model,
history, playback, permission or producer field is introduced.

One dedicated max1 preparation worker keeps the existing End/control worker free.
A real held-POST Qt subprocess proves End dispatch/completion before that POST is
released, with no follow-up read/publication afterward. Other control/input reads
are gated during the one pending preparation; client POST24s/GET8s are bounded.
Hide/Profile/foreground/source/context/deadline cancels queued dispatch and clears
the stored request descriptor; already started HTTP may finish. Ready completion
also clears metadata. Optional status metadata is retained only until the original
native deadline, without body/grant cache or deadline renewal. Four new i18n keys
cover Load/loading/unavailable/uncertain in all five languages. The explicit button
is a Pi adaptation, not an asserted exact Apple gesture.

The new load-button layout exposed a strict native-body pixel failure during
image-only expiry. The initial diagnostic also mishandled a null descriptor;
its exact underlying layout timing is not asserted. The actual product now uses
bounded8x32ms polished-layout settling/clamp/verification for moment_text only,
with the existing3px qualification tolerance unchanged. A cleared late callback
is inert. Original history/current-reply restore paths and touch/context/explicit
reply-follow cancellation remain. Final actual QML covers late arrival, expiry
and cleared late callbacks on both formats. Intermediate logs/captures remain.

1188 full tests and Ruff0.16.0 src/tests pass, including31 new preparation tests.
The no-replay refresh case keeps artwork capability available, rather than passing
because capability disappeared.936 closed-source actual QML views comprise170
Moment-art/preparation,90 Forecast,426 composer,100 history windows and150 broad
views, across five locales/two formats, without errors/binding loops. Both format
pending/ready/uncertain/unavailable layouts were inspected. The source/wire joins,
current-artist flag, clocks, POST and follow-up active response are explicitly
synthetic; no Core/provider execution or artist-photo/license quality is claimed.
Original200 native frames and protected media bytes are unchanged, including the
historical LOCAL_UNPUBLISHED label. Wheel bfaa489e7bbd48a16085f060973eb2a438416aef667886edf7b6917b5d674988 matches all64 sources.
Evidence: taskvisualizations/pi-session-artwork-preparation;
ARTWORK_PREPARATION_REFERENCE.json pins the protected8b implementation/contracts.
Fresh qualified host readback returned MATCH; no cleanup or host mutation occurred.

This delivers current-Moment preparation, not retained/historical preparation,
flow-only art, reactions, broad media or full Apple parity. General Flow/order,
private/standalone lifetime, full playback header, exact native glass and physical
performance remain open. No merge, release, install, pairing, live HA/Profile,
provider/model, ARM or physical acceptance follows from these local results.


### Current Flow: newest saved contribution and own turn first

The actual shared Flow now places the pending local question and the admitted
current-only question/answer before saved contributions. Only this Flow's retained
presentation is reversed, matching pinned Apple e106 Timeline lines510–525.
The owner/controller list stays in canonical increasing order; chronological
history first/next/prefix windows keep their existing order. ID/references,
receipt confirmation, readonly versus native rights, RAM-only lifetime,
foreground/context/expiry and media admission are unchanged. No transport,
write/replay, producer field or new strings are introduced.

The real QML harness checks displayed card Y-order, unchanged canonical model
order, pending/current response above visible saved cards, and the exact confirmed
assistant ID at the12px reading edge on both formats/five locales. An obsolete
fixture assertion required scrolling more than100px to a newest answer; it now
checks that exact ID/pixel target instead. Existing history return same-ID/pixel,
missing-entry withdrawal and actual touch cancellation assertions stay intact.
The new current-only/saved geometry join is explicitly synthetic and grants no
additional current/private/history authority. Its first attempt reused a fixture
that had already been emptied; a fresh original tail fixture is now copied.
Both diagnostic runs remain in the evidence folder.

This closes the audited own-turn placement and retained Flow presentation-order
gaps. Playback/header grouping and complete backward/continuous current Flow
remain open local work. Core8b still exposes tail/anchor plus chronological
first/next, with no beforecursor. Broad private/standalone lifetime, richer media/
actions, exact native glass/SF glyphs, ARM/installed/live/physical acceptance remain
open. FLOW_PRESENTATION_ORDER_REFERENCE.json pins the exact source basis.


Final local QML qualification:946 actual views (436composer,170Moment/artwork,
90Forecast,100historywindows,150broad), five locales/two sizes, no QML errors or
binding loops. Newest-first card Y-order, exact12px confirmed-answer focus,
pending/current before saved, and existing history same-ID/pixel, withdrawal,
touch and image-reading cases pass. Both formats were visually inspected.
Ruff0.16.0 src/tests passes. Product Python code is unchanged: the last full
local Python suite remains1188 on parent660cc151 and is not claimed rerun on this
QML-only candidate. The prior qualified-host MATCH is likewise a parent
measurement, not a new host check. Wheel900b213e70eb46a95a39c70d2c5bff3285978af4c120e41963cbdda593869f0b
matches all64 packaged sources. Evidence:taskvisualizations/pi-flow-presentation-order.
All results are local synthetic-transport/Qt/package, not live HA/Profile, ARM,
installed or physical acceptance. Exact new-head CI is recorded separately.


### Music context before the native Moment; first-visible Flow reading anchor

The shared current Flow now places its existing admitted Runtime music metadata
before native Moment cards, following the pinned Apple e106 currentHeader ->
NativeSessionMomentsView musicContext/currentCard hierarchy. The card contents,
source/logo readiness, metadata identity, native/image admission and deadlines
are unchanged. This adopts container order only; full native album artwork,
gestures, playback controls, favorites/output volume and exact glass stay open.
No unsupported playback artwork URL is promoted into the current-Moment grant.

A new actual QML probe exposed a presentation-related reading bug: with current
reply and saved cards both visible, rememberFlow chose a saved conversation353px
below the reading edge instead of the current reply crossing the top. The function
now compares actual visible Y positions across admitted native, retained and
current-only cards and stores the topmost intersecting card. The one descriptor
still contains only Session/Profile/kind/ID/finite bounded offset, with no body,
grant or deadline cache. Restoration still looks up current admitted models;
missing ID, scope/context/foreground loss and touch cancellation retain their
existing behavior. Playback-only/pending-card reading positions remain open.
Explicit reply-follow and artwork-body reading restoration keep their own gates.

The current-only/saved join is explicitly synthetic UI geometry, not extra
producer authority or live Runtime evidence. The failing first720x720 probe and
intermediate header-only qualification are preserved separately. New actual
geometry checks cover music before Moment on every applicable artwork fixture,
plus first-visible current-response identity with both reply and saved content
visible, across five locales/two sizes. CURRENT_HEADER_ORDER_REFERENCE.json pins
the exact native source and limits. No new strings, transport or producer fields.


Broad QML review found the initial music-before-Moment swap placed the720px
Moment card358px below the reading edge, failing the original half-viewport
first-fold gate. The compact header now keeps title, artist/album, progress/time
and a clickable44px Spotify source in two rows; tablet artist/album stay on
separate lines. No metadata is dropped or elided. The original150-view broad
harness and visibility threshold are unchanged and pass on the compact header.
This is a Pi-responsive metadata adaptation, not complete native artwork/control
header parity. Superseded geometry/package/proofs remain separate.


Final qualification for current-header order and first-visible reading:956 actual
QML views (436composer,180Moment/artwork,90Forecast,100history,150broad), five
locales/two formats, no errors/bindingloops. Both music-before-Moment layouts and
the overlapping current-response/saved reading case were inspected. All existing
ID/pixelreturn/touch/withdrawal/expiry/image-reading checks remain. Ruff0.16.0
src/tests PASS; fresh read-only qualifiedhost MATCH during this resumed slice.
The last full local Python suite remains1188passed on ancestor660cc151; it is not
claimed rerun for this QML-only change (immediate parentca5b22f).
Wheel894862fa5dafbe5afa2c6756cd8688f1a89ae94962ebb23bb1ae4aca73e31ce9
matches all64 packaged sources. Evidence:taskvisualizations/pi-session-current-header,
with failing/intermediate results kept separately. The first broad run
found a true720px first-fold regression (Moment card358px below the reading
edge). Compact metadata combines artist/album and progress/time, with
Spotify attribution beside the title. Tablet details stay separate. All fields
remain; original first-fold tests were not changed or weakened. No liveHA/Profile, ARM,
installed, provider/licence or physical acceptance follows. Exact-head CI separate.


### Playback dispatch prerequisite — 2026-10-20

A reproduced consumer defect could dispatch a command once over WebSocket and
then again over HTTP after losing its acknowledgement. A before/after actual
HAClient test with a synthetic socket proves parent8b683 sends next once plus
one HTTP command; the new source sends next once, no HTTP command, and reports
unconfirmed in the selected locale. The send latch is set before send(), since
partial transmission may precede an exception. Writes also do not fall back after
an explicit rejection, malformed/empty acknowledgement or decode failure. Missing
capability, connection/auth failure before application dispatch and explicitly
allowlisted reads retain their established HTTP fallback. Unknown/malformed
command types are conservatively non-replayable. Confirmed writes keep the fast
path. No raw server error or prompt is included in the new localized status, and
this error does not clear pairing. Read-only source provenance is pinned in
PLAYBACK_COMMAND_DISPATCH_REFERENCE.json. No new producer field or grant.

This is a necessary transport fix before adding Session playback controls, not a
new controls/favorites/volume UI or a general server exactly-once guarantee.
HTTP redirect/context behavior, queued Session-control cancellation and current
Profile/capability gating still need the next dedicated consumer slice. No live
playback, HA, provider, model, ARM, installed or physical test was performed.

Local final qualification:1258 full tests passed, including70 new boundary cases;
Ruff0.16.0 src/tests passed and fresh read-only qualifiedhostverify MATCH. The
previous1188 tests were ancestor evidence; this full suite is on the new source.
UI/QML files are unchanged, so the prior956 actual views on8b683 remain separate
historical UI evidence; no new screenshots or visual parity claim. Wheelb957231aaef9f25dbfc7df55018a4f29a824502b26487eeb8dbdb5c31c5707a9
matches all64 packaged sources. Evidence:taskvisualizations/pi-playback-dispatch-no-replay,
including actual before/after readbacks and reproducible socket probe. Initial
lint findings and prior1255-test intermediate run are retained separately.
