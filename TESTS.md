# Tests

Install development dependencies:

```sh
python3 -m pip install -e ".[dev]"
```

Run the full suite:

```sh
python3 -m pytest
```

Run syntax/package smoke checks:

```sh
python3 -m compileall src tests
QT_QPA_PLATFORM=offscreen python3 -m djconnect_pi.app --windowed --exit-after-ms 1500
```

Run the autonomous Home Assistant contract fixture:

```sh
node Tools/http_e2e_contract.js
node Tools/websocket_e2e_contract.js
node Tools/validate_ha_contract_fixture_security.js
```

The fixture is based on the Home Assistant `pcvantol/djconnect` contract files:
`custom_components/djconnect/const.py`, `custom_components/djconnect/http.py`,
`custom_components/djconnect/api_handlers.py`,
`custom_components/djconnect/websocket_api.py` and the relevant HA tests. It
starts and stops itself on `127.0.0.1` with a dynamic port and keeps VibeCast
HTTP-only unless HA advertises a websocket command for it.

## Coverage Areas

- config creation, persistence and device ID backfill
- English/Dutch/German/French/Spanish translation key parity, placeholder
  parity, QML key coverage and selected user-facing copy checks
- Home Assistant pairing/status/command payloads
- Home Assistant command payloads include `device_id` and
  `client_type=raspberry_pi`
- Home Assistant WebSocket fast-path coverage for default-on config, the
  user-disable setting, `/api/djconnect/v1/websocket/session` bootstrap with
  DJConnect bearer auth, in-memory short-lived token caching, capabilities
  dispatch, redacted diagnostics, one-shot HTTP fallback and secret-safe logs
- Ask DJ capability payloads advertise text input and structured actions, while
  voice, TTS and local audio remain unsupported; actual composition additionally
  requires the exact contextual dialogue/history contracts and explicit owner Profile
- Ask DJ, Track Insight, Music DNA and Music Discovery payloads propagate
  language/locale, Pi identity and optional Music DNA context without adding
  local voice, TTS or profile aggregation
- Track Insight request and response coverage for
  `/api/djconnect/v1/track_insight`, canonical `client_type=raspberry_pi`,
  language/locale/mood headers, current track metadata, direct and wrapped
  response decoding, no BPM/key/model fields, no-track/rate-limit retry states,
  stale analysis clearing, backend visualisation/visualization/visualizer
  decoding, visual-only fallback rendering from existing response fields,
  visualizer replacement on new insight responses and secret-safe logging
- Ask DJ history polling uses bearer auth, Pi identity headers, the revision
  cursor and pairing/auth/version guards with quiet backoff on unavailable
  backend states
- Ask DJ QML renders assistant, system, status and other-client user messages
  plus HA-provided action buttons, without typed prompt input, send-message
  controls or local-only history clear; the confirmed clear button calls the
  backend history clear route, empties local bubbles only after success and
  preserves them on backend errors
- Ask DJ action taps send only the structured action payload through the normal
  HA command contract
- Music DNA profile parser coverage for disabled profiles, enabled summary-only
  profiles, optional dashboard blocks, hidden empty cards and hidden
  `eligible:false` blocks
- Music DNA settings and clear endpoint coverage, including enable/disable
  payloads, confirmation-driven touch actions, backend-preserved enabled state
  after clear and compact refresh/disabled-label behavior
- Music DNA websocket coverage for profile/settings/clear and HTTP-only
  coverage for export/import even when Music DNA websocket routes are
  advertised
- Music Discovery gating coverage so disabled Music DNA opens consent/empty
  state, consent accept enables Music DNA before loading the feed and consent
  reject shows the compact gating block
- Music Discovery parser coverage for backend-provided `sections[].items[]`
  recommendations with artwork, opaque section labels/IDs, backend-order
  preservation, no top-level legacy item or recent-history fallback rendering,
  and direct backend quality, reason and `reason_sources` propagation
- Music Discovery QML coverage for one-item-per-row recommendations, taller
  passive feed cards, Play Now-only playback routing and the full-screen
  Waarom reason details overlay
- Music Discovery HTTP and websocket contract coverage for feed, refresh and
  Play Now/feedback endpoints/message types, including `client_type=raspberry_pi`,
  `device_id`, `client_id`, optional `music_dna_key`, `section_id` and
  `discovery_item_id`, with no local `uri`/title/action reconstruction in the
  websocket play payload
- autonomous Node.js HA contract fixture coverage for pair, status, command,
  event, voice, Ask DJ, Music DNA, Music Discovery, Track Insight and VibeCast
  HTTP routes; HA-style websocket auth/session bootstrap; advertised websocket
  command dispatch; HTTP fallback expectations; and redaction checks that keep
  tokens, proofs, APNs/install identifiers and bearer secrets out of fixture
  state/output
- local Client API info, pairing-info, pair, command, DJ response auth and mDNS
  TXT properties
- Raspberry Pi-specific local Client API restart/shutdown endpoints, including
  bearer-token auth, optional device-id header validation and JSON responses
- mDNS discovery is suppressed while the Pi is paired and can return after
  pairing is reset/forgotten
- separate Client API daemon event bridges for queued HA commands and DJ
  response toasts
- installer/systemd contract for separate API and touch UI services
- systemd startup contract that the touch client pulls in the updater service
  on boot/start before the UI process starts
- installer contract for the narrow reboot, shutdown and update-check sudoers
  rule used by the touch/web UI, including absolute `systemctl` paths and
  `visudo -cf` validation
- web portal contract for save-on-change Settings, warning-styled reboot,
  refresh busy states, clipboard feedback and newest-log scrolling
- touch UI contract for Settings power/update actions, output-device "Geen",
  warning-styled reboot, wrapped Logs text, macOS-style toast presentation,
  queue `play_context_at` routing, Ask DJ manual-refresh toast feedback,
  playlist item command routing, mood selection and automatic return-to-now
  settings
- release bundle contract for including docs, systemd units, `scripts/install.sh`
  and a bundled wheel without the loose `src/` app source tree
- repo-only OS bootstrap contract for Raspberry Pi OS Lite 64-bit, modern
  HyperPixel KMS DPI overlay setup, root filesystem expansion, persistent 1GB
  swapfile, boot-time filesystem repair checks for unsafe power-loss recovery,
  timezone, NTP time synchronization, SSH, apt full-upgrade, minimal X11/Qt
  runtime dependencies, Raspberry Pi Connect and localhost-only x11vnc
- installer contract that OS bootstrap tasks stay out of the app release cycle
- technical design decisions documentation is linked from README and contains
  dependency/style/release-maintenance sections
- release hygiene points to canonical `pcvantol/djconnect/SYNC_PROMPTS.md` and
  `pcvantol/djconnect/PRODUCT_ROADMAP.md`; local copies are forbidden
- installer contract for rerunnable manual updates: existing config is kept,
  systemd units are refreshed, and API/UI services are restarted
- installer contract for early free-space and active-swap checks before large
  PySide6 downloads
- installer contract for resource snapshots, inode reporting, CPU/Python/path/
  GitHub/thermal checks and incomplete `.venv` cleanup before dependency retry
- installer contract for disabling the old updater/client before manual
  installs and for per-package dependency markers under release `.install-state`
- bootstrap/README contract that public release download examples match the
  current project version
- config private permissions and atomic-write behavior
- Raspberry Pi system-info logging
- debug logging paths for invalid HA JSON and local API request limits
- Home Assistant 401 authentication errors and backend-unavailable responses
  are parsed into specific user-facing backend states instead of raw JSON/status
  text
- backend availability property coverage for red/green kiosk connection status
- local Client API debug screenshot route, API-daemon screenshot event file and
  QML-to-window screenshot capture contract
- loopback-only local Client API debug screen switching and screenshot
  response coverage
- backend notification toast state
- auth/backend toast suppression while the Pi is waiting on the blocking
  pairing screen
- playback response alias parsing
- playback output-device response parsing, `set_output` command dispatch and
  fallback HA `devices` command loading when status omits the device list
- playback refresh contract that Now Playing album art is cached locally before
  QML renders it
- Home Assistant playback contract coverage for no-active-playback status
  snapshots, empty HTTP 2xx body errors, HTTP 401/403/404 auth failures,
  `success:true` empty playback command responses, `devices`/`outputs` aliases,
  nested playlist response shapes and queue/playlist decoding up to 100 items
- live output-device validation and rollback coverage when HA rejects a
  selected output device
- queue loading contract sends `command:"queue"` with `limit=100`
- queue row playback contract sends `command:"play_context_at"` with nested
  `value.uri`, keeps direct Spotify episode/track URIs playable without
  context and preserves context plus offset behavior for playlist, album and
  show contexts
- playlist loading contract sends `command:"playlists"` with `limit=100` from
  both the touch UI and web portal state endpoint
- installer/updater contract that pip self-upgrade is skipped by default and can
  still be forced with `DJCONNECT_UPGRADE_PIP=1`
- CI/release contract that packaging tools (`pip`, `setuptools`, `wheel`) are
  refreshed before test/build/wheel steps, and release docs require reviewing
  third-party packages, GitHub Actions/Node tooling and OS/bootstrap packages
- shared `examples/voice_intents.json` availability for website/docs alignment
  without enabling local Raspberry Pi voice capture
- HA major/minor version compatibility checks and blocking mismatch behavior
- protocol mismatch error handling
- PySide backend properties and command dispatch
- persistent logging and redaction
- bundled QML files and offscreen QML load
- startup splash, blocking pairing screen, tap-to-wake blanking, wake refresh,
  independent return-to-now timer, disabled return-to-now wake behavior,
  navigation idle-timer restart, splash-on-wake and toast QML contract checks
- previous/next wake-screen signal coverage, including HA command-event
  previous/next
- modal overlay touch-blocking, settings reset-pairing/reboot confirmation,
  opaque Logs/Over/Instellingen backgrounds and About full-width website
  contract checks
- generated six-digit pairing code persistence and `/api/device/pairing-info`
  aliases
- dark DJConnect blue/purple gradient QML theme contract checks
- transparent rounded touch button, readable logs, scrollable settings, About,
  queue and playlist QML contract checks
- Games screen full-background touch blocking so Speelt nu controls cannot be
  tapped through transparent game areas
- touch-friendly icon bottom navigation order, height, selected-state checks,
  consistent QML Canvas menu icons, primary tabs for Speelt nu, Wachtrij, Ask
  DJ, Track Insight, Ontdek and Meer, plus the Meer overflow screen for
  Bediening, Afspeellijsten, Music DNA and secondary destinations
- shared AppBackground gradient, display-only Speelt nu checks and enlarged
  Bediening playback-control sizing checks, including that Speelt nu album art
  has no play/pause overlay
- Maze Chase power-pellet, vulnerable ghost and fixed-aspect playfield QML
  contract checks
- Empty queue/playlist labels and backend behavior that only loads demo media
  after explicitly entering demo mode
- kiosk branding contract checks for the bundled app icon, no visible quit
  action, explicit media-row geometry with fixed-size media play buttons and
  settings without pairing controls
- compact touch log formatting and 24-hour album-art cache helper behavior
- bounded log tail reading before QML log display formatting
- HA queue/playlist media parser coverage for artwork aliases from the shared
  contract
