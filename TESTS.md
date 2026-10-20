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
  QML `grabToImage` capture contract
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
