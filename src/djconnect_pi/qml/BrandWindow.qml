import QtQuick
import QtQuick.Controls
import "BrandTheme.js" as BrandTheme

ApplicationWindow {
    // Basic controls inherit from the window, including their popup windows.
    palette.window: BrandTheme.colors.background
    palette.windowText: BrandTheme.colors.text
    palette.base: BrandTheme.colors.surface
    palette.alternateBase: BrandTheme.colors.surfaceRaised
    palette.text: BrandTheme.colors.text
    palette.button: BrandTheme.colors.surfaceRaised
    palette.buttonText: BrandTheme.colors.text
    palette.highlight: BrandTheme.colors.buttonStart
    palette.highlightedText: BrandTheme.colors.text
    palette.placeholderText: BrandTheme.colors.muted
    palette.light: BrandTheme.colors.border
    palette.midlight: BrandTheme.colors.surfacePressed
    palette.mid: BrandTheme.colors.border
    palette.dark: BrandTheme.colors.background
    palette.shadow: BrandTheme.colors.background
    palette.link: BrandTheme.colors.cyan
    palette.linkVisited: BrandTheme.colors.purple
    palette.toolTipBase: BrandTheme.colors.surfaceRaised
    palette.toolTipText: BrandTheme.colors.text
    palette.accent: BrandTheme.colors.focus
    palette.disabled.text: BrandTheme.colors.disabledText
    palette.disabled.buttonText: BrandTheme.colors.disabledText
    palette.disabled.windowText: BrandTheme.colors.disabledText
}