- backend media-list artwork background-cache coverage so Queue/Playlists show
  rows immediately, cache only the first visible batch and keep album art
  without blocking QML delegates
- QML memory-pressure checks for artwork `sourceSize` bounds and disabled
  dynamic image cache retention
- backend guard coverage that duplicate queue/playlist loads are skipped while
  a matching request is already in flight
- opaque queue/playlist main screens, manual refresh controls and no
  DJ-response dismiss dialog in QML
- web portal Diagnostics rendering plus daemon-side systemd status
  normalization for running/stopped/failed/unknown component health
- volume cap at 60, fixed screen-timeout and return-to-now dropdowns, anchored
  media-row geometry
  and reboot sudoers contract coverage
- local Client API pairing-info and logging regression coverage, plus Postman
  collection endpoint contract checks
- game title QML contract checks ensuring titles come from translation keys
- blocking version-mismatch QML contract checks
- touch-only games panel packaging and four-game QML contract checks
- updater release asset selection, SHA256 verification, top-level tarball
  directory stripping, bundled-wheel venv installation and atomic activation
- updater post-install cleanup of old release directories while keeping the
  active release and one rollback release
- updater pip install environment coverage for cache-local temp files under
  `/var/cache/djconnect-pip`
- updater dependency install coverage for resumable marked steps, including
  shiboken6, PySide6 Essentials, PySide6 Addons, PySide6, requests, zeroconf
  and the bundled wheel
- updater stable/beta prerelease channel handling
- apt maintenance windows, upgrade command flow and reboot gating

## Shared settings3 and Brand V2 candidate

`tests/test_shared_settings.py` consumes producer-pinned settings3 snapshots and
checks closed identity, complete first acceptance, stale Session draft rejection,
operation receipt recovery without PATCH replay, reassignment, unavailable choices,
no shared config writes and retired paired legacy Mood/output hints.
`tests/test_app_backend.py` also checks delayed Profile results, denied reads,
no optimistic quick-control confirmation and no local preference persistence.

`tests/test_brand_v2.py` verifies imported PNG hashes/alpha/dimensions against the
pinned Core manifest, headset-only micro sizes, local portal assets and five-locale
keys. It loads actual QML through `Tools/preview_shared_settings_brand.py`:40
fixture views across720x720/1200x1920, five languages and four initial states.
This uses software/offscreen Qt, not physical Pi display acceptance. See
[the consumer qualification boundary](docs/SHARED_SETTINGS_AND_BRAND_V2_ADOPTION.md).


## Shared phone/tablet presentation checkpoint

Both Pi profiles load the same feature screens and Session controller. Use
`Tools/preview_brand_colors.py` for actual QML fixture rendering at 720x720 and
1200x1920; use `Tools/preview_shared_settings_brand.py` for the four shared-settings
states in all five locales on both formats. Neither tool pairs a device or starts
music. The compact visual reference is iPhone mini, the large reference iPad portrait.

The Session additions cover explicit Profile confirmation, delayed-result rejection
on context changes, pure current reads, no automatic replay of uncertain writes,
independent live-display deadlines and historical retention deadlines. Product demo
state is labelled and cannot use the server or native delivery grants. History
schema2 fixtures preserve their pinned Core source/hash separately from local tests.

Current local checkpoint: the full suite reported 448 passed and 13 skipped;
after the compact toolbar/icon adjustments the relevant QML, locale and Session
subset reported 51 passed. Actual QML previews checked 36 page views without errors;
40 localized settings fixture views also passed. Screenshots and logs are fixture
proof only. No ARM/installed/physical/full-Session-parity qualification is implied.


History search checkpoint: 463 passed, 13 skipped. Additional tests cover exact
Session/query validation, retained-entry types, malformed and surrogate-splitting
highlight rejection, safe original/revision source links, mandatory Spotify
attribution, delayed-query withdrawal, navigation-only anchor reads and retaining
the active Runtime when a saved-session request fails. The QML preview now checks
40 views and exercises accented touch input/backspace plus private-query clearing.
The HTTP, WebSocket and fixture security tools passed. The built wheel includes
all shared Session, keyboard and attribution assets; this does not prove ARM,
installed behavior, a real HA exchange or physical touch acceptance.


PR111 follow-up: 480 tests passed and Ruff0.16.0 passed. The preview now checks44
actual QML views including opening/ending states; all56 packaged source files
matched the separately built final wheel. A CodeQL finding in a synthetic test URL
assertion was corrected to an exact parsed hostname check; its11 tests passed.
These results supersede prior local counts, while remote exact-head checks remain
separate. No installation or full Apple parity is claimed.

The Session safety suite includes an injected elapsed/UTC clock for rollback,
forward correction, unchanged-deadline re-fetch, retained search/history expiry,
GUI queue delay and background/resume without write replay. The real QML preview
also exercises synthetic native grant render/expiry/background withdrawal on
both sizes. These checks are offline fixtures and do not establish installed,
ARM, live Profile authorization or physical foreground/suspend acceptance.

Pinned native expressive fixtures retain Core's original bytes/hash. The200
frame checks cover five families, five locales and four Personas, preserving
prose, current/Flow identity, qualified source links and denial/expiry. The QML
preview renders six NL producer cases per target and checks that the first
accepted card is above the fold. These source-shaped Runtime fixtures do not
qualify live providers or Pi hardware.

History presentation checks include all five date locales, equivalent timestamp
offsets and invalid/no-timezone inputs. Search emphasis tests cover exact UTF-16
server ranges, overlapping ranges, surrogate-splitting rejection, literal HTML,
emoji and line breaks. The QML preview renders dates/highlights in every locale
on both dimensions, including a literal image-tag negative case.

Active Session text tests cover exact released capability gates, explicit matching
Profile/private owner scope, selected references, one-shot requests and unknown
outcomes. Receipt owner/client/context/turn/entry bindings and fresh history roles
must match; older chat and history Moments cannot confirm a new answer. Context,
source expiry, background and Runtime replacement clear the relevant private UI.
Tools/preview_session_composer.py uses synthetic transport with the actual
controller/QML for both sizes, five locales, explicit send/readback and draft
withdrawal. Copied released Core transport receipts anchor decoder syntax; these
checks do not invoke a provider or establish live/installed Pi acceptance.

Session concurrency tests keep one text POST separate from bounded Session reads
and lifecycle control. They cover both completion orders of a concurrent refresh,
End superseding a read, duplicate-write rejection, source/capability/Runtime
withdrawal, denial and late-result fences. A fresh-process Qt probe holds a real
question worker at a barrier and proves End completes before releasing it; this
avoids native timers left alive by unrelated backend tests. Transport remains
synthetic: this is not HA/ARM/suspend/physical qualification.
The composer preview also renders pending-question controls, a concurrent read
with End still available, and the ended state after discarded late work on both
sizes. Queued questions revoked before dispatch are not sent. Started requests
are not described as cancelled and are never automatically replayed.

Exact question receipts are reconciled against later typed history after an
accepted-but-unavailable read or concurrent refresh. Both entry IDs, Session,
client-message/turn IDs, text input, roles and nonempty bodies must match. A
missing receipt, partial pair, voice row or foreign identity cannot confirm the
turn; repeated reads emit no second focus signal. The original confirmation
retention deadline cannot be extended by a later read.
The real QML composer harness adds a long retained conversation on both sizes:
newly confirmed own reply focus, unchanged pixel reading position on refresh and
injected Qt touch dragging that cancels reply following. This is local Qt touch
injection, not installed Pi touch or physical acceptance.

A validated question receipt outside the tail may use bounded exact owner anchor
reads. The array order of receipt IDs is not timeline order. New discovery probes
at most both IDs once; a displayed anchored answer is subsequently revalidated.
Anchor identity, window/scan envelope, source representation and revision must
match; same-revision rows merge only by canonical ID/order without conflicting
copies. Revision drift, malformed/withdrawn anchors and order collisions cannot
confirm a reply. Denied private history clears old Session content. The current
Session can also open the existing chronological history pager from its first
page through the real QML navigation path, with five-locale read-only wording.

Previous-page history navigation retains at most32 RAM-only request descriptors,
never old body pages. A previous action reissues the existing owner read with its
opaque cursor/window and current revision. Cursor conflict or revision drift
revalidates the currently visible anchor once and drops the old trail; a missing
or withdrawn anchor cannot restore prose. First-page navigation, source/context
withdrawal, close and background invalidation clear the trail. Real QML exercises
the previous button and fresh restored first page on both sizes, including all
five locale labels. Explicit page navigation starts at that page's beginning;
continuous Flow and per-page prior pixel-position restoration remain separate.

The Session composer preview additionally verifies compact/expanded Apple toolbar
order, thirteen confirmed-value glyph variants and three scoped choice pop-outs
on both sizes. It checks that queued option clicks submit no work after Session,
Profile/edit-token, operation-pending or ending-lifecycle withdrawal. Its settings
state is synthetic presentation data, not producer authorization evidence. Preview
tools stop automatic QML fixture polling timers (3s/15s) while preserving explicit
reads and layout timers; production polling remains enabled. Final toolbar
checkpoint:770 full tests,86 broad QML views and84 dedicated views, all passing;
source/package/design only, no installed/physical or live-provider qualification.

Session playback metadata uses only its current active broadcast projection.
Tests compare title/artist/album/item/source across all200 pinned Core frames and
reject malformed states, mismatched/ending contexts, unsafe Spotify sources and
naive timestamps. Boolean timing values are not numeric progress. Real QML
captures the metadata after scrolling on both sizes/all five locales, plus a
labelled synthetic paused/output case and ending withdrawal. Plain text and
packaged Spotify renderer readiness are preserved. Observed progress is clamped,
not locally extrapolated. Final playback checkpoint:771 tests;86 broad and98
dedicated QML views. No artwork fetch, global/status fallback, historical-current
promotion, playback command, provider call or installed/physical claim.

Previous-page reading restoration keeps only a valid retained entry ID and finite
bounded offset in the existing32-descriptor RAM trail. Tests prove the metadata
never reaches transport, the target page is freshly read, and only a same-revision
still-retained identity restores position. Missing entries, invalid offsets and
cursor/revision fallback cannot replay a stale position. Real QML Next/Previous
on long pages preserves entry+pixel offset after layout on both target sizes.
Context/view withdrawal cancels pending restoration; active dragging suppresses
it. Final page-position checkpoint:778 tests,86 broad/102 dedicated actual QML
views; local synthetic/source/package/Qt proof only. Continuous Flow and broader
forward revisit history remain open.

Forecast v1 text tests use20 immutable pure released Core projection/expression
fixtures (five languages/four Personas), generated with explicit synthetic
semantics and fixed clocks; provenance pins source hashes/construction. They are
not Runtime/Planner/provider/HA/model acceptance. Tests preserve original prose,
claim roles and source identity; reject invalid scope, revisions, deadline renewal,
subscription/capability withdrawal and expired same-revision revival. Controller
coverage proves active-read admission and expiry before GUI state read. Real QML
Flow/Forecast toggles preserve actual input text and Flow scroll position in five
languages on both sizes; expiry removes sections. Final checkpoint:809 tests,
86 broad/114 dedicated QML views. No imagery fetch, new request or generation.

