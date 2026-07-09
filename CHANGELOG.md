# Changelog

## 3.2.14

- Add a compact mood selector to Speelt nu that stores the selected mood and
  sends it through the existing Home Assistant mood context paths.
- Move Wachtrij into the primary bottom navigation next to Speelt nu, move
  Music DNA behind Meer and remove Wachtrij from the Meer overflow menu.
- Add a separate automatic return-to-Speelt-nu setting with 30/60/120/off
  choices, defaulting to 60 seconds, while keeping screen blanking independent
  and preserving the current screen after wake when return-to-now is disabled.
- Make Ontdek recommendation rows taller and one-per-row, and open Waarom
  reason text in a full-screen details view with a close button instead of a
  toast.
- Widen and lower the Games playfield and keep Maze Chase inside a fixed
  320:170 canvas aspect ratio.
- Polish Ask DJ, Logs, About, Settings, Track Insight, Music DNA and Ontdek
  touch flows: newest history/log entries first, compact top-right refresh
  controls, confirmation before Music DNA disable/clear and removal of
  redundant About/Settings rows.
- Move Music DNA enable/disable and listening-profile clear controls into the
  Settings screen with dedicated Music DNA labels and localized copy.
- Add the Raspberry Pi control-screen favorite heart action with backend-owned
  favorite state/capability handling, while keeping it off the Now Playing
  screen.
- Keep Now Playing focused by removing the Track Insight shortcut and keeping
  Track Insight available from its dedicated navigation surface.
- Improve screen wake behavior so tapping an already-awake screen does not jump
  back to Now Playing, and waking from a blanked screen respects the separate
  return-to-now setting.
- Extend contextual toast icon support and make Track Insight HTTP fallback
  tolerate slower backend responses.

## 3.2.12

- Correct the Raspberry Pi Ask DJ capability payload for `readonly_actions` by
  advertising `ask_dj_free_input_supported:false` in both the local device API
  and Home Assistant pairing/status payloads.

## 3.2.11

- Make the Raspberry Pi Track Insight surface contract-complete for the current
  Home Assistant server-side response shape: direct and wrapped responses
  decode to the same UI model, language/locale/mood/Music DNA context and
  current track metadata are sent with `/api/djconnect/v1/track_insight`, and
  404 `no_track_playing` plus 429 `rate_limited` clear stale analysis into
  retryable empty states.
- Keep Track Insight rendering within the central contract by showing
  summary/full text, genre/subgenre, visual/mood context, production,
  instrumentation, arrangement, listening cues and 0..1 metrics as
  percentages, while filtering BPM/key/model-style fields out of the UI model.
- Tighten Raspberry Pi Ontdek / Music Discovery against the current central
  contract: render backend `sections[].items[]` without local recommendation
  generation, dedupe repeated `id`/`uri` items, show compact repeated-play or
  based-on counts and keep disabled feeds as empty/degraded states.
- Send Music Discovery Play Now actions only through
  `/api/djconnect/v1/music_discovery/play` with Pi identity plus `section_id`
  and `discovery_item_id`; non-playable recommendation rows no longer trigger
  generic playback from the card.

## 3.2.10

- Update all Raspberry Pi Home Assistant DJConnect HTTP client routes to the
  canonical `/api/djconnect/v1/...` prefix while preserving the
  `client_type=raspberry_pi` identity contract.
- Add regression coverage that fails if source, tests or docs reintroduce a
  hardcoded Home Assistant DJConnect route without the `/v1` prefix.
- Refresh route references in architecture, bootstrap, handoff and README
  documentation while leaving local Pi `/api/device/*` routes unchanged.

## 3.2.9

- Add the server-authoritative Music DNA dashboard/opt-in flow on Raspberry Pi,
  including profile/settings/clear UI, hidden empty dashboard blocks and no
  local Music DNA aggregation.
- Add the Ontdek / Music Discovery main navigation page with Music DNA consent
  gating, HA-provided recommendation rendering, reason details and Play Now
  calls through `/api/djconnect/v1/music_discovery/play`.
- Add HTTP and websocket client coverage for Music DNA and Music Discovery
  contracts, plus QML/nav/parser tests and updated docs for the new feature
  boundary.
- Sync the Raspberry Pi Ask DJ client with the current Home Assistant
  integration contract by forwarding language, locale and optional mood
  metadata on Ask DJ, command, status, Track Insight and Music DNA requests.
- Add server-backed Music DNA profile/settings/clear client calls while keeping
  the Raspberry Pi renderer/controller-only with no local Music DNA analysis or
  Spotify OAuth credentials.
- Update Track Insight rendering to show backend interpretation fields such as
  summary, genre, vibe and production context while removing BPM/key display.

## 3.2.7

- Render Home Assistant queue metadata on the Raspberry Pi client by showing
  returned track artists and album details instead of title-only rows.
- Accept both flat `queue: [...]` and nested `queue.items` queue payloads while
  preserving queue context and avoiding playlist/search result lists.
- Prefer backend artwork aliases in queue rows, including `album_image_url`,
  `image_url` and `thumbnail_url`.

## 3.2.6

- Send the current Raspberry Pi app language as BCP-47 DJConnect request
  metadata for user-facing Ask DJ, command, status/capability and WebSocket
  payloads, while keeping pairing/bootstrap payloads and protocol values
  unchanged.
- Add tests for HTTP and WebSocket locale propagation so Home Assistant can
  resolve response language from client metadata before Assist/TTS defaults.

## 3.2.5

- Remove the web portal's separate Dutch/English translation table by
  generating portal strings from the central `src/djconnect_pi/i18n.py`
  resources for `en`, `nl`, `de`, `fr` and `es`.
- Add web portal translation-key coverage tests so future portal labels stay in
  sync with the supported locale set.
- Update the release script for protected-main repositories with
  `--no-push-main` and per-version release notes instead of publishing the full
  changelog as every GitHub release body.

## 3.2.4

- Include the temporary pairing code in the Postman local Client API pairing
  request and CI mock server so the release publish workflow exercises the
  current `/api/device/pair` validation contract successfully.

