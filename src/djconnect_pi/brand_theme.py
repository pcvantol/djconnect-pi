"""Shared Pi presentation colours; canonical artwork remains Core-owned."""
from __future__ import annotations

import json
from importlib.resources import files


def colors() -> dict[str, str]:
    source = files("djconnect_pi.qml").joinpath("BrandTheme.js").read_text(encoding="utf-8")
    return json.JSONDecoder().raw_decode(source.split("var colors = ", 1)[1])[0]


def css_color(value: str) -> str:
    """QML uses #AARRGGBB; CSS uses #RRGGBBAA."""
    return "#" + value[3:] + value[1:3] if len(value) == 9 else value


def apply_palette(app) -> None:
    """Give Basic controls (including native popup menus) the same dark palette."""
    from PySide6.QtGui import QColor, QPalette

    theme = colors()
    palette = QPalette()
    for role, token in {
        "Window": "background", "WindowText": "text", "Base": "surface",
        "AlternateBase": "surfaceRaised", "Text": "text", "Button": "surfaceRaised",
        "ButtonText": "text", "Highlight": "buttonStart", "HighlightedText": "text",
        "Link": "cyan", "LinkVisited": "purple", "PlaceholderText": "muted",
        "Light": "border", "Midlight": "surfacePressed", "Mid": "border",
        "Dark": "background", "Shadow": "background", "ToolTipBase": "surfaceRaised",
        "ToolTipText": "text", "Accent": "focus",
    }.items():
        palette.setColor(getattr(QPalette.ColorRole, role), QColor(theme[token]))
    for role in (QPalette.Text, QPalette.ButtonText, QPalette.WindowText, QPalette.PlaceholderText):
        palette.setColor(QPalette.Disabled, role, QColor(theme["disabledText"]))
    app.setPalette(palette)