Historical playback cards use only history2 playback_observed and exact
observed_playing_not_full_listen coverage. Tests preserve original body/source
and canonical historical authority while projecting bounded title/artist/album;
unknown coverage/shape is refused and empty fields retain text fallback. Actual
QML renders a labelled synthetic observed entry through the real controller in
five languages/both sizes, including literal markup/emoji, packaged Spotify
attribution, full-card scrolling and expiry removal. Final checkpoint:816 tests,
86 broad/128 dedicated QML views. No current promotion, artwork fetch, seek,
favorite, full-listen claim or provider/model call is included.

Current-Session history and archive navigation are checked through actual QML
buttons and the real controller on both sizes. Cases cover origin-specific tab/
Back, unsent input, archive menu/list/detail, current and foreign retained entry
open/anchor reads without replacing Runtime, cancellation before submission and
foreground withdrawal. Synthetic pending executor work is held across navigation
then drained, exercising a stale view epoch before the chosen fresh read. Both
entrypoints share one guarded read intent; polling cannot steal its dispatch.
Empty search clears still revoke tickets while avoiding redundant GUI change
signals. Both preview harnesses now fail on QML binding-loop warnings as well.
Final navigation checkpoint:817 tests,86 broad/152 dedicated views. No server
contract, lifecycle write, media grant or installed/live/physical proof is added.


The shared Session composer preview additionally verifies return from current
history to the same still-present Flow contribution and pixel offset on both
canvases. It checks metadata-only descriptors, withdrawn-entry fallback, history
Qt-touch scrolling without losing Flow position, native Moment ID capture and
foreground withdrawal. These are local synthetic transport/actual QML checks,
not physical touch, installed Pi or live Profile/HA qualification.


Search qualification additionally covers bounded fresh multi-page traversal,
revision/ID/order/cursor rejection, withdrawn bodies, scan-limit reset and stopped
private reads after cancellation. The QML harness renders the limit copy in all
five locales/both formats, restores a surviving result position, invokes the
actual revalidation timer callback behind a held read, closes before dispatch,
and verifies denied-result withdrawal. Periodic refresh uses the existing owner
GET only; these synthetic proofs do not contact HA, providers or models.


The broad page preview now renders Privacy/Legal via actual More-menu clicks in
all five locales on both canvases. It verifies selected More tab, Back navigation,
page-end scrolling and adaptive one-/three-column menu presentation. No external
licence link is opened, and no server request is required for either static page.


Current-only selected-Moment replies have a separate qualification suite. It
combines a synthetic admitted native reference with unchanged pinned credit prose
and adapted receipt identities, checks original deadline/revision/owner fences,
refuses malformed/error/unqualified responses and proves no retained-history or
executable/media fields appear. QML uses explicit synthetic question workers on
both canvases/five languages. These tests do not qualify broad private/standalone
chat or a live model/provider/HA response.


The shared QML composer harness also checks current-only reply return position:
receipt identity/pixel only, same still-valid card after history, withdrawal ->
top, and no response body/grant in the descriptor. An explicitly synthetic long
response makes this reading case distinct on both phone and tablet; unchanged
released prose remains in the separate five-language rendering probes.


Current-only question cards use exact bounded local request text, never a server
user-message echo. Tests cover malformed prompt bounds, immutable GUI snapshots,
combined question/answer withdrawal, literal markup/emoji/newline and native QML
PlainText evaluation on both layouts/five locales. The user card has no separate
persistence or rights lifetime. Pending/uncertain turns remain outside this UI.


Pending Session questions are local input only. Controller tests distinguish
pre-dispatch/accepted/uncertain/withdrawn states, prove no replay after refresh and
no queued POST after source/foreground/End withdrawal. Actual QML holds one worker
in each locale/layout to check user text, Sending copy, native PlainText and atomic
replacement/blanking, without a server or model call.


Session header retention tests derive only the released explicit owner-list
policy/lifecycle rule; they do not assume a default or invent wire expiry fields.
They check expiry before GUI admission, parent-before-entry removal, rollback,
selected-context notification and no body/cursor resurrection. Real QML uses a
synthetic short-lived terminal header plus longer-lived entries in all locales
on both layouts, asserting empty rows/detail and cleared selected draft.


Pending status polish is qualified in actual QML: Sending is hidden only in the
dock while its pending card is visible; accepted/uncertain status returns after
completion. All five locales on both layouts include a real controller with
synthetic uncertain transport, preserving no-replay behavior and warning text.


Archive freshness qualifies first-to-last fresh owner traversal for all shown
pages, strict revision/policy/keyset/cursor consistency and atomic replacement.
Tests cover100headers across5requested20-row pages, truthful incompleteness,
Profile/view cancellation and no cached earlier headers. Actual QML checks the
15s timer, More, ID/pixel preservation, missing-ID fallback, five-language limit
copy and queued cancellation behind a held read on both layouts. Older-window
paging and real device/server acceptance are not inferred.

Archive slice final:13 new synthetic cases,885 full tests;262 dedicated and116 broad actual QML views, no errors/binding loops. Partial expiry preserves the traversal budget; stale More is fenced, active reads debounce and polished fresh layouts preserve the anchor. Diagnostic fixture worker ordering and ISO rounding failures are retained separately from the corrected product layout finding. Local package60-source match; no installed/live claim.

Conversation read cancellation:18 cases cross question/refresh with three request
boundaries and foreground/Profile/End withdrawal. They verify exact GET counts,
no late publication and no automatic POST replay. Existing retained rows before
End completion are distinguished from new reader output. Synthetic fixtures only;
not network cancellation, server question cancellation or physical acceptance.

Retained Flow tests cover all six history2 kinds in owner order, independent
readonly/free-input capability, absence of native-grant promotion, original input
immutability and copied GUI state, expiry/foreground/Profile/capability/denial/empty
withdrawal, exact typed receipt-anchor merge,20-row tail bound, separate current
Runtime versus historical playback and atomic expiry before GUI publication.
Historical Spotify tests cover absent/false native flags, provider or link
attribution, missing valid source and malformed explicit flags. Dedicated actual
QML uses unchanged released rows plus clearly synthetic playback/conversation and
short-lifetime overlays; both layouts/five languages check shared cards, literal
markup/emoji/newline as PlainText, disabled composer/actions, logo readiness and
expiry. These are fixture/controller/Qt proofs, not ARM, installed or live evidence.

Final retained Flow qualification:922 full tests passed, including13 new typed-Flow cases and6 historical Spotify attribution cases. Ruff0.16.0 src/tests passed; hostverify MATCH.292 dedicated actual QML views plus116 broad views on both formats/all locales completed without errors/binding loops. Both format captures were visually inspected; the repaired Spotify logo is visible on the mixed retained surface. Local wheelbc6ecf1509307c2c472404e97d157ad602c80d76d151b55dea88e155d9def6e7 matches all61 packaged source files including SessionRetainedEntry.qml. Evidence: taskvisualizations/pi-session-retained-flow. Source/synthetic transport/Qt/package proof only; no live Profile/HA/ARM/installed/physical acceptance. Earlier intermediate test/package/render results and diagnostics are kept separately, not promoted to final source proof.

Archive windows:13 bounded owner-query cases cover older/newer access beyond100,
32-descriptor memory bound, fresh return and ID/pixel metadata only, invalid
coordinates, keyset/scope drift and one bounded newest reset, denial without
fallback, late-read cancellation and unchanged current Session. Actual QML checks
older/newer/newest routing, current-window15s revalidation and detail Back freshness.
Forecast scope cases cover equal/lower revision with changed style/playback,
immutable content, independently observed Persona/Mood/Presence counters, unknown
Persona floor and fresh higher recovery, and harmless playback observation ticks.
Real controller and five-language/two-layout QML probes preserve draft/toggle/
expiry behavior. Synthetic Runtime overlays are labelled separately from original
pure producer fixtures and any native/installed/live qualification.

Final combined qualification:962 full tests passed, including13 archive-window cases and54 pure Forecast receiver cases plus3 current-controller scope cases. Ruff0.16.0 src/tests passed; hostverify MATCH.386 dedicated actual QML views plus116 broad views completed without errors/binding loops on both formats/all five locales. Real QML buttons/timer callbacks prove beyond100 access, fresh window revalidation, ID/pixel restoration after detail, top-visible reset copy, context close, Forecast scope withdrawal/fresh recovery and Persona uncertainty. Local wheel9a8a7bd4ca0f7fe692ce18935d2285379a709336e7d4b86d4aeed3aa237eb45d matches all61 packaged sources. Source/synthetic transport/package/Qt proof only; no ARM/installed/live Profile/HA/physical acceptance.
No duplicate Forecast prose remains after withdrawal; terminal reads preserve state without text renewal. Actual tablet geometry must settle and applied position must verify within8 attempts. Automatic fixture polling bindings alone are disabled, explicit real callbacks remain tested, and production polling is unchanged. Failed/intermediate diagnostics are retained.


Retained Flow question selection:18 new cases cover all six released history2
kinds with exact original IDs and current Session, no native promotion, missing/
foreign IDs despite an old detail, expiry/removal/foreground/capability/End before
queued POST, fresh source withdrawal and draft invalidation, separate timeline
origin and Profile/busy/read-only gates. Synthetic transports do not establish
actual producer narration/readback for every type. Existing owner contract and
exact receipt/history checks remain authoritative. Actual QML probes drive the
shared button, preserved draft/modal/current tab, pending-disabled action, exact
selected_entry send/fresh confirmation and source-expiry cancellation in five
languages on both formats. No new user-facing strings; existing i18n keys reused.

Final retained Flow selection qualification:980 full tests PASS (18 new cases), Ruff0.16.0 src/tests PASS, current shared-root hostverify MATCH.426 dedicated actual QML views plus116 broad views completed without errors/binding loops on720x720 and1200x1920/all five languages. Both new composer layouts were visually inspected against existing native references and pinned Apple source; exact inline/native geometry and glass effects remain open. Wheel32edb508939bdccb7ec3b09a2592e935912c6ebaed5408da6878aff7139cc68f matches all61 packaged source files. Evidence: taskvisualizations/pi-session-retained-flow-selection. Source/synthetic transport/Qt/package only; no ARM/installed/live HA/Profile/physical qualification. Diagnostics preserve an initial test End call missing its required Session-ID argument, a fixture using single-result visual lookup as an iterator, and hostverify's obsolete default repository root; corrected explicit shared-root verification was MATCH. Product gates were not loosened for fixtures.


Saved-history reading prefix:20 new cases cover fresh first+next aggregation,
full shown-prefix revalidation with fresh cursors, bounded100-body navigation and
fresh Previous return, same-revision/ID/order/cycle/20-wire-row/denial/expiry/owner
failure, before/between-read view cancellation, revision-anchor fallback, unsafe
reading offsets, actual monotone GUI-queue expiry and rejection of unknown wire
prefix markers. The dedicated real QML harness covers current and archive origin,
both formats/all five locales, actual More/Next/Previous/15s callbacks, fresh body
replacement, ID/pixel position, limit copy and denial withdrawal. These are
synthetic owner transports, not live producer/installed/native-hardware acceptance.

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