## 3.2.3

- Add Raspberry Pi client localization support for English, Dutch, German,
  French and Spanish across touch UI, update UI, setup/status strings, Ask DJ
  fallback labels and local API display payloads.
- Default unsupported language settings to English while still detecting
  supported Raspberry Pi OS locales locally; Home Assistant language
  provisioning remains ESP-only.
- Add translation validation for supported locale key parity, placeholder
  parity and QML translation-key coverage so future user-facing strings must be
  added consistently.
- Extend Raspberry Pi OS bootstrap locale generation to include the supported
  UI language families.

## 3.2.2

- Align the Raspberry Pi local-device pairing shape with the ESP32/HA contract:
  pairing-info and mDNS now expose pairing paths, code aliases, model/api
  metadata and firmware/version aliases, and `/api/device/pair` validates the
  temporary pairing code before storing the device token.
- Align Ask DJ and Now Playing with the HA Track Insight contract:
  `/api/djconnect/v1/track_insight`, `intent/action/type/open_screen:
  "track_insight"` and normalized `track_insight` rendering.
- Use Music DNA terminology and `music_dna_key` / `X-DJConnect-Music-DNA-Key`
  throughout client-facing payloads and headers.
- Render Track Insight as read-only unless the backend explicitly returns
  `playback_actions[]`; show Music DNA Match from
  `track_insight.music_dna.match_percent`.

## 3.2.1

- Sync the Raspberry Pi client with the Home Assistant 3.2 backend contract:
  typed Ask DJ messages now explicitly request text-only responses with
  `audio_response:"never"`, while replay UI remains available only when HA
  returns an `audio_url`.
- Report `ask_dj_voice_supported:false` and
  `ask_dj_audio_response_supported:false` in pair/info capabilities so Home
  Assistant does not infer Pi voice, PTT, local TTS or audio response support.
- Normalize safe object-shaped `music_backend_error` values into compact
  code/message text for About, diagnostics and local API output.
- Document the intentional Raspberry Pi contract choice: typed text-only Ask
  DJ via Home Assistant, no Pi-local `/api/device/dj_response`, no voice/PTT
  and no local DJ response audio.

## 3.2.0

- Upgrade the Raspberry Pi client protocol to 3.2.x while preserving
  `client_type: raspberry_pi` in pair/status/command/Ask DJ payloads.
- Keep Raspberry Pi transport local-only: pairing stores only `ha_local_url`,
  ignores accidental `ha_remote_url` values and exposes Local only in
  diagnostics/About output.
- Parse the Home Assistant music backend summary, including backend name,
  availability, revision, target player, error and capabilities, and show it in
  status/about/diagnostics surfaces without storing Spotify credentials.
- Surface unsupported backend capability and stale backend action responses as
  user-facing Ask DJ/backend messages instead of attempting Spotify-specific
  fallbacks.

## 3.1.111

- Align Raspberry Pi Ask DJ with the server-side contract: typed prompts send
  `audio_response:"auto"`, backend-returned actions are posted back without
  client-side playback inference, output actions use the returned value, and
  audio replay is shown only when the backend response includes `audio_url`.
- Document the Ask DJ rendering and action boundaries so the Pi never parses
  visible text, reuses previous artwork, stores Music DNA locally or creates
  local TTS bubbles.

## 3.1.110

- Open the Ask DJ touch keyboard as an overlay directly below the prompt field
  when the field receives focus, instead of reserving fixed space in the chat
  layout.

## 3.1.109

- Add a Now Playing favorite action that sends `save_current_track` through
  the shared DJConnect command endpoint.
- Render Ask DJ `save_current_track` control actions as direct favorite buttons
  without routing them through recommendation playback or adding extra artwork.
- Show concise saved/failed feedback for Spotify favorite saves while keeping
  normal authentication policy intact.

- Keep queue item playback in queue context by sending `play_context_at` and
  leaving the Queue screen open instead of jumping back to Now Playing.
- Normalize touch UI button corner radii across standard, Ask DJ, warning and
  danger buttons while keeping Meer menu rows and bottom navigation on the
  original shared radius.
- Show the normal refresh toast when the Ask DJ screen is manually refreshed,
  while keeping the automatic history load on screen open quiet.

## 3.1.107

- Update Raspberry Pi Ask DJ for the Home Assistant v3.1.92 contract: typed
  text messages use `/api/djconnect/v1/ask_dj/message`, history sync keeps
  `since_revision`, history clearing uses `/api/djconnect/v1/ask_dj/history/clear`
  and capabilities advertise text actions while voice/PTT/TTS/local audio stay
  disabled.
- Render Ask DJ response `items[]` as compact rows, keep memory summaries
  text-only and route HA-provided control, output, confirmation and Play Now
  actions through `/api/djconnect/v1/command` without local intent reconstruction.

## 3.1.106

- Apply the blue-to-magenta button gradient across the Raspberry Pi UI.

## 3.1.105

- Remove the Ask DJ audio replay button from the Raspberry Pi UI.
- Show SSH and VNC tunnel commands in the updater Remote meekijken panel.

## 3.1.104

- Use the blue-to-magenta Play Now gradient for all Ask DJ buttons.

## 3.1.103

- Scroll the Ask DJ history to the newest chat bubble automatically when the
  screen opens or refreshed history arrives.

## 3.1.102

- Normalize album-art extraction for now playing, queue/playlists and Ask DJ
  action rows when Home Assistant/Spotify sends nested `images[]`, `album`,
  `item`, `cover`, `thumbnail` or artwork payloads instead of flat
  `image_url` fields.

## 3.1.101

- Polish Ask DJ on the Raspberry Pi as a read-only action surface: preserve
  server history revisions and trim metadata, show the read-only state in the
  UI, render replay audio only when provided, and dispatch HA-provided action
  commands without local intent interpretation.
- Render Ask DJ playback recommendations and output-device selections as
  list-item rows with artwork or output affordances plus Play Now/Activeer
  buttons, while hiding duplicate speaker bullet text when matching structured
  actions are present.
