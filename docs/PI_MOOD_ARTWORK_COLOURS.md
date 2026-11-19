# Mood and displayed-artwork colours

Shared presentation uses confirmed active Session Mood first, then available
confirmed settings3 Mood, otherwise the brand palette. The four three-stop Mood
palettes match pinned Apple UI e106a467. Decorative backgrounds, hero surfaces
and Glass materials follow these colours. Semantic primary/selected/destructive
and status roles retain their existing meanings.

Artwork colour is an alpha-weighted RGB average of a single 32x32 Qt readback
of the caller's already displayed Image, excluding transparent letterboxing.
It is a bounded colour approximation, not Apple's proprietary material renderer
or an exact copy of its palette extraction. It never fetches, decodes, caches or
retains a new image. One live readback per QML engine is shared across samplers;
there is no queued image/body cache, retry loop or new worker pool.

Now Playing, Track Insight and Discover use their existing displayed images.
Session uses only its already admitted current Moment or Forecast image. No
playback metadata is promoted into a new cover/display grant. Historical images,
missing full Session cover composition and other absent image loaders stay open.
Original sources, attribution, fit, loading, expiry and visibility rules remain.

Every sample binds its original image, source generation and presentation lease.
Source/lease changes, hidden or idle UI and admission withdrawal clear stored
colour immediately. A late callback checks the current original admission both
before and after the pure pixel sampler. Moment/Forecast about-to-change signals
invalidate colour before projection replacement. Returning to a view samples
fresh pixels rather than restoring an old colour or deadline.

`GlassStyle.qml` centralizes moodTintStrength (0.12), artworkTintStrength (0.16),
heroMoodStrength (0.18), and the material channel ceiling (0.24). Strengths can
be adjusted centrally. The shared Glass toggle and Pi profile defaults remain;
simpler materials also use bounded tint. This adds no setting or server write.

Qualification is recorded in TESTS.md and the parity checkpoint. The new source
has not been installed. Protected source/review, separate Finalization, a distinct
immutable release and new approved rc.6 operative bindings remain necessary.