72 new image cases cover original producer chains, malformed grants, immutable
revision/deadline floors, route-specific no-credential HTTP, redirects/status/MIME/
magic/animation/size/decode rejection, bounded worker admission, hide/latest lease,
clock expiry and queued/real-thread foreground/Profile/End/capability withdrawal.
An initial full-suite Qt native crash in the in-process thread barrier is retained
as a diagnostic; the same real-worker End barrier now owns its Qt application in
a fresh subprocess. No product admission gate was weakened. Initial fixture wall
clock rollback was corrected by initializing its clock at the source time.


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


### Shared current-Session playback controls — 2026-10-20

The admitted music context now has an explicit Playback controls pop-out on both
Pi formats. It offers play/pause, previous/next and current-track save only when
the backend advertises favorites. It has five-language accessible names/status,
Back-equivalent Close and explicit Refresh. This is a Pi adaptation of the pinned
Apple current music actions, not artwork tap/swipe, exact SF or native geometry.
The added glyphs reuse the existing Pi Main.qml transport geometry. Saving does
not infer or toggle a favorite state; favorite state/removal and volume/output
controls remain open. Opening the pop-out never dispatches an action.

One dedicated max1 worker first reads the paired owner active Session, requiring
original Session/item/state/source equality, then resolves fresh backend status.
Backend ID/revision/availability, strict favorite capability when applicable and
observed URI/hash plus playing/paused state must match. The equality hash is the
released RendererSafePlaybackProjection.from_observation representation; it is
not a new permission. Only then is one existing command POST sent. These
preflights and the POST use fresh no-environment HTTP sessions, normal paired
Bearer/device/explicit Profile, configured HA, redirects disabled and no inherited
netrc/proxy credentials/cookies. No caller URI/subject or invented expected
Session/item wire field is added. Session visibility/foreground/Profile/current
reference/backend/End and worker fences revoke queued dispatch immediately.
Closing the pop-out before dispatch cancels the local intent; started HTTP may
finish. End remains available during a held command; other input/control reads
are temporarily gated. Real worker End-before-release is tested in a separate Qt
process. Definitive owner Session withdrawal clears only a still-original scope.

Command playback payloads never update Runtime optimistically. An independent
normal owner refresh supplies the observed UI state. A still-current visible uncertain result locks
further clicks until explicit refresh, with no automatic write replay. These are
existing global Profile playback commands, not operation1 receipts or server
exactly-once/CAS transactions. A server change after the final read remains
possible; no atomic expected Session/item guarantee is claimed.

Final source qualification:1315 full Python tests (57 new controller/transport
cases), Ruff0.16.0 src/tests PASS and fresh read-only qualifiedhost MATCH.
1046 actual QML views:90 playback +436 composer +180 Moment/artwork +90 Forecast
+100 historywindows +150 broad, five locales and720x720/1200x1920; no errors or
binding loops. Real mouse-button probes cover pending/accepted/uncertain,
play/pause/save, explicit refresh, no replay, unsupported favorites, close-before-
dispatch and foreground withdrawal. Glyph pixels and the original half-viewport
first-fold threshold are asserted with controls active. Existing reading/expiry/
receipt/search/image/history tests remain. Both final pop-outs were visually
compared with the pinned source and existing offline mini/iPad references; no new
native controls screenshot or exact visual parity is claimed. Wheelc32c3c4b78abc83c3725c6ea2917e8704e9e7c144a34ba49c7e2d63ba3789d42 matches
all65 packaged sources; the source tree stayed closed during final qualification.

Diagnostics preserve a real QML state-binding loop (fixed by immediate revocation
and deferred notification), missing transport glyphs found during visual review
(fixed and pixel-tested), initial fixture startup/viewport positioning, wrong
QImage conversion and teardown order. The first held-worker fixture omitted its
active mock and attempted fixture.invalid; no HA/provider response or real
credential was involved. Final fixtures intercept all transport. These are
local source/synthetic HTTP/Qt/package results, not live Profile/HA/provider/model,
ARM, installed or physical acceptance. Original native fixture bytes remain
unchanged; backend metadata/commands/readback transitions are explicitly synthetic.
SESSION_PLAYBACK_CONTROLS_REFERENCE.json pins authority and limitations.
Evidence:taskvisualizations/pi-session-playback-controls. PR111 remains draft;
full Apple parity and installed4-inch Session delivery remain open.

The final popup uses aboutToHide, so queued intent is revoked at the beginning of
closing, before any exit animation. The real QML close probe now executes the
held worker immediately after close(), with no GUI tick or animation delay.
All1046 final-scope views were rerun on this closed source; earlier onClosed
recordings/packages stay separate under the evidence diagnostics/top-level
intermediate folders. Python fullsuite1315 and Ruff were also rerun on this source.


### Playback URL admission follow-up — 2026-10-20

An offline requests.prepare_request probe confirms embedded URL credentials can
replace an explicit Bearer header even with trust_env=False. No request is sent.
The new isolated playback path now rejects credential-bearing, non-HTTP(S),
query/fragment, control-character and invalid-port HA bases before preparing any
request. Valid configured reverse-proxy base paths remain supported. Other
existing Session routes are unchanged; no new credential or auth fallback.

This transport-only follow-up passes1334 full tests, including19 new base-URL
admission cases, and Ruff0.16.0 src/tests. Wheelb5a5873d165c04020e353b9d34babfc60182788b80168e2c225f86df58e4fd97 matches all65 packaged
sources. Controls/UI/controller bytes remain identical to a54aee5db32cb6cc5b57d344548f01fa95cbe6d9,
where1315 full tests and1046 actual QML views were completed. No extra QML views
are claimed after this transport-only guard. Both proof layers and intermediate
packages are separate under pi-session-playback-controls/final-scope and auth-final.
There is no live HA/Profile/provider/model, ARM, installed or physical claim.


Latest host checkpoint:1required DRIFT in maintenance.verification_artifact_retention,
not a product test failure. The five identified Core Pi-live artifacts crossed
the14-day policy after the earlier MATCH. Exact metadata and fresh host log are
in pi-session-playback-controls/auth-final. No cleanup, relocation, mtime change
or other-lane source write was performed; the Core owner received one concrete
receipt.1334tests/Ruff and code23712dc CI25success/4conditional skips remain
separate from this current unresolved host/delivery gate.


Host follow-up after concrete owner authorization: Core reports all nine original
Pi-live paths durably preserved with identical bytes; the five+four replacements
were separately approved by Peter. A fresh independent Pi actual-root verify
returned MATCH around20October14:31UTC. Earlier retention DRIFT manifests/logs
remain historical and are not deleted. Pi performed no cleanup/mtime/other-lane
source writes. This resolves that host gate only, not installed/live/physical
acceptance or source/release approval. Product proof remains1334tests on code237,
1046QMLviews on controls a54, with unchanged UI/controller bytes in later code.

## rc.5 deployment preparation — 20 October 2026

The distinct rc.5 version preparation passes the full local Python suite:1334tests, Ruff0.16.0 src/tests, shell syntax and diff checks. An initial1333pass/1failure run exposed stale rc.4 README/bootstrap download examples; the examples now match rc.5 and explicitly require separate publication. The final full run passes without weakening the existing installation-contract assertion.

Predecessor6078e706 has25successful applicable CI checks/4conditional skips and passed in-memory compilation of all29 Python source modules on each actual ARM target using its existing Python3.13.5/Qt6.11.2 runtime. This is not rc.5 ARM package import, QML rendering, installation, server execution or hardware acceptance. The existing playback UI qualification remains separately bound to its earlier exact source.

Current device/service/resource/paired-flag observations and the planned immutable package/source/target/capture receipts are documented in `docs/PI_4_0_RC5_PREPARATION.md`. External evidence: `pi-deployment-screenshot-preflight`. No candidate publication, device activation, reset, pairing or Profile substitution has occurred.

## rc.5 malformed-denial review correction

An independent bounded Apple-chat review of exact9f555826 found that non-JSON HTTP401/403 could be misclassified as uncertain/invalid. The shared transport now classifies denial after the original binding fence and before any JSON decode. Full production-byte suite1376PASS;128targetedtransport/playbacktestsPASS;Ruff0.16.0src/testsPASS.42newcases includeGET/POST,isolated/ordinarytransport,401/403,empty/malformed/non-object bodies,bindingreplacementprecedence,503/noReplay,and realtransport→controllerwithdrawal at owner/status/effect boundaries while pairing/token remain.

The actual QML playback harness passes100views with zeroerrors/bindingloops across5locales/bothformats, including realQtbutton→synthetic malformedHTTP denial→clearedSession/draft/closedpop-out. The existing150broad rc.5-preparation views remain a separate predecessor checkpoint. No new installed/live/physical claim or producerfixture is created. Four separate extracted-installer-function fixturechecks are external deployment research, not additional product-suite tests or fullinstaller/rollback proof.


### rc.5 publication guard qualification

`tests/test_release_candidate.py` adds 21 cases covering matching source
versions, missing/failed/pending/duplicate/stale release evidence, each of the
five version boundaries, and missing/duplicate/prefix-only changelog headings.
Together with the existing installation contract, 60 targeted cases pass.
The real publication source-gate Bash step also passes six isolated executions
against local synthetic Git repositories and mocked status responses: qualified
source succeeds; failed/missing/wrong-SHA/wrong-version/unmerged source fails.
The actual build step was executed offline for all three bundles with pip wheel
intercepted to reuse the qualified 5922 wheel, proving source-marker/manifest and
profile/version/archive-hash joins. These external audit cases are not additional
product tests, workflow dispatches, publication or installed proof. Initial
missing-changelog and lint diagnostics are retained. Runtime/QML sources are
unchanged; older QML and ARM proofs retain their original source qualification.

The final complete local suite passes1397tests; Ruff0.16.0 for the publication helper, tests and src passes. Six extracted Bash blocks and git diff checks pass. These results qualify this local source correction, not live deployment.


### Streamed Session JSON review correction

`tests/test_session_json_bounds.py` adds42cases; combined transport/preparation/
playback cases total201PASS and the complete suite1439PASS. It proves streamed
and declared oversize rejection before decode, exact-boundary acceptance,
response/session lifetime, gzip expanded-byte rejection, nesting/token guards,
context-before-denial/stream/decode fences, no replay, and50unclipped escaped
Unicode history text shapes. These are explicit local resource budgets, not new
producer wire limits. `Tools/preview_session_playback.py` now produces130actual
Qt views,5locales/twoformats, including real buttons at oversize/exact boundaries
plus the existing denial/reading/End coverage. Zero errors/binding loops; both
oversize layouts visually checked. No physical, installed or live HA claim.
Provenance: `docs/branding/SESSION_JSON_BOUNDS_REFERENCE.json`; external evidence
`pi-session-json-response-bounds`, with superseded diagnostics retained.


### Queued Moment question source revalidation

Twelve added current-reply cases cover expiry/revision/admission-withdrawal/style
before worker execution, both with and without a GUI expiry observation, a valid
original-intent/receipt control and changed pending metadata. The unobserved cases
call no state getter, Qt event processing or _expire before the worker and prove
zero question dispatch.139targeted and1451app-selection tests pass; the separate
uncommitted two-host consumer/installer tests are excluded from this app count.
436actual composer-QML views pass on both formats/five locales with zero errors.
Original fixtures remain unchanged; expiry/style overlays are synthetic. No new
server field, right, replay or automatic replacement question is introduced.