- Add compatibility fields to the Pi status heartbeat so Home Assistant
  playback sensors can show the active output, available outputs and queue
  count instead of unknown.
- Keep queue item playback in queue context by sending `start_queue_item`
  instead of remapping queue rows to `play_context_at`.
- Reuse the new DJConnect app banner across the touch app, pairing success,
  splash/about overlays and the standalone updater UI.

## 3.1.100

- Update Ask DJ message merging to prefer the server-side `messages[]`
  exchange contract, keep each user question above its assistant reply within
  the same exchange, and deduplicate optimistic, HTTP and history/push copies
  of the same conversation bubble.

## 3.1.99

- Replace the bottom navigation and Meer menu glyphs with consistent QML Canvas
  outline icons so the Raspberry Pi touch UI matches the macOS menu icon style
  more closely and avoids platform-dependent Unicode symbols.
- Extend the repo-only Raspberry Pi OS bootstrap with an optional
  localhost-only `x11vnc` service on port `5901` for SSH-tunneled remote screen
  sharing. The app release installer still does not install or manage VNC.

## 3.1.98

- Add Raspberry Pi Ask DJ `readonly_actions` mode: the touch UI displays the
  shared Home Assistant conversation feed and can render HA-provided structured
  action buttons, without free text prompts, voice input, TTS or local audio.
- Advertise explicit Ask DJ capabilities:
  `ask_dj_supported:true`, `ask_dj_mode:"readonly_actions"`,
  `ask_dj_free_input_supported:false`, `ask_dj_actions_supported:true`,
  `voice_supported:false`, `tts_supported:false` and
  `local_audio_supported:false`.
- Poll Ask DJ history idempotently with the server revision cursor, only after
  pairing/authentication, and back off quietly on unavailable, stale auth,
  version mismatch or network failures.
- Move Afspeellijsten, Games and Instellingen behind a Meer screen so the
  bottom navigation keeps Speelt nu, Bediening, Ask DJ, Wachtrij and Meer.
- Polish the pairing/update UI with an animated spinner, macOS-style app banner,
  pairing-field order alignment, a colon-free pairing heading and a play icon
  on the demo-mode button.

## 3.1.95

- Add the Raspberry Pi text-only Ask DJ screen with server-side history sync,
  clear/trim metadata handling, HA-proxied images, clickable sources, Play Now
  actions and confirmation follow-up buttons.
- Add Home Assistant Ask DJ client calls for message, history, clear and idle
  suggestion while keeping Raspberry Pi voice/PTT/audio upload unsupported.

## 3.1.94

- Align the Raspberry Pi client with the canonical sync contract by removing
  the Pi-local `/api/device/dj_response` endpoint and advertising
  `local_dj_response_endpoint:false` while retaining text-only display support
  for DJ response text returned through normal Home Assistant responses.

## 3.1.93

- Remove the updater progress UI's standalone spinner so the update screen
  relies on status text, progress percentage, progress bar and expandable logs.

## 3.1.92

- Refresh bundled systemd service and timer templates during unattended updater
  installs before stopping the update progress UI and restarting DJConnect
  services, so updater-delivered unit changes take effect without a manual
  installer rerun.

## 3.1.91

- Treat the updater progress UI's normal `xinit`/SIGTERM shutdown as a
  successful systemd exit so completed updates do not leave
  `djconnect-update-ui.service` in a failed state.

## 3.1.90

- Refresh playback immediately when the blanked touch screen wakes, so Speelt
  nu updates title, output-device state and album art before the user navigates.
- Cache Now Playing album art locally before QML renders it and allow the main
  album-art image to use Qt caching, improving perceived refresh latency on the
  Raspberry Pi touchscreen.
- Restart the screen-blanking idle timer on screen navigation and backend wake
  events so taps such as switching to Afspeellijsten cannot be followed by an
  immediate stale timeout.
- Remove the remaining toast glow styling in both QML and the web portal,
  preserve active output-device labels from HA `devices` responses and hide
  repeated current-track-only queue snapshots.

## 3.1.89

- Polish the updater progress screen with a larger app icon, a thicker purple
  progress bar, a fully purple DJConnect-style details button, a bottom-pinned
  remote access block that hides while details are expanded, and the title
  `DJConnect wordt bijgewerkt...`.

## 3.1.88

- Style the updater progress UI details button and progress bar with the
  DJConnect purple/orange treatment, label current and target versions, and use
  non-blocking systemd restarts after updater activation so the client cannot
  deadlock waiting for the updater service to finish.

## 3.1.87

- Show the current version, target version, Pi IP address and SSH command on the
  separate updater progress UI, and wake the display when the updater UI starts
  so remote install monitoring is visible.

## 3.1.86

- Add the separate update progress UI and nightly reboot timer to the web portal
  diagnostics list, and refresh release-cycle documentation around the updater
  service split.

## 3.1.84

- Moved the updater progress screen into a separate `djconnect-update-ui`
  entrypoint and systemd service so unattended updates stop the normal touch UI
  before installing while still showing progress, a spinner and live logs.

## 3.1.83

- Preserve an existing unpacked target release during unattended updater resume
  so `.install-state` dependency markers survive reboot and power-loss retries.

## 3.1.82

- Force binary-only pip installs for runtime wheels in both the manual installer
  and unattended updater so Pi installs never fall back to local source builds.

## 3.1.81

- Added a blocking touch update-in-progress screen with a progress bar,
  spinner and expandable live installer logs backed by the updater daemon status
  file.
- Changed unattended updater behavior so the touch UI stays visible while API,
  maintenance and watchdog services stop during an app update.

## 3.1.80

- Wake the touch display and navigate to Now Playing when backend playback
  transitions from paused to playing, matching the existing wake behavior for
  previous/next commands and track changes.

## 3.1.79

- Disable `djconnect-client.service` at the start of the manual installer so a
  rebooted interrupted install cannot start the old client unit, which pulls in
  the old updater through `Wants=djconnect-updater.service` before the manual
  retry can resume.

