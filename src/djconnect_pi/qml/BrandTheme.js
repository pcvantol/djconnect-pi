.pragma library

// Pi Brand V2 presentation tokens. UI colours complement the immutable Core artwork.
// This JSON object is also consumed by Python/portal; keep it valid JSON.
var colors = {
    "background": "#080B1A",
    "backgroundStart": "#101D42",
    "backgroundMid": "#171334",
    "surface": "#18203B",
    "surfaceRaised": "#222C4D",
    "surfacePressed": "#303C62",
    "border": "#53658F",
    "text": "#F5F7FF",
    "muted": "#BEC8E6",
    "disabledText": "#8996B8",
    "cyan": "#45D9FF",
    "blue": "#638AFF",
    "purple": "#AA8CFF",
    "focus": "#70E3FF",
    "buttonStart": "#354EAB",
    "buttonMid": "#4D43AC",
    "buttonEnd": "#663CA3",
    "disabledStart": "#26324C",
    "disabledMid": "#2D3552",
    "disabledEnd": "#363453",
    "success": "#58D6A8",
    "danger": "#FF899B",
    "dangerSurface": "#72283D",
    "dangerPressed": "#542236",
    "warning": "#FFD18A",
    "warningSurface": "#66451F",
    "warningPressed": "#4F371D",
    "glass": "#D918203B",
    "glassBorder": "#8053658F",
    "scrim": "#E6080B1A",
    "transparent": "#00000000",
    "white": "#FFFFFF"
}

function alpha(color, opacity) {
    return "#" + opacity + color.slice(1)
}
