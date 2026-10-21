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