## 3.1.78

- Disable `djconnect-updater.timer` at the start of the manual installer, and
  re-enable it only after a successful install, so an interrupted/rebooted
  manual install is not raced by the old unattended updater on the next boot.

## 3.1.77

- Stop `djconnect-updater.timer` and `djconnect-updater.service` at the start
  of the manual installer so an old unattended updater cannot race the manual
  install, replace the target release directory and wipe dependency markers.

## 3.1.76

- Split PySide6 dependency installation into separate `shiboken6`,
  `PySide6_Essentials`, `PySide6_Addons` and `PySide6` marked steps in both
  the manual installer and unattended updater, so Pi reboots during the large
  Qt wheel install can resume at the next subpackage.

## 3.1.75

- Stop DJConnect client, local API, maintenance and watchdog services at the
  start of an unattended updater run after a newer release is detected, while
  keeping `djconnect-updater.service` alive.
- Make updater dependency installation resumable per package with
  `.install-state/` markers for venv creation, pip, build tools, PySide6,
  requests, zeroconf and the bundled wheel.
- Make manual `scripts/install.sh` dependency installation resumable with the
  same per-package markers so reboot/interruption retries continue instead of
  rebuilding the release venv from scratch.
- Expanded security/contact guidance in `SECURITY.md` and added
  AI-assisted-development guidance to `CONTRIBUTING.md`.

## 3.1.74

- Added `CONTRIBUTING.md` with MIT licensing, development, release and
  cross-repository contribution guidance for the Raspberry Pi client.
- Stop the running touch UI service and any lingering client process early in
  `scripts/install.sh`, before dependency checks and release installation work.
- Added installer contract coverage for the early touch UI shutdown behavior.
- Added `CHAT_BOOTSTRAP.md` as a local handoff prompt for fresh Codex chats.

## 3.1.73

- Changed the project license metadata and release bundles to MIT.
- Added a separate `djconnect-nightly-reboot.timer` for nightly Raspberry Pi
  reboots at 04:30, installed by bootstrap and refreshed by the app installer.
- Removed the splash replay when the screen wakes from the blanked state; wake
  now returns directly to the kiosk UI.
- Return to Speelt nu whenever the user taps the screen after screen blanking.
- Removed remaining user-facing local API address wording in favor of
  `Client adres`.
- Avoid GitHub API rate limits for stable Pi updates by publishing and reading a
  public `djconnect-pi-latest.json` release manifest from the public release
  assets.
- Refresh installer sudoers from the app installer as well as the OS bootstrap
  so future `sudo -n ./scripts/install.sh` deploys can run from the standard
  Pi install directories after one manual sudo install.

## 3.1.71

- Align Raspberry Pi queue-row playback with the Apple app and HA/HACS
  contract by sending `command:"play_context_at"` with a nested `value.uri`
  payload. `context_uri` is optional, and `offset_uri` is only included for
  playlist, album and show contexts.
- Keep queue rows with direct Spotify track or episode URIs selectable even
  when Home Assistant does not provide `queue_context` or `context_uri`.
- Removed the play/pause quick-action overlay from the Speelt nu album art so
  the artwork stays unobstructed.
- Reduced Raspberry Pi memory pressure by lowering the Qt pixmap cache,
  decoding album/media artwork at display size, disabling extra QML image cache
  retention for dynamic artwork, using one UI worker and clearing log text from
  memory when the Logs screen closes.

## 3.1.70

- Fixed Raspberry Pi queue/playlist item taps by sending compact JSON payloads
  from QML instead of passing QML model references into Python.
- Reduced Raspberry Pi UI load by limiting media-list artwork caching to the
  first visible batch and skipping duplicate artwork cache workers.

## 3.1.69

- Allow Raspberry Pi queue items with a direct Spotify track or episode URI to
  start without requiring `queue_context`/`context_uri`, while preserving
  context plus offset behavior for playlist, album and show contexts.
- Expanded the local-only touch and web games with Maze Chase power pellets,
  Sky Dash/Meteor Run background and explosion effects, Paddle Rally bounce
  feedback, compact controls and short 8-bit sound effects.
- Simplified the touch Settings screen by moving Device ID and Home Assistant
  URL out of Settings, placing update checks below Logs, removing the Now
  Playing status footer and giving album art more screen space.
- Lazily load QtMultimedia for local game sound effects so headless test
  runners without PulseAudio libraries can still import the client backend.

## 3.1.67

- Wake the touch UI to Now Playing at full brightness when Home Assistant
  reports a new track, so the wall display briefly shows the changed music.
- Show Home Assistant DJ text responses as a centered DJConnect overlay for 20
  seconds instead of a small toast, without adding local response audio.
- Added a large play/pause quick action over the Now Playing artwork while
  keeping the dedicated Bediening screen as the full control surface.

## 3.1.66

- Fixed touch and web language refresh so changed settings immediately refresh
  translated labels instead of leaving stale Dutch copy on English screens.
- Fixed touch and web manual refresh so output-device selection is refreshed
  from the current Home Assistant playback state, while recent user output
  selections stay visible briefly until HA confirms them.
- Made queue and playlist rows fully tappable/clickable on touch and web, and
  send complete media-item payloads (`value`, `uri`, `context_uri`) so queue
  item playback and playlist starts use the same client route.
- Added touch-friendly volume step buttons around the volume slider and kept
  the slider for fine adjustment.
- Enlarged the Now Playing album art and rendered title/artist as a shadowed
  overlay inside the artwork for better use of the HyperPixel screen.

## 3.1.64

- Restyled touch and web notification toasts as DJConnect macOS-style rounded
  orange-to-magenta gradient capsules with a play icon, brighter white text and
  glow treatment.
- Removed the explicit web portal "Instellingen opslaan" button. Language,
  log level, screen brightness and screen-blank timeout now save immediately
  when changed, matching the touch UI's save-on-change behavior.
- Changed the reboot action to warning styling on both the touch UI and web
  portal, while keeping reset pairing and shutdown as destructive red actions.
