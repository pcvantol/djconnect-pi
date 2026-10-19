from __future__ import annotations

import json
import subprocess
from importlib.resources import files

from djconnect_pi.brand_theme import colors, css_color
from djconnect_pi.web_portal import index_html


def luminance(color):
    values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(v * weight for v, weight in zip(values, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    bright, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def test_brand_text_and_actions_meet_readability_contrast():
    theme = colors()
    for surface in ("background", "surface", "surfaceRaised", "surfacePressed"):
        for foreground in ("text", "muted", "cyan", "warning", "danger", "success"):
            assert contrast(theme[foreground], theme[surface]) >= 4.5, (foreground, surface)
    for surface in ("buttonStart", "buttonMid", "buttonEnd", "dangerSurface", "warningSurface"):
        assert contrast(theme["text"], theme[surface]) >= 4.5, surface
    assert contrast(theme["focus"], theme["surface"]) >= 3


def test_mood_only_colours_explicit_choice_not_app_navigation():
    source = files("djconnect_pi.qml").joinpath("MoodTheme.js").read_text()
    brand = files("djconnect_pi.qml").joinpath("BrandTheme.js").read_text()
    program = "\n".join(line for line in brand.splitlines() if not line.startswith("."))
    program += "\nvar BrandTheme = {colors: colors};\n"
    program += "\n".join(line for line in source.splitlines() if not line.startswith("."))
    program += "\nconsole.log(JSON.stringify([0,35,70,100].map(v => [color(v,'backgroundStart'),color(v,'gradientStart'),moodColor(v,'gradientStart')])));"
    result = subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True)
    rows = json.loads(result.stdout)
    assert len({row[0] for row in rows}) == 1
    assert len({row[1] for row in rows}) == 1
    assert len({row[2] for row in rows}) == 4
    html = index_html("fixture").decode()
    assert "MOOD_THEMES" not in html
    assert f"--brand-background:{colors()['background']}" in html


def test_translucent_qml_colors_are_converted_for_css():
    assert css_color("#D918203B") == "#18203BD9"
    assert css_color("#00000000") == "#00000000"
    assert css_color("#080B1A") == "#080B1A"
    assert f"--brand-glass:{css_color(colors()['glass'])}" in index_html("fixture").decode()