### Protected two-instance deployment consumer

See docs/PI_TWO_HOST_CONSUMER.md for the closed Core contract/inventory pins,
236 dedicated offline cases, actual read-only identity observations and
remaining exact review/publication/operational gates. Neither rc.5 installation
nor installed screenshots are claimed. Runtime app bytes remain at42dac367.


## Actions archive media type, 21 October 2026

The locked deployment-tool suite passes316cases, including12 new Actions ZIP
HTTP-boundary cases. Three exact negotiation regressions fail on the old reader;
the corrected reader retains release-asset octet-stream, anonymous signed-byte
download, bounded content, unsafe redirect rejection and no automatic retries.
Actual GitHub read-only verification recognizes both existing successful rc.5
install/smoke receipts; that local WIP check is not qualified workflow evidence.
Both device installations and individual smoke checks are separate actual proof.
The new live Pi10/HA-dev active-Session click test is not yet performed: normal
HA-dev two-factor login and existing native VNC authentication are pending.


## Native screenshot capture on Qt 6.11 — 21 October 2026

The unchanged `ApplicationWindow.contentItem.grabToImage` path reproduces the
installed Qt 6.11.2 `item has no QML engine` failure on both local canvas sizes.
The screenshot signal now performs the existing transient X11 wake and defers a
backend capture of the actual `QQuickWindow`. PNG storage uses `QSaveFile` so a
failed encode cannot expose a partial image. No API, pairing, Profile, display
configuration, Session or playback command changes are introduced.

Eight new storage/error-path cases plus existing QML/API-daemon checks pass
(41 focused tests). The complete local suite, using both existing locked test
environments and permitted loopback sockets, passes 1715 tests with no skips.
The earlier restricted run is retained separately: 1472 passed, 20 skipped and
one pytest cache-permission warning. Ruff 0.16.0 and diff checks pass.

Twenty actual isolated Qt daemon-event-to-QML-to-PNG requests cover both
720x720 and1200x1920, all five languages, pairing/About overlays, and logical
idle blanking. Each decoded image has the expected dimensions and visible
pixels, the daemon returns identical PNG bytes, and capture finishes within
0.519 seconds. X11 wake commands are mocked; no network or real OS commands
run. No QML errors or binding loops occur. One macOS font-alias startup warning
is preserved. The initial fixture's missing QML-ID context and ambiguous timer
selection diagnostics are also retained; the final harness resolves the real
component context without changing production idle behavior. An initial
encoder-failure test exposed a temporary file retained by the mock; cancelling
and finishing the QSaveFile transaction removes it explicitly.

Evidence: `taskvisualizations/pi-native-screenshot-audit`. Both format images
were inspected. These are local synthetic captures, not new installed captures,
ARM or physical wake/touch acceptance. Both existing rc.5 installs and immutable
release assets remain unchanged. New runtime bytes need the normal independent
review, protected source, separate Finalization and distinct release delivery.


## Saved Session list SQL revisions — 21 October2026

Core public_session copies each saved Session's SQL revision as an integer.
Pi previously required a string and rejected an otherwise valid nonempty list.
The exact public_session AST is identical at the existing Core8b221d07 pin and
new sourcebbb7a23d: this is existing read compatibility, not adoption of the new
deletion endpoints. Pi now preserves nonnegative integer header revisions as
list metadata, and keeps previously admitted nonempty string metadata compatible.
Boolean, negative, float, absent and container revisions remain invalid. Detail
and cursor revisions retain their separate nonempty opaque-string checks; list
metadata cannot become a deletion CAS token. Retention, Profile/epoch fences,
source rights and all mutation paths are unchanged.

Twenty-two new cases include zero/large SQL values, malformed types, unchanged
opaque detail admission, original retention expiry, fresh multi-page refresh,
late Profile withdrawal and stale-list removal after a malformed page. The four
numeric regression cases fail on the original Pi code. After repair81 focused
checks and the complete1737-test local suite pass with no skips. Ruff0.16.0 and
diff checks pass. Twenty actual isolated Qt list/detail views cover both sizes
and all five locales, including10 genuine Qt mouse clicks from the numeric-header
list to an independently read opaque-revision detail. Active Session state is
preserved; no network, OS commands or deletion routes run. Both formats were
visually checked. The initial fixture looked for a Repeater delegate in QObject
ownership rather than the visual tree, then exposed a queued signal during
fixture teardown; the final fixture traverses real visual items and drains
callbacks before destroying their source. Diagnostics are retained.

Evidence:taskvisualizations/pi-history-delete-handoff-review. Fixture body bytes
are unchanged on disk; copied owner IDs/deadlines/envelopes are synthetic. No
new installed, HA-dev, hardware touch, media-license or erasure acceptance is
claimed. New deletion capability/UI stays absent, and EADBrc.5 installations and
immutable release assets remain unchanged.


## Shared Session volume source qualification — 21 October 2026

The playback pop-out now offers an explicit current-volume read and a 0–60%
slider on both formats. Opening, notifications, programmatic slider values and
drag movement submit no volume write. A real release or keyboard movement makes
one typed intent. Zero is preserved; unknown data never defaults to 50%. An
observed volume above 60% is shown honestly with a separate explicit set-to-60%
button. The 60% ceiling follows pinned Core8b221d07's existing Pi contract.

A RAM-only observation lease binds the original Profile/Session/item/state/source,
backend/revision and output ID. Each write independently reads the owner active
Session and raw backend status, requires strict current volume capability and an
unchanged output/observed volume, then makes one existing paired isolated HTTP
set_volume request. Spotify receives integer percent; the released MA adapter
receives target/100 because its integer1 means100%. No new wire fields, output
selector, CAS guarantee, response import, optimistic volume, fallback or write
replay is introduced. Original private personal/household admission stays narrow;
other authorized Profile modes remain an independent consumer audit, not a Core
block. A backend change after the final read remains possible under the existing
global command semantics. Close/hide/foreground/Profile/item/backend/End withdraw
queued intents; a started HTTP request may finish. One dedicated worker keeps End
available. Local read failure preserves the Session and shows unavailable.

Validation:105 new volume cases, including two real held-worker/End subprocesses,
and the full1842-test integrated local suite pass with no skips. Ruff0.16.0 and
diff checks pass. Final180 actual isolated QML views cover both formats, all five
locales and both backend shapes, including real press/drag/release, keyboard,
close-before-release, unknown/zero/above-limit and unsupported states. Both layouts
were visually inspected and compact pop-out bounds checked. There are zero QML
errors/binding loops; one macOS font-alias startup warning is retained. The first
80-view Spotify-only run is intermediate and is not added to180. The added worker
test initially passed an observation dictionary instead of its lease; the six
fixture failures and corrected105-pass log are retained. All transport/owner and
OS wake effects are synthetic/mocked; no network, HA/provider, device playback,
installed ARM or physical touch acceptance is claimed.

Evidence: taskvisualizations/pi-session-volume-consumer and the earlier143-case
pinned contract audit. The local review wheel SHA256
074f3fe68281b94e7cf6e7dcdc87b244500600d1f6587525f5e6a22776840b42
matches all65 runtime files. The initial host check observed the announced Core
maintenance URL outage; after the owner completed installation a fresh actual-root
verification returned MATCH. No Pi repair was performed. Both installed EADBrc.5
apps, immutable release assets and operative bindings remain unchanged. Exact
independent review/protected delivery and a distinct release are still required.
Output selection, favorite-state/removal and gestures remain open. HA-dev login
and the active Pi10 Session click test remain explicitly human-deferred.


## Current-track favorite state and removal — 21 October 2026

The Session playback favorite button first explicitly reads the current Spotify
track's favorite status. Only a strict boolean favorite_status, consistent with
is_liked when present, makes the next click an explicit Add or Remove action.
Unknown, absent, malformed or contradictory data is never treated as unliked.
A confirmed liked state highlights the existing heart button and labels removal.
An unavailable read preserves the Session and offers another deliberate read.
This replaces the previous UI's unconditional save-only click; it does not use a
server-side toggle. MA does not advertise favorites in the pinned contract and
gets no invented favorite support.

An in-memory serial lease binds the original Profile/Session/item/state/source
and backend/revision. A write independently reads the current owner Session and
raw status, requires the same observed liked state and strict capability, then
sends one existing set_current_track_favorite command with a strict boolean value.
The original isolated HTTP authorization, no-retry and denial guards apply.
Close/hide/context/End withdraw queued work; a started request may finish without
publishing into a withdrawn context. The dedicated worker leaves End available.
Command responses never set a local liked state; the next explicit status read
owns it. Other playback intents clear observation leases, so an old observation
cannot silently authorize a later action. The existing global current-track
command still has a server-change race after the last read; no atomic CAS or
exactly-once guarantee is claimed. Private personal/household admission remains
the current narrow consumer slice, not a permanent ban on other authorized modes.

Sixty-seven new favorite tests pass, including strict status/boolean payloads,
changed owner/status/capability fences, late result withdrawal, no write replay,
denial preserving pairing and two real held-worker/End subprocesses. The full
integrated local suite passes1909 tests without skips; Ruff0.16.0 src/tests and
diff checks pass. Final160 actual isolated QML views cover both formats, five
locales and initially-liked/unliked states with real read/Add/Remove/cancel clicks,
unknown-versus-false, no optimistic response import and compact popup bounds.
The existing playback preview now follows read-then-set and separately passes
130 actual QML regression views, including normal transport, streamed response
bounds, denial, close-before-dispatch and no replay. Both formats were visually
inspected. There are zero QML errors/binding loops; startup font warnings remain
recorded. Four new stable copy keys exist in all five locales.

Two external unmodified pinned-Core8b AST method cases prove boolean true/false
map to the existing provider PUT/DELETE paths. These are offline contract checks,
not extra product tests or provider acceptance. The first new HTTP test fixture
reversed request/response tuple positions; three failures and the corrected log
are retained. A later helper copy accidentally included unrelated volume cases;
that intermediate24-failure diagnostic is retained, and only the intended67
favorite cases are counted. No production condition or assertion was weakened.

Evidence: taskvisualizations/pi-session-favorite-consumer. Local review wheel
497e262b590453ed35d71c1a5982ff99798df58d6ac1270d839e36abc951d31a
matches65 runtime files. Host actual-root verification returned MATCH; no host
repair was made. No network, HA/provider commands, installed ARM, physical touch
or live Profile acceptance is claimed. Both EADBrc.5 devices and immutable assets
remain unchanged. Independent exact-source review, protected source/separate
Finalization and a distinct release/operative binding remain required before
runtime deployment. Output selection and artwork gestures are still open.
HA-dev authentication and the active Pi10 Session test remain human-deferred.


## Explicit Session playback output selection — 21 October 2026

The shared playback pop-out now opens a separate output picker through an
explicit server-inventory read. Only Spotify with strict supports_outputs and
supports_transfer_or_output_selection is admitted. Pinned MA exposes a no-op
set_output and advertises no transfer support; it receives no invented selector.
The current output is labeled and disabled, and only server-returned, non-cached,
unrestricted choices can be selected. Names render as wrapped PlainText. No
arbitrary ID entry, first-device fallback, cached-device fallback or automatic
transfer occurs. Four stable copy keys cover all five locales.