- Tightened the installer-created sudoers rule to only absolute `systemctl`
  paths and validate the generated file with `visudo -cf`, covering reboot,
  shutdown and manual updater starts without interactive authentication.
- Added GitHub Actions concurrency so a newer publish workflow run cancels an
  older in-progress run on the same ref.
- Improved touch UI polish around shuffle/repeat icon rendering, bottom status
  placement, Settings dropdown readability and tap-to-wake activity handling.
- Improved the web portal refresh/log interactions with busy states, bottom
  log scrolling, clipboard copy feedback and a local "Geen" output-device
  option that avoids selecting the first HA output implicitly.

## 3.1.63

- Removed repo-local syncprompt and roadmap copies: this Raspberry Pi repo now
  refers to canonical `pcvantol/djconnect/SYNC_PROMPTS.md` and
  `pcvantol/djconnect/PRODUCT_ROADMAP.md`.
- Added shared `examples/voice_intents.json` for website/docs alignment with the
  HA/ESP post-STT intent examples, without enabling Raspberry Pi voice capture.
- Added contract coverage that successful `status`, `queue`, `devices` and
  `playlists` command responses with empty playback are valid transport
  responses, not backend errors.
- Added explicit playlist parser coverage for `data.items`, alias fields and
  the 100-item local maximum.
- Synced the Raspberry Pi client contract with HA v3.1.37: unpaired mDNS TXT
  now includes pairing metadata, status payloads include `app_version` and the
  Pi language, pairing rejects mismatched identity, and Pi playlist browsing
  requests up to 100 items.

## 3.1.62

- Send `command:"playlists"` with `limit:50` from the Raspberry Pi touch UI and
  web portal, matching the fixed iOS/macOS client contract and avoiding Spotify
  invalid-limit failures.
- Kept queue browsing on `command:"queue"` with `limit:100` and added
  regression coverage for both media-list limits.
- Updated the shared playback contract docs so Home Assistant defaults missing
  playlist limits to 50, clamps playlist limits to the Spotify-safe maximum 50
  and keeps queue limits up to 100.
- Stopped upgrading pip on every install/update by default; set
  `DJCONNECT_UPGRADE_PIP=1` only when a pip self-upgrade is explicitly needed.

## 3.1.61

- Minified the built-in Raspberry Pi web portal HTML response while keeping the
  source template readable for maintenance.

## 3.1.60

- Hardened the Home Assistant playback command integration against the current
  shared contract for `status`, `devices`, `queue` and `playlists`.
- Added playlist parsing for `playlists`, `items`, `data.*` and `result.*`
  response shapes, including extra title, URI, owner and artwork aliases.
- Treat empty HTTP 2xx playback command bodies as explicit contract errors
  instead of silently accepting `{}`.
- Keep backend-unavailable responses separate from stale pairing/auth failures:
  HTTP 401/403/404 now maps to authentication state, while HTTP 200
  `success:false`/`backend_available:false` stays a playback backend issue.
- Added regression coverage for no-active-playback status snapshots, nested
  playlist shapes, queue limits, output aliases and empty response bodies.

## 3.1.59

- Removed the extra white top indicator from the selected bottom navigation
  button; the purple gradient and selected border now carry the active state.
- Fixed output-device selection so refreshes no longer fall back to the first
  available output device when Home Assistant omits the active device field.
- Aligned the web portal with the touch UI by loading output devices through
  the `devices` command when the `status` response omits them.
- Added regression coverage for output-device preservation and web portal
  output-device loading.

## 3.1.58

- Added Raspberry Pi-specific local Client API power endpoints for Home
  Assistant button entities:
  `POST /api/device/restart` and `POST /api/device/shutdown`.
- Fixed deployed Pi debug screenshots by capturing the QML `Window.contentItem`
  instead of calling `grabToImage` on the `Window` object.
- Kept the endpoints on the existing authenticated `/api/device/*` contract:
  bearer token is required and `X-DJConnect-Device-ID` is validated when
  supplied.
- The new endpoints return JSON before scheduling the underlying restart or
  shutdown action, so Home Assistant receives a stable response before the Pi
  stops or restarts.
- Updated the Postman collection and API tests for the new restart/shutdown
  endpoint contract.

## 3.1.56

- Added a touch Settings and web portal "Controleer op updates" action that
  starts `djconnect-updater.service` on demand.
- Added a touch Settings and web portal shutdown action with confirmation on
  the Pi.
- Extended the installer-created narrow sudoers rule so the `djconnect` runtime
  user can run only the required power/update service actions: reboot, poweroff
  and `systemctl start djconnect-updater.service`.
- Improved reboot/shutdown/update action diagnostics by logging stdout/stderr
  from failed systemctl calls instead of only reporting exit code 1.
- Fixed queue and playlist row taps to send `start_queue_item` and
  `start_playlist` commands instead of generic `play_uri`.
- Added a local-only "Geen" output-device option so the Pi no longer
  implicitly selects the first Home Assistant output device.
- Restyled the on-device volume slider with a purple left-to-right track.
- Removed the inactive slash overlay from shuffle and repeat buttons.
- Moved the log-file path from Instellingen to the bottom of Logs and wrapped
  long log lines inside the Logs UI.
- Made the Speelt nu artist font larger.
- Changed web portal Diagnostics so Home Assistant API unavailability is shown
  as failed instead of stopped, because Home Assistant is not a Pi systemd unit.

## 3.1.55

- Added a live Diagnostics section to the Raspberry Pi web portal. It shows
  Home Assistant API, local Client API, pairing state and DJConnect systemd
  service/timer health as running, stopped, failed or unknown.
- Restyled the web portal playback buttons toward the ESP web interface:
  large purple icon buttons, active shuffle/repeat states and a visible volume
  percentage.
- Capped user volume control at 60, where the UI displays 60 as 100%.
- Changed the screen timeout setting from a free SpinBox to a fixed dropdown:
  30, 60, 90, 120, 180, 240, 300 and 600 seconds.
