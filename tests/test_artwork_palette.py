from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtGui import QColor, QImage

from djconnect_pi.app import DJConnectBackend
from djconnect_pi.artwork_palette import displayed_artwork_tint
from djconnect_pi.brand_theme import colors


@pytest.mark.parametrize("color", ["#ff0000", "#00ff00", "#0000ff", "#ffffff", "#000000", "#387caf"])
def test_solid_displayed_pixels(color):
    image = QImage(32, 32, QImage.Format_ARGB32)
    image.fill(QColor(color))
    assert displayed_artwork_tint(image) == color


def test_full_displayed_sample_and_transparent_letterbox():
    image = QImage(4, 1, QImage.Format_ARGB32)
    for x in range(3):
        image.setPixelColor(x, 0, QColor("red"))
    image.setPixelColor(3, 0, QColor("blue"))
    assert displayed_artwork_tint(image) == "#bf0040"
    image = QImage(32, 32, QImage.Format_ARGB32)
    image.fill(QColor(0, 255, 0, 0))
    image.setPixelColor(0, 0, QColor("red"))
    assert displayed_artwork_tint(image) == "#ff0000"


def test_alpha_weight_and_empty_pixels():
    image = QImage(2, 1, QImage.Format_ARGB32)
    image.setPixelColor(0, 0, QColor(255, 0, 0, 128))
    image.setPixelColor(1, 0, QColor(0, 0, 255, 255))
    assert displayed_artwork_tint(image) == "#5500aa"
    image.fill(QColor("transparent"))
    assert displayed_artwork_tint(image) == ""


@pytest.mark.parametrize("size", [(33, 1), (1, 33), (33, 33), (2048, 1), (0, 0)])
def test_rejects_samples_outside_fixed_pixel_budget(size):
    image = QImage(*size, QImage.Format_ARGB32)
    assert displayed_artwork_tint(image) == ""


@pytest.mark.parametrize("value", [None, "file:///private/image.png", "https://fixture.invalid/art", b"pixels", {}, 32])
def test_sampler_accepts_pixels_never_paths_or_urls(value):
    assert displayed_artwork_tint(value) == ""


def test_sampling_does_not_mutate_or_retain_cross_call_pixels():
    image = QImage(32, 32, QImage.Format_ARGB32)
    image.fill(QColor("red"))
    original = image.copy()
    with ThreadPoolExecutor(max_workers=4) as executor:
        assert list(executor.map(displayed_artwork_tint, [image] * 16)) == ["#ff0000"] * 16
    assert image == original
    image.fill(QColor("blue"))
    assert displayed_artwork_tint(image) == "#0000ff"


def _theme(expression):
    brand = files("djconnect_pi.qml").joinpath("BrandTheme.js").read_text()
    mood = files("djconnect_pi.qml").joinpath("MoodTheme.js").read_text()
    program = "\n".join(line for line in brand.splitlines() if not line.startswith("."))
    program += "\nvar BrandTheme = {colors:colors};\n"
    program += "\n".join(line for line in mood.splitlines() if not line.startswith("."))
    program += "\nconsole.log(JSON.stringify(" + expression + "));"
    return json.loads(subprocess.run(["node", "-e", program], check=True, capture_output=True, text=True).stdout)


def test_mood_hues_match_pinned_apple_ui():
    assert _theme("['default','chill','groove','energy','party'].map(v => ['gradientStart','gradientMid','gradientEnd'].map(k => moodColor(v,k)))") == [
        ["#3285FF", "#843DF5", "#CB27F5"], ["#4DA3FF", "#7B61FF", "#D184FF"],
        ["#06C7AD", "#169BC8", "#10B981"], ["#DDFF00", "#00B8FF", "#39FF78"],
        ["#FF287F", "#AA38F5", "#F43DCE"],
    ]


def test_semantic_action_and_status_roles_do_not_follow_mood_or_artwork():
    values = _theme("['chill','groove','energy','party'].map(v => ['gradientStart','gradientMid','gradientEnd','focus','toastStart','toastEnd'].map(k => color(v,k)))")
    assert all(value == values[0] for value in values)
    assert len(set(_theme("['chill','groove','energy','party'].map(v => color(v,'backgroundStart'))"))) == 4


def test_unknown_mood_and_artwork_have_fresh_neutral_fallback():
    values = _theme("[undefined,null,true,false,-1,NaN,Infinity,'unknown'].map(v => key(v))")
    assert values == ["default"] * 8
    assert _theme("material('chill','')") == _theme("material('chill','not-a-colour')")
    assert _theme("material('chill','')") != _theme("material('chill','#ff0000')")


def test_bright_and_dark_artwork_keep_text_contrast_on_material():
    rows = _theme("['chill','groove','energy','party'].map(m => ['#ffffff','#000000','#ff0000','#00ff00','#0000ff','#ffff00','#ff00ff','#00ffff'].map(a => material(m,a))).flat()")
    def light(color):
        c = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return sum(v * w for v, w in zip(c, (0.2126, 0.7152, 0.0722)))
    for surface in rows:
        for foreground in (colors()["text"], colors()["muted"]):
            high, low = sorted((light(surface), light(foreground)), reverse=True)
            assert (high + 0.05) / (low + 0.05) >= 4.5, (surface, foreground)


def test_backend_readback_cannot_finish_after_shutdown():
    image = QImage(8, 8, QImage.Format_ARGB32)
    image.fill(QColor("red"))
    receiver = SimpleNamespace(_shutting_down=False)
    assert DJConnectBackend.sampleArtworkTint(receiver, image) == "#ff0000"
    receiver._shutting_down = True
    assert DJConnectBackend.sampleArtworkTint(receiver, image) == ""


@pytest.mark.parametrize("size", [(720, 720), (1200, 1920)])
def test_real_qt_readback_revocation_and_late_result_fences(size):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "tests/probes/artwork_palette_readback.py"), *(str(v) for v in size)],
        cwd=root, env={**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software"},
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    proof = json.loads(result.stdout)
    assert not proof["qml_errors"]
    assert proof["revoked_pending_callback_no_slot_call"] and proof["close_during_pending"]