A RAM-only lease binds original Profile/Session/item/state/source/backend/revision
and current output ID. One deliberate selection rereads owner Session, raw status
and server inventory, requires the original output plus the exact still-eligible
choice, then sends one existing isolated paired set_output command with that ID
and an explicit play boolean matching the observed playing/paused state. The
server's existing set_output independently calls devices(fresh=True) before the
transfer. The devices read command itself may use the producer's inventory cache;
Pi does not invent a freshness parameter or claim a fresh provider request from
the initial list read. Duplicate IDs, inconsistent active-output identity and
malformed metadata fail closed. A local resource bound rejects over100 raw rows
or over32 admitted choices without truncating; these are Pi budgets, not new Core
wire maxima or permissions. Original Session/expiry/media grants are unchanged.

Close/main-popup-close/foreground/Profile/item/backend/capability/End revoke
queued intents before the exit animation. A started HTTP request may finish;
withdrawn results cannot publish. The same dedicated worker leaves End available.
No command response or optimistic device selection changes Runtime/configuration.
An uncertain selection blocks new effects; the picker Refresh explicitly reads
the owner before a subsequent separate inventory read. It never retries the
transfer. The existing global command still has a race after the last client
read; no Session/item/output CAS or exactly-once guarantee is invented. Admission
remains the existing narrow private personal/household slice; broader authorized
Profile modes are still a local consumer audit, not a permanent producer block.

Validation:85 new cases, including strict choices/caps, current-output and stale
membership fences, playing/paused payloads, denial/no-replay,10 late-result cases,
two real held-worker/End subprocesses and absent-backend metadata. Full integrated
local suite1994 PASS/no skips; Ruff0.16.0 src/tests and diff checks pass. Final200
actual isolated QML views cover both formats, all five locales and playing/paused
states, with real picker clicks, pending/no-optimism, close-before-dispatch without
a GUI wait, cached-choice withdrawal, explicit recovery, no alternatives,
unavailability and capability withdrawal. Popup bounds are checked, both formats
visually inspected, with zero QML errors/binding loops and the retained macOS
font-alias startup warning. The two earlier200-view runs are intermediate and
are not added to the final200 count.

Seven external unmodified Core8b set_output AST cases separately prove fresh=True,
playing/paused flags and rejection of missing/cached/restricted/duplicate/empty
IDs. These are offline contract checks, not extra product tests/provider evidence.
The initial added read-worker harness used a singular slot name and failed six
cases before correction. The initial full run then exposed unsafe direct access
to absent backend metadata (218 failed/1774 passed, including those harness cases).
A second full run retained1993 passes and exposed the same absent-backend issue
in the favorite support check; both checks now fail closed, without altering the
regression assertions. All failures/logs and intermediate packages/views remain.

Evidence: taskvisualizations/pi-session-output-consumer. Final local review wheel
100b662c9c15082632d4c146df92108c8a256e62e0485f6e4af5a69b51123627
matches all65 runtime files. Actual-root host verification returned MATCH; no
repair, cleanup or service change occurred. No network/provider/player effects,
new ARM/installed/hardware touch or HA-dev acceptance is claimed. Both installed
EADBrc.5 apps and immutable release assets remain unchanged. Independent exact
review/protected source/separate Finalization and a distinct release/approved
operative binding remain necessary before runtime deployment. Artwork gestures,
full header cover, Flow continuity and other parity work remain open. HA-dev
login/Pi10 pairing/active Session click testing remain explicitly human-deferred.


## Flow return and pending-question layout continuity — 21 October 2026

Flow now remembers a visible current playback card when there is no intersecting
admitted native/retained/current-reply prose card. Existing prose and native-body
priority is unchanged. The descriptor still contains only Session/Profile/kind/ID
and a finite bounded pixel offset; it holds no body, media, deadline or display
grant. Returning from current history freshly resolves each supported identity
against the current admitted models, then re-resolves the visual item after
layout. Missing/revoked IDs and scope changes reset safely; they never borrow an
old visual delegate as admission. User dragging/movement, Forecast and explicit
reply-follow take precedence. Old history momentum is cancelled on explicit
return. All supported Flow targets now get at most eight32ms settling attempts,
extending the existing native-body behavior without caching content.

The explicit own-question follow timer now binds the pending client-message ID
and also settles for at most eight attempts. It rereads the owner's current
pending view each time. A late header reflow therefore does not push the just-sent
question out of view. Touch cancels following and a late callback cannot override
the user's reading position. This adds no pending-question history grant or
pending-card back-navigation right; original owner validation and question POST
behavior are unchanged. No new UI copy, protocol or i18n key is needed.

Two original-source failures are preserved: playback-only rememberFlow returned
no descriptor, and the own pending question moved to2250px rather than12px after
a late metadata reflow. The latter loads the exact3288209 QML from its verified
review wheel with unchanged Python/controller bytes; it is a package fixture,
not an installed downgrade. After repair150 targeted actual Qt views cover both
formats/all five locales, real current-history/back clicks, exact pixel/ID return,
changed/withdrawn playback, eight malformed/scope descriptor variants, pending
reflow/withdrawal and genuine Qt touch cancellation. The unmodified existing
composer and artwork tools independently pass436 and180 current-source QML views,
respectively, including native/current-only/retained anchors, original first-fold
thresholds, source expiry, late artwork, user touch, and bounded history windows.
Thus current evidence is766 actual views, not the extra60-view intermediate run.
All three final runs have zero QML errors/binding loops; the targeted run retains
one macOS font-alias startup warning. Both formats were visually inspected.

Forty focused QML/projection tests, Ruff0.16.0 src/tests and diff checks pass.
Only SessionScreen.qml runtime bytes change in this slice. The latest complete
local1994-test suite and27-success/4-conditional-skip CI are explicitly on the
immediate3288209 base, not a newly rerun full suite on this QML head. The local
review wheel23c8d0940d4bab8fb099e2c3752348194e3b13be02ba6f20c97828638bc3a7e9
matches all65 current runtime files. Evidence lives in
taskvisualizations/pi-flow-reading-continuity, with before failures, original-QML
package pin, reproduced harnesses, final images/readbacks and intermediate runs.

Synthetic multiline metadata, own pending text and history envelopes only test
layout. Original producer fixture files, live-source/expiry admission and all
request/response bodies are unchanged. No question transport, model/provider,
HA, OS command, new ARM/installed or physical touch acceptance is claimed.
Actual-root host verification returned MATCH, with no repair or cleanup. Both
installed EADBrc.5 apps and immutable assets remain unchanged. Broader Flow
backward continuity and other parity work remain open; this source slice requires
normal exact review/protected source/separate Finalization and a distinct release
before runtime deployment. HA-dev authentication and the active Pi10 Session test
remain explicitly human-deferred.

## Single saved-Session deletion consumer foundation — 21 October 2026

The received Core archive producer is now independently pinned for this bounded
consumer work: protected source bbb7a23da015de5887eff4103efed9981f12b0bd and separate
Finalization 2a1197c441079896bdfdfdc5a2c732146f54ccd3. Both actual post-merge status
readbacks say POST_MERGE_RELEASE_EVIDENCE_QUALIFIED, runs39572775746/39575446305.
The exact Final handler fetched through GitHub matches the exported source bytes.
Contract and synthetic fixture retain SHA256 b5ffa5ae79e7e0d2f900600bd3873fefe44807de966cc39779ce72d0639fc52b
and79fac1e077a157df0851797c84de2f1f61bc14be08f3048c703ba9acec9f2a67.
The handed-off private owner installation receipt was read and matches those pins,
228 files and payload f2be1e18b19b48be7a34e027cecc36e221e04336bfe833e68046206faf70e569.
That is owner-receipt readback, not a Pi-authenticated HA or personal-erasure test.
Other unchanged product consumers keep their previously documented producer pins.

Implemented source is deliberately the typed transport/consent foundation;
**there is no deletion button, controller scheduling or archive invalidation yet**.
No destructive UI capability is exposed. Single deletion uses only the existing
paired POST session/history/delete. Its closed body omits generic profile_id and
private_session hints; the original Profile header and current binding remain.
The route uses a fresh isolated HTTP session, no ambient credentials/redirects,
streamed2MiB control budget and the existing shape limits. Binding/401/403 checks
still precede body reads. Only this closed route reads bounded5xx bodies to retain
the producer's history_delete_outcome_unknown distinction; arbitrary errors are
never retained. Other requests keep their prior error behavior. Success requires
strict schema1, deleted:true and exact operation/owner/target receipt. No response
imports Runtime, history or configuration, and no request is automatically retried.

The RAM-only SingleDeleteIntent accepts an explicit bool confirmation, strict
single capability/version1, original explicit/resolved Profile, original epoch,
terminal fresh-detail header with opaque revision, original selected Session ID
and known parent retention deadline. It stores no page body or grant. It mints
one UUIDv7 at confirmation and keeps the earlier of that original operation's
five-minute deadline and the original retention deadline. Clock rollback cannot
renew it; the30-second UUID future-skew check remains separate from expiry.
Atomic claim consumes one send ticket, including a timeout, and cannot be rearmed.
Recording/display privacy modes are not used as a new erasure prohibition.
The forthcoming UI owner must freshly read before confirmation, gate queued work
and late receipts on its live epoch/context, keep End available and invalidate the
whole archive only after the exact receipt. Those integrations remain OPEN.
Bulk snapshots/delete-all and individual Moment/bubble/uncertain deletion are not
implemented by this slice; the latter remain a separate Core dependency.

Validation:109 new synthetic tests;175 focused deletion/existing-transport checks;
full integrated2103 tests PASS, no skips,39.22s; Ruff0.16.0 src/tests and diff checks
PASS. Cases cover exact closed payload, denial-before-body, no redirect/replay,
malformed/oversized/deep JSON including503, exact receipt fields, integer-list
revision rejection, terminal/selection/owner/epoch/capability fences, concurrent
single claim, original retention and conservative-clock expiry. The earlier106-
case/2100-test run precedes the three final selected-target cases and is retained
separately. Initial import/dict lint diagnostics are retained. A source inspection
caught and removed an unimplemented owner field assumption before qualification;
the actual detail header has no owner_profile_id, so authority stays in its paired
binding rather than an invented wire field. No test or producer fixture was weakened.

Local review wheel f0d124d9d857f94cbdac37e20c35d23a7b9f482bcd32ba4673d593e0082d5a27
matches all66 runtime files (one new Python module). No QML/controller/i18n bytes
changed and no new Qt-view, ARM, installed, provider, HA, model or physical result
is claimed. Evidence:taskvisualizations/pi-history-delete-consumer-transport with
exact producer exports/status/receipt readbacks, logs, package and diagnostics.
Fresh actual-root hostverify MATCH; no repair/cleanup/other-lane write occurred.
Both installed EADBrc.5 apps and immutable publication remain unchanged. Independent
PR119 review, protected delivery, separate Finalization and a distinct approved
release remain required before any runtime deployment. HA-dev authentication and
the Pi10 active-Session click test remain explicitly human-deferred.

## Confirmed single saved-Session deletion UI — 21 October 2026