- Fixed queue/playlist rows to prevent horizontal scrolling and keep album art,
  text and play buttons in their proper columns.
- Kept output-device selection on the chosen device when HA accepts the target
  device but does not echo it back as the active output immediately.
- Updated Over so the connection label says Home Assistant and the Music state
  is green when connected and red when not connected.
- Broadened the installer-created reboot sudoers rule to match the systemctl
  variants used by the touch UI.
- Added backend and web portal tests for diagnostics rendering and systemd
  status normalization.
- Clarified that the web portal is served by `djconnect-api.service`, so it is
  installed and started automatically with normal install/update flows.

## 3.1.54

- Split playback controls out of Speelt nu into a new touch-friendly
  Bediening screen next to Speelt nu in the bottom navigation.
- Speelt nu is now a display-focused screen with status, refresh and larger
  album art/title content; tapping the cover opens Bediening instead of sending
  playback commands.
- Bediening uses the standard opaque DJConnect gradient and enlarged previous,
  play/pause, next, progress, volume, output-device, shuffle and repeat
  controls for the HyperPixel touch display.
- Removed the remaining hidden album-art swipe playback actions from Speelt nu.
- Kept the Logs screen action layout to one row with Logs wissen, Verversen
  and Sluiten, and no on-device Logs kopieren action.

## 3.1.53

- Trigger `djconnect-updater.service` on every touch-client boot/start through
  systemd ordering, so the Pi checks for a newer public release before the UI
  starts.
- Made the pairing and pairing-success screens fully opaque instead of
  translucent overlays.
- Suppressed Home Assistant auth/backend toast noise while the Pi is waiting
  for pairing; auth failures still show a red status/toast once paired.

## 3.1.52

- Fixed release cleanup so the public Raspberry Pi distribution repo is still
  cleaned when the private source repo already has only the latest release/tag.

## 3.1.51

- Updated the shared sync prompt bundle in the Raspberry Pi client repo for the
  current cross-repo release checklist and contract notes.

## 3.1.50

- Fixed the local Client API auth test setup so CI starts the API with the
  device token already persisted, matching the runtime config reload behavior
  used by the API/mDNS startup path.

## 3.1.49

- Changed mDNS discovery behavior so the Pi advertises `_djconnect._tcp` only
  while it is unpaired. The local Client API keeps running after pairing for HA
  commands, screenshots and text DJ responses, but already paired devices no
  longer appear as pairing candidates.
- Pairing through the local Client API now stops the mDNS advertisement
  immediately; forgetting/resetting pairing allows discovery to return.
- Fixed the Client API daemon forget path so it clears the stored device token,
  marks the client unpaired and rotates the pairing code before rediscovery.
- Added shared `PRODUCT_ROADMAP.md` with feature ideas, killer features,
  production must-haves and premium-function candidates. This local-copy model
  was later superseded by the canonical `pcvantol/djconnect/PRODUCT_ROADMAP.md`
  policy.
- Extended the repo-only Raspberry Pi OS bootstrap with boot-time filesystem
  repair configuration for wall-mounted devices that may lose power: it keeps
  `fsck.repair=yes` enabled, removes `fsck.mode=skip`, sets the root fstab
  check pass and configures periodic ext filesystem checks.
- Added explicit NTP time synchronization to the repo-only bootstrap with
  `timedatectl set-ntp true` and `systemd-timesyncd.service` enable/start when
  available.
- Added tests for paired mDNS suppression and rediscovery after reset.

## 3.1.48

- Added explicit Home Assistant backend-unavailable handling so
  `success:false` + `backend_available:false` responses become a short user
  status instead of a hanging or incomplete UI.
- Added 401 authentication handling for Home Assistant responses: the raw JSON
  body is no longer shown on screen, the user sees a concise toast/status, and
  the status dot turns red while the backend connection is unhealthy.
- Added live output-device validation and rollback. A selected output device is
  accepted only after HA returns it as active/available; rejected selections are
  restored and logged.
- Capped the on-device Logs screen to a bounded tail read before formatting so
  large persistent log files cannot stall the touch UI.
- Added performance timing logs around HA HTTP calls, refreshes, playback
  commands, queue loads, playlist loads and artwork caching.
- Queue and playlist rows are emitted immediately after the HA response; album
  art is cached asynchronously afterward so slow image downloads no longer block
  list rendering.
- Fixed the touch reboot action to use the installer-created passwordless
  absolute `systemctl reboot` sudoers rule first.
- Reused the same DJConnect purple/blue app gradient across Speelt nu,
  Wachtrij, Afspeellijsten, Logs, Instellingen and Over, and expanded Speelt nu
  controls into the unused vertical space above the bottom navigation.
- Increased the status dot size and added tests for authentication errors,
  backend availability state, log tailing, output-device rollback, non-blocking
  playlist rendering and QML background/control sizing.

## 3.1.47

- Fixed a HyperPixel row-rendering regression where Wachtrij/Afspeellijsten
  could show album art but lose the title/subtitle text and play button.
- Media rows now use explicit x/y/width geometry for artwork, text and
  play-button columns, avoiding QML anchor ordering differences on the Pi
  runtime.

## 3.1.46

- Locked the Pi queue request to the shared HA contract limit:
  `command:"queue"` is sent with `limit:100`.
- Added backend contract coverage for the queue limit and fixed the GitHub
  Actions debug-screen test expectation so public release publishing can pass.

## 3.1.45

- Added loopback-only debug automation for deployed Pi screenshots:
  `GET /api/debug/screen?screen=<name>` switches the UI screen through the
  local command-event bridge, and `GET /api/debug/screenshot` may be called
  from `127.0.0.1` without exposing the device bearer token over LAN.
- The screenshot response now includes `content_base64` for SSH-based
  diagnostic capture so release deploy verification can attach actual PNGs.
- Added backend, local API and QML tests for the debug screen/screenshot path.

## 3.1.44

- Fixed Wachtrij/Afspeellijsten media-row rendering by replacing the delegate
  `RowLayout` with explicit anchored artwork, text and fixed-size play button
  positioning.
