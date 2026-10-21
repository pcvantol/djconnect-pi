# Apple card materials in the shared Pi app

Design comparison uses pinned Apple UI `e106a467`, especially
`DJConnectRootView.swift` and `NativeSessionMomentsView.swift`. These references
supply presentation, never a new image grant, endpoint or runtime authority.

Apple has distinct roles: ordinary Session frosted surfaces, framed artwork
(with an eight-point inset), and hero cards with a three-colour gradient and
outline. Its hero modifier is not itself a native glass modifier. The Pi keeps
those roles distinct; the shared Glass toggle controls actual glass surfaces.
Hero gradient colours are centralized in `GlassStyle.qml`.

| Apple role / page | Shared Pi presentation | Status in source |
| --- | --- | --- |
| Session welcome hero | `SessionStartCard`, hero `GlassCard` | Dedicated hero gradient and outline |
| Session Moment/retained/reply/history cards | Existing `GlassCard` / `GlassSurface` | Existing shared material retained |
| Admitted current Moment image | `sessionMomentArtworkFrame` | Eight-pixel bounded inset inside original footprint; full image fit |
| Current Forecast artist image | `sessionForecastArtworkFrame` | Shared artwork frame; original artist/source attribution retained |
| Track Insight hero and artwork | Main header / `trackInsightArtworkFrame` | Hero gradient, framed existing image |
| Track Insight empty hero | `trackInsightEmptyHero` | Hero treatment for original empty-state copy |
| Track Insight visualizer, metrics, sections | Existing Main content cards | Shared material, original Mood focus borders retained |
| Discover consent, disabled-profile hero, result cards | Existing Main cards | Shared material / dedicated hero role |
| Discover artwork | `discoveryArtworkFrame` | Framed original image, same source/loading policy |
| Music DNA active/inactive heroes | `musicDnaSummaryHero`, `musicDnaOptInHero` | Grouped existing content/actions; bounded intrinsic height |
| Music DNA sections | Existing Main section cards | Shared material |
| Ask DJ contributions, inline analysis and media/action cards | Existing Main content cards | Shared material; user contribution tint remains distinct |
| About, Privacy, Legal, Feedback | Existing `GlassCard` sections | Already shared material; retained |
| Session pop-outs | Shared `GlassPopup` / `GlassSurface` | Visual entry only; Popup lifecycle and original close handlers stay immediate |

The plain `AnimatedAlbumArtworkView` reference explicitly disables its generic
album glass frame. No blanket replacement of every Pi image or decorative
rectangle is made. Existing Main Now Playing cover geometry remains unchanged.
This comparison does not add the still-missing full Session current-cover loader
or its display rights. Tiny legacy media-row thumbnails and remaining Apple-only
page composition are not declared complete.

Artwork frames never fetch an image. A bounded 32x32 readback of the already
displayed Image supplies an optional material tint. Callers retain all existing
URL/source/attribution/visibility/expiry/cache bindings. The shared GPU material
continues sampling only its decorative underlay. Protected image fit is retained;
frame inset is bounded by a quarter of either dimension so narrow/wide admitted
images never get negative content geometry. No implicit cache or image retention
is introduced. Confirmed Mood and current displayed-artwork material tinting are implemented
in source; see `PI_MOOD_ARTWORK_COLOURS.md`. Remaining gaps include exact native Apple rendering,
full hero scene animation and physical performance/acceptance.