This supersedes the preceding foundation-only UI status for SINGLE Session
removal. The shared historical detail now exposes a red-tinted trash action only
with strict session_history_delete:true/version1, a terminal archived target,
original known parent retention and the current explicit/resolved paired Profile.
The active Runtime cannot be selected for erasure. No active Runtime is required
in order to erase an earlier Session. Individual contributions remain view-only;
bulk and individual-content erasure are distinct OPEN functions, not rights
inferred from this button. Five new i18n keys are present in all five locales.

The first deliberate click performs isolated fresh owner-active, capability and
authorized detail reads. The opaque detail Session revision must still equal the
original displayed target's revision; numeric list metadata never becomes CAS.
The confirmation identifies the selected Session by its existing localized date.
Only its explicit destructive button mints the original UUIDv7 intent. A separate
max1 worker repeats those owner/capability/detail/target/context checks and claims
one send ticket before the existing typed POST. Original binding, archive view
epoch, current Runtime identity (including none), target, opaque revision and
parent deadline fence queued work and delivery. No command response is imported
as Runtime, no setting/pairing/playback/lifecycle effect is attached to erasure,
and no automatic POST retry, new operation ID, fallback or replay exists.

About-to-hide immediately withdraws the queued ticket before an exit animation.
Navigation, visibility, foreground, Profile/token, archive epoch, selected target,
revision, capability, retention and End changes likewise withdraw it. Started HTTP
may finish; closing the dialog never promises server cancellation. The button
says Close after confirmation rather than implying that it can undo a started
request. Other control/input work is gated while the dedicated worker runs, but
End keeps its independent executor. Two real held-worker tests prove that End
remains immediately available during both checking and confirmed-send preflight.

Only the typed exact owner/operation/target/schema/deleted:true receipt causes
whole-archive invalidation: list/windows/cursors, detail trail, search, historical
selection/navigation descriptors and queued reads lose their archive epoch.
This is not a client loop or optimistic removal of one row. Current Session,
active Flow, settings and pairing are preserved, with a separate ordinary owner
refresh resolving any server-withdrawn dependent Flow contributions. The receipt
itself is not a projection. Current media remains a separate owner; the Pi has no
historical-media loader to claim qualified here. A late worker/GUI callback cannot
replace a successor view. An uncertain result never claims erasure and blocks a
new delete intent until explicit recovery. Recovery withdraws stale archive views
and independently reads the archive; it does not repeat the POST. Its one bounded
QObject-owned zero-delay timer runs after QML's existing search-target/view-epoch
transition, and rechecks owner, visibility, foreground, idle state and absence of
a newly selected detail before starting that read. No history TTL or native grant
is manufactured from this operation's five-minute journal lifetime.

Final validation:84 new controller/worker cases,259 focused new/existing deletion
and transport checks PASS; full integrated2187 PASS/no skips39.45s. The final
current-source Qt evidence is150 actual single-delete views plus100 unmodified
history-window views, both formats/all five locales, with real mouse checking,
confirmation/cancel/close, no optimism, success, unknown version, active-target
refusal, changed revision, original expiry, uncertain read-only recovery and the
no-active-Runtime case. Zero QML errors/binding loops; one font-alias startup
warning per process is retained. Both final formats were visually inspected.
Earlier140/150-view runs are intermediate and are not added to this250-view gate.
Ruff0.16.0 src/tests and diff checks PASS. Local review wheel
8c5203c5f6c0a25528665b97929eecf6e27050f224e560540f66f02d20072ff8
matches all67 runtime files, including the new controller module. No new ARM,
installed, actual HA/provider/model, physical-touch or personal-erasure result.

Diagnostics are preserved, not promoted to passes. One initial fixture's bogus
current reply was correctly withdrawn; a proper admitted-reply fixture now proves
preservation. Its original historical display clock initially rejected a real-wall
UUID; only that synthetic operation clock was aligned, never the original grant.
A real QML race initially invalidated the recovery read when clearing the derived
search target; the bounded deferred-read implementation fixes it without changing
existing search/epoch fences. One integrated Python process then segfaulted in Qt
timer dispatch during processEvents: that run is FAILED, not a full-suite PASS.
New notification/recovery callbacks now use QObject-owned single-shot timers,
stop on shutdown and do not emit a result after their owner closes. The full
collection subsequently passed2186, followed by final2187 after the added
no-active-Runtime regression. The underlying general PySide cause is not claimed
proven, nor is a hardware bug or ARM fix inferred. All original failed logs,
intermediate runs, reproducing harnesses, final pixels and package receipts remain
under taskvisualizations/pi-history-delete-single-consumer.

The qualified producer pins remain source bbb7a23 / separate Final2a1197c for
this archive operation, verified in the preceding checkpoint. Other unchanged
product consumers keep their existing pins. Fresh actual-root hostverify MATCH;
no repair, cleanup, other-lane source write, HA login, personal erasure, publication,
installation or operative rebind occurred. Both actual EADBrc.5 apps remain
unchanged. Independent exact PR119 review and normal protected source, separate
Finalization, distinct immutable release and new approved operative binding remain
required before runtime deployment. HA-dev authentication and the active Pi10
Session click test remain explicitly human-deferred. Next functional follow-through
is separately confirmed bulk archive deletion or another larger open parity gap.


## Confirmed whole-archive deletion — 21 October 2026

Bulk saved-Session deletion is now SOURCE delivered, independently capability-gated
by strict session_history_bulk_delete:true/version1. The shared archive list has
an explicit action that first reads fresh owner-active/capabilities and the released
GET session/history/delete_snapshot. It validates schema1, exact resolved owner,
opaque token, strict nonnegative exact-display count and original created/expires
metadata. The server selects the complete terminal retained set, independently of
client pages/search/filter. No detail parent display deadline is invented. Empty
count is informational: no destructive confirmation, operation ID or POST. Five
new localized keys cover action, count/scope confirmation, empty, conflict and
completion in en/nl/de/fr/es.

Confirmation binds original Profile/device/token, archive view epoch, current
Runtime identity (including none), immutable snapshot/count and original expiry.
One new UUIDv7 is minted only on deliberate confirmation. The same max1 archive
worker repeats fresh owner-active/capabilities, claims one atomic send ticket and
sends exactly one typed delete_all POST. It never replaces the snapshot at send,
loops over singles, sends client target lists or adds profile_id/private_session
body hints. Original snapshot expiry and UUID five-minute/30-second bounds remain;
these are operation authority, not private/native display grants. Close, navigation,
foreground, Profile/token, capability, active Session or archive epoch changes
withdraw queued work immediately; started HTTP may finish. End remains independent.
No privacy-mode erasure type ban, automatic replay/renewal/fallback, response import
or optimistic erasure exists. Snapshot conflict requires new explicit checking and
consent. Pending503 remains uncertain and offers explicit readonly recovery.

Only the exact typed schema/owner/op/snapshot/deleted:true receipt with the captured
count invalidates the WHOLE archive via the existing list/window/cursor/detail/
search/selection/navigation/late-read fences. Active Session/Flow/settings/pairing
remain separate; a normal independent owner read resolves dependent server Flow
withdrawals. Sessions ending after snapshot preparation are outside its server set.
Bulk is not Profile, MusicDNA or preferences erasure. Individual content deletion
remains outside this slice. No historical-media loader or physical acceptance is
claimed. Released producer pins remain bbb7a23 / separate Final2a1197c.

Final qualification:136 new cases;395 focused deletion/transport PASS; full2323
integrated PASS/no skips40.31s. Final actual Qt gate530 views =150 bulk +150 single
+100 unmodified history-window +130 unmodified playback regressions, both formats
and five locales. Real mouse clicks check count/scope, cancellation, no optimism,
zero, unsupported version, conflict, close before worker, original expiry, no-active
Runtime and readonly recovery. Zero errors/binding loops; startup font-alias
warnings retained. Both final layouts visually inspected. Ruff0.16.0 src/tests and
diff PASS. Local review wheel dc179d565a908d5ca0bfaa4647f25941876435deecea68de7576579c549c2572
matches67 runtime files. Evidence:taskvisualizations/pi-history-delete-bulk-consumer,
qml-final/single-final/history-final/playback-final, package and retained diagnostics.
Intermediate views/runs are not added to530. No new ARM/installed/liveHA/provider/
model/physical-touch/personal-deletion result; both installed EADBrc.5 apps unchanged.

Diagnostics: the first Qt run caught an unfilled Python-format count placeholder;
percent-one substitution and five regressions fix it without changing existing keys.
A subsequent full process FAILED exit139 during Qt timer dispatch. An isolated
30-owner repro proved60 pre-existing playback visibility/cancel notifications
attempting deleted signals, but did not itself segfault: the general segfault root
cause is NOT claimed proven. Both callbacks now use one QObject-owned/coalesced
zero timer, stopped on shutdown/destruction, preserving immediate revocation and
deferred QML notification. The repro then had no stderr; two subprocess and one
deferred/coalescing tests pass. An initial test counted its separate fixture archive
notice; it is drained before the coalescing measurement, not asserted away. Full2323
and the final Qt gate passed afterward. Failed/intermediate logs remain preserved.
Fresh actual-root hostverify MATCH; no repair/cleanup/other-lane write. Independent
exact PR119 review, protected source/separate Finalization/distinct immutable release
and new operative binding are still required for deployment. HA-dev login and Pi10
active-Session click test remain explicitly human-deferred.


## Original archive deletion status recovery — 21 October 2026

This SOURCE slice adds explicit readonly status recovery for the ORIGINAL single
or bulk archive operation. Pi independently verified protected Core source1253
58561f97a04c36fce21ba5e6886eb6c3640a4ec3 and separate Final1254
b4bf47018d165e4f9e171291425a7a134ca9e0d2, actual canonical qualified statuses
39591327915/39593182742, and exact contract API/git bytes: blob26299c6f881ac30863cac073d1bf55948cd32a79,
SHA2563a868d32af4c9c68fb157c5795d6446a25210d5bb4a6963de48ca5c8cbbc0723.
The private owner-installed receipt was read independently:232 source/Final files
match, payload90766c59519934c4c960ca7599fce24bc2491714f0aaf2b409591066e8c32805,
schema12/integrityOK/0pending, single/bulk/content/status capabilities1. This is
OWNER RECEIPT readback, not Pi HA authentication, personal erasure, new operative
pair or installed client acceptance. Individual-content prepare/delete UI remains
client-owned work; no Core producer gap is inferred from its absence in Pi.

The separate strict session_history_delete_status:true/version1 action appears
only for a possibly posted original RAM intent in the same explicit/resolved
Profile/device binding. It reuses the existing max1 archive worker; fresh owner-
active/capability reads and a new visibility/view/current-Runtime read ticket
fence GET session/history/delete/status. Query contains only paired identity,
contract_version1, original operation ID/mode and exact original single target/
opaque revision or bulk snapshot token. No confirmed, confirmation_id, Profile/
private-session body hint or new operation is created. Isolated HTTP, original
Bearer/Profile authority, URL/credential/redirect/no-retry guards and streamed
2MiB/shape budgets remain. Four new keys in all five locales explain checking,
pending, unknown and expired_unknown. Once the original POST may have started,
the dialog says Close even while checking; no fictitious server cancellation.

