# Pi shared settings and Brand V2 consumer candidate

Owning work: [Pi settings #104](https://github.com/pcvantol/djconnect-pi/issues/104)
and [Pi Brand V2 #108](https://github.com/pcvantol/djconnect-pi/issues/108).
This is consumer source work, not release, installed-HA, audible, physical Pi or
joint cross-client acceptance.

## Shared settings3

The native Settings screen edits Persona, provider Voice, Gender, symbolic Mood,
DJ Presence and Announcement Output through the existing Core settings3 owner.
With a Session, explicit changes affect its captured revision and Profile defaults;
without a Session they affect defaults only and never start music. Reads are pure.
The Pi remains without microphone upload, PTT, TTS or local DJ audio. All four
shared output intents can be selected for linked clients; this Pi itself never
claims to render speech. Unavailable saved voices/output intents remain intact.

GET uses only version3 and the paired device identity. PATCH captures the binding,
defaults revision and Session identity/generation/revision from the original read.
An opaque RAM draft token prevents applying a stale editor to a successor Session.
Profile/token/host changes discard the visible projection and delayed results.
All six choices require explicit confirmation for the first migration or unknown
legacy Session Mood. A partial edit sends only explicitly changed fields, so an
automatic Session Mood is not silently copied to Profile defaults.

A fresh GET confirms every accepted operation. A lost PATCH response triggers only
pure operation receipt reads; PATCH is never automatically resent. Live absence
keeps the operation pending and blocks another write. Expired absence is shown as
uncertain, followed by a fresh owner read. Operation identity, binding, revisions,
voice identifiers and preferences remain in RAM, outside config, screenshots of
protocol diagnostics, logs, API discovery and persistent caches. Restart performs
a fresh read, never replays an operation and never reconstructs Profile defaults.

### Legacy disposition

| Existing Pi surface | Disposition |
| --- | --- |
| Numeric Mood quick selector | REPLACE: on a paired Pi, send a symbolic shared settings patch; retain the local visual selector for unpaired/demo use only. |
| Numeric Mood in HA bodies/headers | REMOVE for paired Pi requests, including before the first owner response. |
| Local DJ announcement output selector | REPLACE: the shared editor owns this intent; hide the old paired selector. |
| Legacy Ask DJ announcement output hints | REMOVE for paired Pi requests, including startup; no fallback write on unavailable/older owner. |
| Local portal legacy output setter | REMOVE for paired Pi: return a translated upgrade requirement without saving any settings. |
| Old config mood/output keys | RETAIN historical bytes pending qualified platform migration/removal; never import them as shared defaults or forward them on a paired Pi. No pairing/history/DNA deletion. |
| Local volume, music output, brightness, timeout, language, autoplay and maintenance | KEEP device-owned; unchanged by shared settings patches. |
| Local Persona/Voice/Gender/Presence storage | NONE introduced. |

The fixtures in `tests/fixtures/shared_settings` are extracted byte-preserving
objects from protected Core delivery `e8cc70ddffb4112b09babdda4d45140b98926ae5`.
Their provenance file records the complete fixture hash. Fixture checks are not a
substitute for connected HA migration/export/import/restart or joint acceptance.

## Brand V2

`docs/branding/pi-import.json` pins the exact producer commit, artifact archive and
manifest hashes, plus every imported output. The downloaded archive and all
selected PNG hashes were verified before copying. `core-manifest.json`, the Inter
OFL license and font provenance are retained alongside the receipt.

At this consumer checkpoint Core PR1224 at
`883cb9f3ff9de8ec7f5ae4c5f04f852e0d8bd866` is an **open candidate**. Its technical
checks succeeded but Owner Authorization has not passed. The Pi import is a
review candidate and must not be merged/rolled out as an accepted brand until the
protected producer pin is delivered and this receipt is reconciled. A replacement
producer SHA requires a new exact hash readback, not an implicit main-branch pull.

| Surface | Consumer mapping |
| --- | --- |
| Qt native window icons | Exact headset-only 16/20/24/32/40px; glass 64/128/512px. |
| QML startup, pairing, About and announcement banners | Shared `BrandLockup` component, exact compact/primary PNGs according to available width; translated tagline or existing contextual detail below. |
| Local web portal | Embedded local compact dark wordmark on narrow screens, primary dark at >=512px available width, exact 32px headset favicon. No remote image dependency. |
| Light surface | Exact light variants retained and supported by the QML component. |
| Launcher/OS desktop entry | No standalone desktop launcher/icon installation exists in this repository; no OS configuration is added. |
| Persona avatars, vinyl/music glyphs, reactions and artwork | Existing semantic artwork remains. |

The glass rim retains its canonical alpha silhouette and dark interior. No local
redrawing, background-removal recipe or opaque rectangle is substituted. PNG
wordmark typography is supplied outlined/rasterized by Core, with licensed Inter
provenance. The English primary tagline remains exactly `Your music. Your DJ.`;
the separate native tagline has keys in all five locales.

## Reproduce local qualification

Use the exact project lock in an isolated environment, then:

```sh
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -m pytest -q
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python Tools/preview_shared_settings_brand.py --output /tmp/pi-settings-brand-preview
```

The native preview loads the actual shared QML editor and lockup, checks six
controls for empty, active, migration-required and unavailable-voice snapshots in all
five locales at720x720 and1200x1920 (40 fixture views), and rejects QML errors.
Its screenshots include native-size micro marks and scroll access to lower fields.
This is macOS Qt fixture proof only. Protected CI, actual HA acceptance, Pi ARM
packaging, installed screenshots, physical touch/font/legibility and cross-client
acceptance remain separate gates. No Pi service, URL, install or release is changed.
