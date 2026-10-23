# Pi10 native VibeScape — local candidate

The sole Pi worktree implements a renderer-local VibeScape visit for the
`pi5-arm64` profile only. It opens above the mounted Session/Flow navigation
from an explicit tap during a paired, owner-resolved active Session. The compact
Pi has neither an entry nor a renderer instance. Exit, background, navigation,
Session/Profile replacement, pairing loss and ending withdraw the visit; a
return to an earlier context does not reopen it. No scene/touch/seed/dynamics
state is persisted. Normal screen brightness still applies. The visit temporarily
holds logical idle blanking and automatic return-to-now, restoring their normal
timers on exit without changing configuration.

The procedural field is a native GLSL/Qt RHI port of
`pcvantol/djconnect-app@3c223b9acaf47f1dfe1890d44703abf8242256e4`:
`Sources/DJConnectUI/VibeScapeShaders/VibeScape.metal` and `VibeScapeScene.swift`.
It uses the same four Mood palettes, bounded local composition and liquid field,
local dynamics and up to four soft touch impulses. It has a 480x768 pixel budget,
smooth upscaling and a 33ms animation timer. These are Pi resource choices, not
claims of achieved hardware frame rate. Reduced motion freezes animation and
withdraws touch impulses. No accepted numeric track-intensity basis is available,
so no beat, audio or fabricated Track Insight intensity drives this rendering.

OpenGL RHI is required; the Qt software scenegraph and shader failure show an
honest unavailable state. VM OpenGL uses llvmpipe: exercising the native shader
path there does not prove hardware GPU acceleration or Pi5 performance. Actual
Pi5 V3D/GLES, thermal/load/memory, installed display and touch acceptance remain
open until the distinct qualified delivery and owning hardware checks.

This is a local visual renderer, not adoption of the iOS/macOS visual-director
speech routes. There is no microphone/STT/upload, general Ask DJ fallback,
provider/model call, playback command, scene transcript, Core scene persistence,
or visual directive applied-acknowledgement. New Core/Apple push/background WIP
is not a Pi authority. Flow/Forecast remain mounted; Forecast return is shown
only when that existing capability is admitted.

## Separate content-deletion consumer foundation

The same local WIP also adds identifier-only `ContentPreview`/`ContentIntent`
and closed isolated prepare/delete/status transport, using protected Core
Source58561f97 + separate Finalb4bf4701. Original five-minute confirmation,
UUIDv7 lifetime/skew, owner/scope/digest equality, one atomic send claim and
read-only original-operation status are explicit. Receipt fields are not confused
with prepare-only affected_moments/fenced_request_count. No Profile/private body
hint or automatic write retry is added. **This foundation is not connected to a
button, worker or display invalidation and is not delivered individual erasure.**
The complete visible-target preview/confirm UI, End-free worker, withdrawal and
late-read/media invalidation are still required before enabling that feature.

## Qualification and delivery boundary

All current work is a local candidate above fa1d07b. Initial host retention
DRIFT blocked delivery. A fresh native actual-root verification subsequently
returned MATCH (`/private/tmp/pi-vibescape-before-delivery-hostverify.log`), which
is readiness only. No independent review GO, release, deployment, live VM pairing
or physical Pi result follows from the local implementation. Exact VM snapshots,
source manifests, successful and failed runs and review package are retained at
`/Volumes/Shared Data/tmp/pcvantol/pi-unattended-vm/`.