Typed admission verifies outer schema/owner/op/mode/body/digest, strict definitive
boolean and one of four released states. Completed additionally requires the
original exact nested receipt and captured bulk count; the client rejects a
completed result beyond its ORIGINAL UUID journal lifetime. The status query can
report expiry but cannot renew snapshot/operation consent or any display grant.
Unknown/pending/expired and status-request validation/availability errors never
settle an earlier ambiguous POST. They retain uncertainty and block a new delete
intent. An explicit ordinary archive reload may withdraw stale views but likewise
retains the original identifier-only RAM intent; another status click reads that
same ID/body. No polling, new-ID retry, mutation replay or persistence of content.
Owner/auth context withdrawal clears RAM state. Only a bound completed original
receipt invokes whole-archive invalidation plus normal independent owner refresh;
active Flow/settings/pairing/playback remain separate. End is independently free.

A real QML regression found that clearArchive announced a changed list while the
old detail was still present, letting the later derived searchTarget change
invalidate the new recovery read. invalidateArchive now clears archive/list/detail/
search/trails/selection first and then announces the complete withdrawal. Public
clearArchive keeps its existing behavior. The observer regression sees no stale
intermediate detail; all epoch/search/late-read fences remain unchanged. The failed
Qt run and instrumented diagnostics are preserved, not counted as passes.

Final qualification:126 new cases;521 focused status/deletion/transport PASS;
full2449 integrated PASS/no skips40.77s. Final actual Qt gate540 views =240 status
(single/bulk, unknown/pending/expired/completed, bad result, cancel/withdrawal,
readonly refresh retaining uncertainty, same-ID recheck) +150 unmodified single
+150 unmodified bulk regressions, both formats/all five locales. Zero QML errors/
binding loops; one font-alias startup warning per process retained. Both formats
were visually inspected. Ruff0.16.0 src/tests and diff PASS. Local review wheel
f4b09061ee9aecf25fe5ada5e343c2800c81452ef4100a94ab23913064ecd901
matches67 runtime files. Evidence:taskvisualizations/pi-history-delete-status-consumer,
qml-v2 (FINAL), single-regression, bulk-regression, package and exact producer
exports/readbacks. Earlier qml-v1/diagnostic dirs are INTERMEDIATE, not added.
No ARM, new installed/live HA/provider/model/physical touch or personal-delete PASS.
Both installed immutable official EADBrc.5 apps and operative binding are unchanged.
Fresh actual-root hostverify MATCH; no repair/cleanup/other-lane write. Independent
exact PR119 review, protected source/separate Finalization/distinct release/new
approved operative binding remain required for deployment. HA-dev authentication
and active Pi10 Session click test remain explicitly human-deferred.


### User-reported installed Pi issues — 21 October 2026

Read-only actual 4-inch logs show Track Insight rejected with device_not_mapped
and Music DNA with music_dna_context_changed. CORRECTION: the normal HA-dev UI saved a Store row labelled DJConnect Pi to
the requested iPhone17Pro Profile, but that friendly-name selection did not
identify the physical Pi. Owner metadata later proves physical D83ADD41F167
is absent from that Store; its separate configentry was the diagnostic that
matched the real Pi. No physical mapping or live-function PASS is claimed.
Writes are stopped pending exact affected-row and prior-binding proof. Pi10 normal pairing with verified Raspberry Pi selection
fails invalid_client_type before POST pair. Peter authorized a concrete handoff
to the current Core owner, who accepted the manual-URL discovery-ID defect.
No invented IDs/client types, replay, root configuration edits or pairing bypass.

Source corrections remove the legacy local mood control from Now Playing; the
server-owned DJ Session mood toolbar remains. About's existing three sections
now use shared GlassCard. Privacy uses applicable exact protected Apple e106a467
prose (data, token storage and AI caveat), replacing extra invented Pi headings.
Apple push/voice/platform framework claims are not copied into unsupported Pi
features. Legal keeps the two Apple legal paragraphs together and Pi-specific
OSS/license information; repeated notices are removed. Rejected discovery feeds
cannot adopt a Profile, import result rows or display raw machine error/message
as content. Closed Profile-related Session 409 errors show Profile guidance
instead of falsely implying a network outage; pairing and write guards remain.

Own-source qualification:244 focused PASS, full2454 integrated PASS/no skips
42.90s, Ruff0.16.0 src/tests and diff PASS. Final150 actual offline QML views
cover both formats/five languages; no QML errors/binding loops. Earlier150 are
intermediate, not added. About and Privacy inspected visually. Local review wheel
f6f5b102da04d640136a7e23d00b99d5dd916e969269681a84403f1a2d0e7d97 matches67 runtime files. No new ARM, installed, live
Session/provider/model/physical-touch acceptance. Original492 Linux CI Qt timer
segfault remains FAILED evidence; local PASS does not close that CI diagnostic.
Evidence:taskvisualizations/pi-user-reported-ui-fixes; original logs preserved.


### Backend timer lifetime and actual CI diagnostic

Exact5f2e619 CI independently read:26 SUCCESS/4 conditional SKIPPED/1 FAILURE.
Failure is TDE observe coverage, not a fully green head: real Linux Qt6.11.2
exit139 at bulk readonly recovery processEvents again; normal Python job passed.
No rerun/status override or general native/ARM root-cause claim.

A separate actual Qt probe proves a concrete backend lifetime defect: after
shutdown the shared-settings periodic timer remained active and both delayed
startup readers still fired. Startup250/350ms and deferred settings reconciliation
now use QObject-owned single-shot timers; shutdown stops these plus the periodic
settings timer. Shutdown guards reject new refresh/settings work and late settings
results cannot rearm polling. Normal initial timing is preserved. Three isolated
actual Qt dispatcher probes prove running delivers each startup read once, while
shutdown/destroy deliver none. No network or OS effect.

App-backend tests now retain, shut down and delete each test's native backend and
actual worker pools; submit-only fake executors do not hide the original pools.
The Session controller fixture closes owned resources before native deletion.
No processEvents call, functional assertion or coverage threshold was skipped.
The old static-singleShot spy now checks the actual deferred owned timer.

Four new regression cases,495 focused PASS; full2458 integrated PASS/no skips
44.51s and independent coverage7.16.2 full2458 PASS/no skips45.53s. Final150 actual
offline QML views on this timer source/both formats/five locales, zero errors;
earlier150 runs remain component/intermediate proof and are not added. Ruff and
diff PASS. Local review wheel 9fe1ca7f4046fe3fcc518bf94cf5ea60eb107ae0dd2ed490d19c638e88b7ed3d matches67 runtime files.
New exact-head CI remains required; these local results do not by themselves
prove the Linux crash's full root cause. Evidence/coverage XML/original failures
retained in taskvisualizations/pi-user-reported-ui-fixes. No new runtime install.

Profile diagnostic correction: owner read-only metadata now proves the requested
iPhone17Pro Profile ID is profile-fd38fad08e19, distinct from physical Pi4
configentry/explicit profile-b5189fb44f4f. However, the actual physical Pi4 has
no row in the ProfilePlatform Store. The earlier UI save selected another row
with the friendly label DJConnect Pi; separate configentry identity proof did
not identify that dropdown row. This mistake was disclosed to Peter and Core.
All further mapping writes are stopped. The owning Core lane was asked for
exact affected-row and proven prior-binding metadata for ordinary UI restoration;
no guessed rollback, forced mapping or client-context clearing is allowed.
Both HA-dev pairing approvals stand; Pi10 remains unpaired awaiting normal Core
manual-URL fix and protected/Final/installed readback. Authentication is resumed.


### Direct Session entry, welcome card, banner alignment and optional cache (21 October)

Peter explicitly requested direct active-Session presentation, otherwise the
Session creation screen, and both brand text lines beside the mark. This local
candidate supersedes the extra Pi-only Use this Profile step. A valid current
server-resolved device mapping may now scope Session requests without a second
local confirmation or config write. Existing explicit choices must still agree
in controllers; missing/malformed/mismatched mappings remain unavailable. The
original raw explicit choice remains part of the request/result binding fence.
Core still authenticates every device request and rejects mismatched mapped
owners. Private-mode, native/media admission, original deadlines, revocation,
context epochs and no-replay rules remain; no new mapping/grant/audio permission.

The shared welcome card has localized hero copy, local decorative record art,
Mood/Presence/Persona choices and a gradient Start button. Choices come only
from current server settings options/writable fields; each explicit click sends
one existing typed settings patch with its edit token. Loading, programmatic
updates and selection rendering never write. Selection shows confirmed server
values, with no optimistic change. Start is disabled during unavailable,
selection-required, pending/unknown or busy settings. The existing Start request
is unchanged; released Core8b Runtime inherits activated Profile defaults,
including Persona/Presence. Active Runtime hides the welcome card. No local
speaker/microphone activation and no invented presence option or wire field.

The AppBanner now places the original mark next to a single text column. The
outlined name uses the original compact asset's alpha bounds(525,142,1092,162)
through QML sourceClipRect, without editing the asset or redrawing its type.
Localized detail text shares the same left edge below the name, beside the mark.
Both sizes/five languages have actual geometry and pixel checks.

Actual Pi10 normal HA-dev pairing succeeded after qualified Corebf6b/Final0090
and the owner-installed receipt. Public info says paired:true; physical Start
was performed by Peter. An actual VNC capture shows DJ Session/Profile guidance,
not an active Flow acceptance. Recent logs then stopped reporting503 and instead
showed PermissionError in optional album-art cache mkdir. This candidate moves
mkdir/existence/stat into the existing optional-cache fallback, preserving the
original image URL and playback refresh when local cache access fails. No live
chmod/chown/config patch or reinstallation was done. Legacy030549 restoration
still awaits the separate user's choice; it was not automatically changed.

Final local qualification:19 new meaningful cases,292 focused PASS; full2477
integrated PASS/no skips47.92s; Ruff0.16.0 src/tests/diff PASS. Final70 actual QML
views(both formats/five locales) cover explicit settings clicks/no optimism,
pending/unavailable Start, one explicit Start, active Session without onboarding,
and brand geometry. Zero QML errors/binding loops; one startup font-alias warning.
Earlier60/70 views are intermediate, not added. The unmodified broader composer
first found an implicitWidth binding loop in the hidden new card; that436-view
run is FAILED. A fixed natural card width breaks the dependency without changing
fill-width layout or tests. Final-v2 has70 targeted/brand+436 unmodified composer
+180 unmodified artwork views=686 current views, zero errors/binding loops.
Review wheel
ccdcf4ab70673f35911afe2b40ac8c1c97fd7cb70b2dd8caefcb6295748e2592
matches68 runtime files. Original producer fixture bytes are unchanged; owner,
settings and Session joins in these previews are synthetic, network/OS calls
blocked. The original first-fold, native/source expiry, touch, context/queued-question
and no-replay assertions remain unchanged. Evidence:taskvisualizations/pi-session-start-direct-entry.

This is source/review evidence, not installed/live Profile/Flow/physical-touch
acceptance. Both installed binaries remain immutable official EADBrc5. Current
source candidate remains local while the actual host retention
gate reports a newly expired Core-output pair after the previous owner archive.
No protected push/merge/publication/deployment or other-lane cleanup. Independent
PR119 review, separate Finalization, distinct release and fresh operative binding
remain required before new runtime installation.
