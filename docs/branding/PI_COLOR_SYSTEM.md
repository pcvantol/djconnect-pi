# Pi Brand V2 colour application

`src/djconnect_pi/qml/BrandTheme.js` is the single colour source for the Pi
presentation. Its JSON token object is consumed directly by QML, by the Python
Qt palette and by the embedded portal's CSS variables. `BrandWindow` supplies an
explicit Basic-control palette so dropdowns, popup delegates and disabled controls
inherit dark surfaces instead of the platform's light defaults.

This is a Pi consumer palette complementing the delivered Core cyan/blue/purple
glass-headset artwork, not a claim that Core published these UI token values.
The exact approved Core images, original RGB values, alpha silhouette and receipt
remain unchanged. The colour foundation itself does not change identity, pairing
or shared settings persistence. The accompanying shared Session/UI work is tracked
separately in the experience comparison below; this document does not qualify it.

Backgrounds and app chrome remain stable across Mood changes. The existing Mood
thresholds and identity colours remain in the explicit Mood selection; they no
longer recolour navigation or error/success semantics. Game terrain/objects and
server-supplied artwork/visualizer colours retain their semantic meaning. Neutral
specular highlights, scrims and the screen-blanking black remain intentional.

Primary text, secondary text and status colours meet 4.5:1 against opaque app
surfaces; primary button text meets 4.5:1 at all gradient stops. Focus boundaries
meet 3:1 against app surfaces. Translucent ambient fields still require rendered
visual inspection. The native preview tool covers real pages at 720x720 and
1200x1920; the existing settings preview covers five locales and four shared
settings states. These are fixture proofs, not physical-display acceptance.

Reproduce:

```sh
PYTHONPATH=src QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software python Tools/preview_brand_colors.py --output /tmp/pi-brand-pages
PYTHONPATH=src QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software python Tools/preview_shared_settings_brand.py --output /tmp/pi-brand-settings
PYTHONPATH=src QT_QPA_PLATFORM=offscreen python -m pytest
```

Full Apple experience parity is tracked separately in
[the implementation comparison](../PI10_APPLE_EXPERIENCE_PARITY.md).