- Removed the unsupported speaker emoji from Speelt nu and kept the
  output-device selector functional with a fallback HA `devices` command when
  status does not include the device list.
- Made Instellingen, Over and Logs opaque full-screen views instead of
  translucent overlays, and disabled horizontal scrolling in Instellingen and
  Over.
- Changed the Home Assistant URL in Instellingen to a label/value row, made the
  Device ID row consistent, removed the no-voice explanatory text and changed
  the save toast to "Instellingen opgeslagen".
- Added an Apparaat herstarten confirmation dialog and kept the actual reboot
  action behind the existing narrow systemctl sudoers rule.
- Replays the DJConnect splash briefly when the screen wakes from the blanked
  state.
- Aligned the Speelt nu refresh button with the Wachtrij/Afspeellijsten refresh
  buttons and expanded tests for the updated QML and HA device-list behavior.

## 3.1.43

- Added `docs/TECHNICAL_DESIGN_DECISIONS.md` with reverse-engineered design
  patterns, language-specific coding conventions and dependency/license/source
  inventory, and made it part of the release documentation checklist.

## 3.1.42

- Added a local debug screenshot flow for the HyperPixel UI:
  `GET /api/debug/screenshot` asks the QML UI process to capture the live
  scenegraph with `grabToImage` and save it to the configured screenshot path.
- Documented the screenshot endpoint in the local API/Postman docs and added
  API, daemon and QML contract tests for the request/event/capture path.
- Kept the endpoint protected with the device bearer token once the client is
  paired, while still allowing bring-up diagnostics before pairing.
- Fixed a queue/playlist responsiveness regression by moving album-art caching
  into the backend worker path instead of QML row delegates.
- Restored visible cached artwork in Queue and Playlists and replaced the
  malformed row play canvas with a fixed-size media play icon button.
- Made the selected bottom navigation item more obvious with a stronger
  gradient, thicker border and top active indicator.
- Removed the dark lower overlay from the Now Playing album art, replaced the
  separate output-device label with a compact selector row and gave playback
  controls more vertical space.
- Expanded Maze Chase to four vertical rows of white pellets.

## 3.1.41

- Made the bottom navigation bar one-third taller and added simple tab icons
  for touch-friendly kiosk navigation.
- Improved Maze Chase by slowing the ghost, adding a large power pellet and
  making the ghost temporarily edible with a blinking blue/white vulnerable
  state.

## 3.1.40

- Fixed Games screen touch pass-through so empty/transparent game areas no
  longer activate underlying Speelt nu playback controls.
- Moved Games to the right of Afspeellijsten in the bottom navigation bar.
- Kept real HA empty queue/playlist responses empty and show "Geen wachtrij" or
  "Geen afspeellijsten"; demo media is now only loaded when demo mode is
  explicitly active.
- Fixed remaining game-canvas QML mouse-handler warnings by using explicit
  signal parameters.

## 3.1.40

- Keep the touch screen awake for 10 seconds when previous/next track starts,
  including HA initiated previous/next commands received through the local
  Client API command-event bridge.

## 3.1.40

- Routed Home Assistant initiated `/api/device/command` calls from the separate
  local API daemon to the touch UI through a small persisted command-event
  queue, so HA entity actions such as previous/next are actually executed by
  the UI process.
- Added an output-device selector to the Speelt nu screen. It reads device
  lists from HA status/command responses and sends `command:"set_output"` with
  the selected value.
- Added manual refresh buttons to Speelt nu, Wachtrij and Afspeellijsten.
- Made Wachtrij and Afspeellijsten opaque full main screens so Speelt nu no
  longer shows through.
- Changed incoming textual DJ responses to a toast that disappears after 10
  seconds instead of a blocking overlay with a Close button.
- Disabled horizontal scrolling in Over and Instellingen and kept destructive
  reset-pairing buttons visually consistent with the other square Pi buttons.
- Fixed QML modal-handler warnings by using explicit signal parameters.
- Expanded tests for command-event routing, output-device parsing/dispatch,
  DJ-response toast behavior and the updated QML kiosk layout.

## 3.1.40

- Fixed Home Assistant command payloads to always include the stable
  `device_id` and `client_type=raspberry_pi`, resolving HA `invalid_client_type`
  responses during refresh/status commands.
- Fixed stale pairing-code behavior after "Opnieuw koppelen" by making the
  local API daemon reload shared config before info/pairing-info and local
  pairing requests.
- Added a macOS-style confirmation screen for "Opnieuw koppelen" and made the
  settings reset-pairing action red.
- Renamed the settings title to "Instellingen", renamed "Logs bekijken" to
  "Logs" and removed the settings Close button.
- Made full-screen overlays consume touch input so controls on underlying
  screens cannot be tapped through logs, about, pairing, version mismatch or
  confirmation screens.
- Made the touch reboot action fall back to `sudo -n systemctl reboot` and made
  the installer write a narrow sudoers rule for only `systemctl reboot`.
- Updated the About screen to use the full available width and show
  `https://djconnect.dev` in white.
- Extended release cleanup tooling so normal release closeout can also clean
  old public distribution releases/tags with `--public`.
- Updated the touch UI kiosk branding to show `DJConnect` everywhere, use the
  real bundled app icon, remove visible close buttons and ignore stale persisted
  config versions in favor of the runtime package version.
- Tightened the Pi media screens with fixed-size play buttons, compact
  `HH:MM:SS INF/WRN/DBG/ERR` log prefixes, Apple-aligned demo queue/playlist
  samples and HA queue/playlist artwork alias support with a 24-hour local
  image cache.
- Fixed unattended updater installs from public tarballs by stripping the
  top-level bundle directory, installing the bundled wheel into the release
  venv, validating all console entrypoints and only then switching
  `/opt/djconnect/current`.
- Made the unattended updater clean old Pi release directories after a
  successful install, keeping the active release plus one rollback release and
  removing stale temporary unpack directories.
