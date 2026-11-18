"""Bounded, stateless colour sampling of pixels already displayed by Qt."""
from __future__ import annotations

from PySide6.QtGui import QImage


def displayed_artwork_tint(image: QImage) -> str:
    """No IO, decoding, image cache or retention; callers own source admission."""
    if not isinstance(image, QImage) or image.isNull() or not (0 < image.width() <= 32 and 0 < image.height() <= 32):
        return ""
    red = green = blue = weight = 0
    for y in range(image.height()):
        for x in range(image.width()):
            pixel = image.pixelColor(x, y)
            alpha = pixel.alpha()
            red += pixel.red() * alpha
            green += pixel.green() * alpha
            blue += pixel.blue() * alpha
            weight += alpha
    if not weight:
        return ""
    return f"#{round(red / weight):02x}{round(green / weight):02x}{round(blue / weight):02x}"
