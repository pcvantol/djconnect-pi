.pragma library

var palettes = {
    "default": {
        gradientStart: "#247fff",
        gradientMid: "#7757ff",
        gradientEnd: "#c33cff",
        accent: "#7B61FF",
        accentSoft: "#3324145f",
        surface: "#24105c",
        focus: "#D184FF",
        chip: "#3324145f",
        backgroundStart: "#2b0a5f",
        backgroundMid: "#191053",
        backgroundEnd: "#070b16",
        bannerStart: "#12091d",
        bannerMid: "#26103f",
        bannerEnd: "#141125",
        overlayStart: "#2f8cff",
        overlayEnd: "#8b5cf6",
        toastStart: "#ff5a2e",
        toastMid: "#f13ccc",
        toastEnd: "#b731ff",
        sliderStart: "#ec4899",
        sliderEnd: "#8b5cf6"
    },
    "chill": {
        gradientStart: "#4DA3FF",
        gradientMid: "#7B61FF",
        gradientEnd: "#D184FF",
        accent: "#7B61FF",
        accentSoft: "#334d63a0",
        surface: "#35236a",
        focus: "#D184FF",
        chip: "#33293f72",
        backgroundStart: "#102f63",
        backgroundMid: "#1c1f56",
        backgroundEnd: "#070b16",
        bannerStart: "#071923",
        bannerMid: "#0c2c44",
        bannerEnd: "#0b1629",
        overlayStart: "#4DA3FF",
        overlayEnd: "#D184FF",
        toastStart: "#4DA3FF",
        toastMid: "#7B61FF",
        toastEnd: "#D184FF",
        sliderStart: "#4DA3FF",
        sliderEnd: "#D184FF"
    },
    "groove": {
        gradientStart: "#2EC4B6",
        gradientMid: "#7B61FF",
        gradientEnd: "#D184FF",
        accent: "#2EC4B6",
        accentSoft: "#332b5f72",
        surface: "#213f64",
        focus: "#D184FF",
        chip: "#332a4d5e",
        backgroundStart: "#073c42",
        backgroundMid: "#27215f",
        backgroundEnd: "#070b16",
        bannerStart: "#071d18",
        bannerMid: "#0b302a",
        bannerEnd: "#0b1824",
        overlayStart: "#2EC4B6",
        overlayEnd: "#D184FF",
        toastStart: "#2EC4B6",
        toastMid: "#7B61FF",
        toastEnd: "#D184FF",
        sliderStart: "#2EC4B6",
        sliderEnd: "#D184FF"
    },
    "energy": {
        gradientStart: "#8AC926",
        gradientMid: "#FFD166",
        gradientEnd: "#FF6A3D",
        accent: "#FFD166",
        accentSoft: "#334c3f18",
        surface: "#59461a",
        focus: "#FFE5A3",
        chip: "#333c3218",
        backgroundStart: "#2e430d",
        backgroundMid: "#4a3413",
        backgroundEnd: "#070b16",
        bannerStart: "#25100b",
        bannerMid: "#3a1421",
        bannerEnd: "#1d1121",
        overlayStart: "#8AC926",
        overlayEnd: "#FF6A3D",
        toastStart: "#8AC926",
        toastMid: "#FFD166",
        toastEnd: "#FF6A3D",
        sliderStart: "#8AC926",
        sliderEnd: "#FF6A3D"
    },
    "party": {
        gradientStart: "#FF2E63",
        gradientMid: "#A855F7",
        gradientEnd: "#FFD166",
        accent: "#A855F7",
        accentSoft: "#33441662",
        surface: "#4a1c5f",
        focus: "#FFD166",
        chip: "#3335144c",
        backgroundStart: "#571126",
        backgroundMid: "#341869",
        backgroundEnd: "#070b16",
        bannerStart: "#190d2d",
        bannerMid: "#34123d",
        bannerEnd: "#25131a",
        overlayStart: "#FF2E63",
        overlayEnd: "#FFD166",
        toastStart: "#FF2E63",
        toastMid: "#A855F7",
        toastEnd: "#FFD166",
        sliderStart: "#FF2E63",
        sliderEnd: "#FFD166"
    }
}

function key(value) {
    if (value === undefined || value === null || value < 0) return "default"
    var mood = Math.max(0, Math.min(100, Math.round(value)))
    if (mood <= 24) return "chill"
    if (mood <= 59) return "groove"
    if (mood <= 84) return "energy"
    return "party"
}

function color(value, token) {
    var theme = palettes[key(value)] || palettes.default
    return theme[token] || palettes.default[token] || "#247fff"
}

function disabled(position) {
    if (position === "mid") return "#3c3f61"
    if (position === "end") return "#4b3d65"
    return "#33415f"
}