- Made unattended updater dependency installs use the same cache-local pip
  temp directory as the installer, avoiding `/tmp` pressure during large
  PySide6 wheel installs on Raspberry Pi Zero 2 W.
- Initial Raspberry Pi display-remote scaffold with Qt Quick/QML, fullscreen
  720x720 touch UI, playback controls and app-like DJConnect pairing, status
  and command client contract.
- Split the local Client API into `djconnect-pi-api` and
  `djconnect-api.service`; the Qt touch UI no longer hosts the API itself.
- Added full-screen startup splash and blocking first-run pairing screen with
  Client adres and pairing code input.
- Added Home Assistant version compatibility guard. A `3.1.z` Pi client accepts
  HA `>=3.1.0` and `<3.2.0`; mismatches show a blocking screen and trigger
  `djconnect-updater.service`.
- Added local demo mode before pairing and a "Demomodus stoppen" action that
  returns to the blocking pairing flow.
- Added touch-only local games matching the Apple app set: Paddle Rally, Meteor
  Run, Sky Dash and Maze Chase.
- Set default touch screen blanking to 2 minutes with tap-to-wake and a
  configurable timeout in settings.
- Added unattended GitHub release updater, apt maintenance service, systemd
  units, release scripts and bootstrap documentation.
- Added persistent rotating file logging, configurable screen blanking,
  stable/beta update channel selection and expanded tests.
- Added startup Raspberry Pi system-info logging for both UI and API daemon.
- Hardened config writes with private file permissions and atomic replacement.
- Added Client API request size limiting and expanded regression, monkey,
  installer contract and QML tests.
- Switched unattended app updates to the public release repository
  `pcvantol/djconnect-pi-releases` and added a GitHub Actions publish workflow.
- Added complete release bundles with `docs/`, `scripts/`, `src/` and
  `systemd/` so production Pi installs can run from the public release tarball.
- Added modern HyperPixel 4 KMS DPI overlay setup, Raspberry Pi OS Lite 64-bit
  bootstrap with minimal X11/Qt runtime dependencies and installer version
  output.
- Added dark DJConnect blue/purple gradient styling across the touch UI.
- Updated the cross-repo sync prompt with full HA-side Raspberry Pi mDNS
  autodiscovery requirements.
- Documented manual production updates from the public release tarball and made
  the installer restart API/UI services when rerun over an existing install.
- Reviewed Dutch/English translations, moved game titles behind i18n keys and
  fixed the playback fallback so "nothing playing" is translated by the UI.
- Removed Wi-Fi provisioning from the installer; Wi-Fi/hostname/SSH/locale are
  handled by Raspberry Pi Imager before first boot.
- Split general Raspberry Pi OS bootstrap into repo-only
  `scripts/bootstrap_raspberry_pi_os.sh` and excluded it from release tarballs.
  The DJConnect app installer no longer performs timezone, SSH, apt
  full-upgrade, Raspberry Pi Connect, minimal X11/Qt runtime or
  HyperPixel setup.
- Fixed public release install checksum verification so the installer compares
  SHA256 hash values instead of relying on the filename stored in the `.sha256`
  asset.
- Removed third-party system monitoring setup from all bootstrap scripts and
  documentation; monitoring is no longer installed or managed by DJConnect Pi.
- Made the public release installer resumable across reboot, power loss or
  thermal freezes. Release unpack and Python dependency install steps now use
  markers under `/opt/djconnect/install-state/<version>/`, and pip downloads
  are cached under `/var/cache/djconnect-pip`.
- Moved the pip cache outside `/opt/djconnect` so pip can use it while the
  installer runs as root without ownership warnings.
- Added root filesystem expansion to the repo-only Raspberry Pi bootstrap and
  an early free-space check to the release installer so large PySide6 downloads
  fail with a clear recovery message instead of filling the SD card mid-install.
- Added persistent 1GB swapfile setup to the repo-only bootstrap and an early
  active-swap requirement check to the release installer.
- Renamed the public app installer to `scripts/install.sh`, added resource
  snapshots around major install steps, and added prerequisite checks for
  architecture, Python version, writable paths, GitHub release access and
  Raspberry Pi thermal/throttling status.
- Changed public release tarballs to install from a bundled wheel under
  `wheels/` and stop shipping the loose `src/` app source tree.
- Increased the installer free-space requirement to 3GB, added inode reporting,
  cleaned incomplete `.venv` directories before dependency retries, and moved
  pip temporary files under `/var/cache/djconnect-pip/tmp`.
- Hardened installer recovery for partial venv installs by requiring all
  DJConnect console entrypoints before marking dependencies complete.
- Configured `/etc/X11/Xwrapper.config` with `allowed_users=anybody` during
  install so the systemd-managed touch client can start Xorg on Raspberry Pi OS
  Lite.
- Added `needs_root_rights=yes` to the Xwrapper install step so Xorg can open
  `/dev/tty0` when launched by the systemd-managed touch client.
- Changed installer dependency installation to invoke pip through
  `.venv/bin/python -m pip` so a broken generated `pip` wrapper cannot abort
  recovery installs.
- Added a generated six-digit Pi pairing code, exposed it on the blocking
  pairing screen and `/api/device/pairing-info`, and rotate it on pairing reset.
- Refined touch UI controls with transparent rounded purple/blue buttons,
  larger readable logs, copy/clear log actions, scrollable settings, an About
  screen, and queue/playlist screens.
- Fixed the games selector labels by translating each game `titleKey` instead
  of reading a missing `title` field.
- Fixed local Client API request logging so `GET /api/device/pairing-info`
  returns JSON instead of an empty reply, allowing HA mDNS discovery to prefill
  the Pi pairing code.
- Aligned the Pi pairing screen order and labels with the macOS pairing screen,
  removed the logs button from that first-run flow and kept demo mode as the
  only local action.
- Added a Postman collection for the local Pi Client API under `docs/postman/`.
- Added now-playing track progress, font-independent playback icons, larger
  full-width settings controls, logs autoscroll on refresh and richer Maze
  Chase Pac-Man/ghost rendering.
