import hashlib
import os
import subprocess
import sys
from importlib.resources import files


def test_inter_asset_and_required_license_are_pinned():
    data = files("djconnect_pi").joinpath("fonts/InterVariable.ttf").read_bytes()
    assert hashlib.sha256(data).hexdigest() == "4989b125924991b90d05b2d16e0e388c48f7d5bb8b30539bbf9c755278d0ccaf"
    license_text = files("djconnect_pi").joinpath("fonts/LICENSE.txt").read_text()
    assert "SIL OPEN FONT LICENSE Version 1.1" in license_text
    assert "The Inter Project Authors" in license_text


def test_actual_qt_font_loading_is_idempotent_and_covers_ui_samples():
    script = '''
from PySide6.QtGui import QGuiApplication,QFontMetrics,QFontInfo
from djconnect_pi.brand_theme import apply_palette
app=QGuiApplication([])
apply_palette(app);apply_palette(app)
assert app.font().family()=="Inter Variable"
assert QFontInfo(app.font()).family()=="Inter Variable"
m=QFontMetrics(app.font())
for text in ['Chat met de DJ…','Ask your DJ…','Frag deinen DJ…','Parlez à votre DJ…','Habla con tu DJ…']:
    assert all(m.inFontUcs4(ord(c)) for c in text)
'''
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "QT_QUICK_BACKEND": "software"}
    result = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
