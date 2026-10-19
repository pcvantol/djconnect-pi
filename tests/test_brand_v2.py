from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from djconnect_pi.i18n import SUPPORTED_LANGUAGES, translate
from djconnect_pi.shared_settings import CHOICES, FIELDS
from djconnect_pi.web_portal import index_html

ROOT = Path(__file__).resolve().parents[1]


def test_imported_assets_match_exact_candidate_and_preserve_alpha_and_native_sizes():
    receipt = json.loads((ROOT / "docs/branding/pi-import.json").read_text())
    manifest_bytes = (ROOT / "docs/branding/core-manifest.json").read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == receipt["manifest_sha256"]
    manifest = json.loads(manifest_bytes)
    assert receipt["producer_commit"] == "883cb9f3ff9de8ec7f5ae4c5f04f852e0d8bd866"
    assert receipt["producer_status"] == "open_candidate_requires_protected_acceptance"
    for path, source in receipt["imported"].items():
        data = (ROOT / path).read_bytes()
        original = manifest["files"][source["source"]]
        assert (
            hashlib.sha256(data).hexdigest() == source["sha256"] == original["sha256"]
        )
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">II", data[16:24]) == (
            original["width"],
            original["height"],
        )
        assert data[25] == 6  # RGBA, without opaque-square recompositing.
    for size in (16, 20, 24, 32, 40):
        assert (
            manifest["files"][f"assets/djconnect/brand-v2/mark-{size}.png"]["role"]
            == "headset-only"
        )


def test_portal_embeds_canonical_local_wordmarks_and_micro_favicon():
    html = index_html("fixture").decode()
    assert 'sizes="32x32" href="data:image/png;base64,' in html
    assert (
        '<picture><source media="(min-width:548px)" srcset="data:image/png;base64,'
        in html
    )
    assert 'class="brand-lockup"' in html
    assert 'alt="DJConnect"' in html


def test_dynamic_settings_labels_and_brand_tagline_exist_in_all_locales():
    for language in SUPPORTED_LANGUAGES:
        for field in FIELDS:
            key = f"shared_field_{field}"
            assert translate(language, key) != key
        for field, choices in CHOICES.items():
            for value in choices:
                key = f"shared_{field}_{value}"
                assert translate(language, key) != key
        assert translate(language, "tagline") != "tagline"
    assert translate("en", "tagline") == "Your music. Your DJ."


def test_native_settings_and_brand_views_in_every_locale(tmp_path):
    import os
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "Tools/preview_shared_settings_brand.py"),
            "--output",
            str(tmp_path),
        ],
        env={
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
        },
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    readback = json.loads((tmp_path / "native-fixture-readback.json").read_text())
    assert len(readback["checks"]) == 40
    assert not readback["qml_errors"]
