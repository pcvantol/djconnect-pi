# Raspberry Pi Profile Adoption Report

Epic 3B Phase 4 scope: Raspberry Pi Ambient Client profile adoption.

## Shared UX Philosophy

The Raspberry Pi is a shared household screen first. Its default mental model
is Room -> Household -> Shared DJ, not a second Apple-style personal client.

The Pi sends canonical Profile Platform request context and lets Home Assistant
resolve the DJConnect Profile. It never infers a person from touch usage,
playback state, Home Assistant user hints or recent activity. Personal profile
state appears only when the backend resolves the paired device or explicit
selection to a personal profile.

## Household And Shared Behavior

Household, room, guest, kids and party profiles are treated as safe shared
contexts. The Pi may show:

- Now Playing and playback controls;
- shared Ask DJ read-only history and backend-provided structured actions;
- shared/household Music DNA;
- shared/household Discover recommendations;
- Track Insight for the current playback context;
- device diagnostics, pairing and update state.

Discover defaults to shared recommendations. Music DNA defaults to the resolved
shared profile's Music DNA. Ask DJ defaults to shared history only.

## Personal Behavior

Personal profile behavior is explicit. The Pi supports it by sending optional
`profile_id` and `private_session` fields when configured, and by honoring
backend `resolved_profile` metadata.

When the resolved profile type is `personal`, the Pi renders personal Music DNA,
personal Discover and personal Ask DJ history returned by Home Assistant. The
Pi still does not own personal state, does not compute Music DNA, does not
persist recommendations locally and does not create a local resolver.

## Privacy Decisions

Profile-scoped UI caches are isolated. On profile change, the backend clears:

- Ask DJ messages and revision cursors;
- Music DNA summary and sections;
- Discover items, empty/error text, feedback and playing state;
- Track Insight analysis for the previous context.

Playback, pairing, local settings and diagnostics remain device-owned.

Living-room safety rules:

- Personal Ask DJ history is hidden unless a personal profile is explicitly
  resolved.
- Personal recommendations are hidden unless a personal profile is explicitly
  resolved.
- Household/shared recommendations are visible.
- Guest-safe profile data is rendered as shared and must not expose personal
  Music DNA.
- Private Session request context is sent to the backend; persistence policy
  remains backend-owned.

## Canonical Contract Adoption

The Pi now consumes canonical profile contract fixtures:

- `profile_context.requests.json`;
- `profile_context.responses.json`;
- `profile_context.errors.json`;
- `capabilities.websocket.json` with Profile Platform capabilities and
  `profile_context` contract version.

Profile-aware requests carry `device_id`, `client_type:"raspberry_pi"`,
`request_source`, and optional explicit `profile_id`/`private_session`.
WebSocket capability parsing stores advertised `capabilities` and
`contract_versions` instead of version guessing.

Canonical profile errors are treated as profile/setup failures, not stale
pairing failures. Pairing is kept for errors such as `device_not_mapped`,
`profile_required`, `invalid_profile` and account/backend profile errors.

## Known Tradeoffs

- No profile selector UI was added in this phase. The Pi can carry explicit
  profile context through config, but household/default resolution remains the
  expected path.
- Profile CRUD, household management, export/import and cloud behavior remain
  out of scope.
- The UI does not yet visually label every screen with active profile metadata;
  cache isolation and contract correctness were prioritized.
- Existing Music DNA enable/clear controls remain available through the Pi, but
  the backend owns the scoped profile state and policy.

## Recommendations For ESP32 Adoption

ESP32 should stay a Voice / Control Client.

Recommended adoption path:

- send `device_id`, `client_type:"esp32"` and `request_source:"voice"` or
  `request_source:"device_command"`;
- let Home Assistant resolve profile from device, room or fallback mapping;
- do not add Music DNA UI, Discover UI or Ask DJ history;
- do not infer personal identity from voice use unless a future canonical
  speaker identity hint exists;
- respect private-session/profile privacy flags returned by the backend;
- isolate any short-lived response/audio cache by resolved profile or session.

ESP32 should not implement profile switching or personal-history rendering in
the current platform model.
