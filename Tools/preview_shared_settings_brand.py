"""Offline native QML fixture preview; never connects to HA or a physical Pi."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from shiboken6 import delete

from djconnect_pi.i18n import translate
from djconnect_pi.shared_settings import SharedSettingsClient, snapshot_response

ROOT = Path(__file__).resolve().parents[1]


class PreviewBackend(QObject):
    sharedSettingsChanged = Signal()
    languageChanged = Signal()

    def __init__(self, language, state):
        super().__init__()
        self.state = {**state, "available": True, "error": ""}
        self.language = language

    @Property("QVariantMap", notify=sharedSettingsChanged)
    def sharedSettings(self):
        return self.state

    @Property(bool, notify=sharedSettingsChanged)
    def sharedSettingsBusy(self):
        return False

    @Property(int, notify=languageChanged)
    def translationVersion(self):
        return 1

    @Slot(str, result=str)
    def t(self, key):
        return translate(self.language, key)

    @Slot()
    def pollSharedSettings(self):
        pass

    @Slot("QVariantMap")
    def saveSharedSettings(self, patch):
        raise AssertionError("Preview must not save settings")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    warnings = []
    qInstallMessageHandler(lambda kind, context, message: warnings.append(message))
    QQuickStyle.setStyle("Basic")
    app = QGuiApplication([])
    engine = QQmlApplicationEngine()
    source = """import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "QML_ROOT"
Window {
    width: 720; height: 720; visible: true; color: "#171029"
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 28; spacing: 12
        BrandLockup { Layout.fillWidth: true; Layout.preferredHeight: width >= 512 ? width / 4 : width * 448 / 1728 }
        Row {
            spacing: 18
            Repeater { model: [16,20,24,32,40,64,128]
                Image { required property int modelData; width: modelData; height: modelData
                    source: "QML_ROOT/brand-mark-" + modelData + ".png" }
            }
        }
        Flickable {
            objectName: "settingsScroll"; Layout.fillWidth: true; Layout.fillHeight: true
            contentHeight: editor.height; clip: true
            ScrollBar.vertical: ScrollBar {}
            SharedSettingsPanel { id: editor; objectName: "settingsEditor"; width: parent.width; backend: preview }
        }
    }
}""".replace("QML_ROOT", (ROOT / "src/djconnect_pi/qml").as_uri())
    checks = []
    for case in ("active", "legacy_unknown", "unavailable_voice", "empty"):
        if case == "empty":
            state = {}
        else:
            data = json.loads(
                (ROOT / f"tests/fixtures/shared_settings/{case}.json").read_text()
            )
            owner = SharedSettingsClient(lambda: None)
            owner._snapshot = snapshot_response(data)
            owner.context = lambda: ()
            state = owner.projection()
        for language in ("en", "nl", "de", "fr", "es"):
            backend = PreviewBackend(language, state)
            engine.rootContext().setContextProperty("preview", backend)
            engine.loadData(
                source.encode(), QUrl("file:///private/tmp/pi-native-preview.qml")
            )
            assert engine.rootObjects(), warnings
            window = engine.rootObjects()[-1]
            for width, height in ((720, 720), (1200, 1920)):
                window.setWidth(width)
                window.setHeight(height)
                for _ in range(12):
                    app.processEvents()

                def items(item):
                    yield item
                    for child in item.childItems():
                        yield from items(child)

                controls = [
                    x
                    for x in items(window.contentItem())
                    if x.objectName().startswith("shared_choice_")
                ]
                assert len(controls) == (0 if case == "empty" else 6), (
                    case,
                    language,
                    len(controls),
                    warnings,
                )
                assert all(c.width() > 100 and c.height() >= 54 for c in controls)
                scroll = window.findChild(QQuickItem, "settingsScroll")
                assert scroll.property("contentHeight") > 0
                if language == "nl" and case == "active":
                    assert window.grabWindow().save(
                        str(args.output / f"settings-brand-{width}x{height}.png")
                    )
                    scroll.setProperty(
                        "contentY",
                        max(0, scroll.property("contentHeight") - scroll.height()),
                    )
                    for _ in range(8):
                        app.processEvents()
                    assert window.grabWindow().save(
                        str(args.output / f"settings-brand-{width}x{height}-bottom.png")
                    )
                checks.append(
                    {
                        "case": case,
                        "language": language,
                        "size": [width, height],
                        "controls": len(controls),
                    }
                )
            window.close()
            delete(window)
            app.processEvents()
    # Fail on QML errors, missing assets, binding loops or undefined properties.
    errors = [
        m
        for m in warnings
        if any(
            x in m for x in ("Error", "Unable", "Cannot", "undefined", "Binding loop")
        )
    ]
    assert not errors, list(dict.fromkeys(errors))
    (args.output / "native-fixture-readback.json").write_text(
        json.dumps(
            {
                "qualification": "offline macOS Qt fixture only; no HA/installed/physical Pi claim",
                "qt": "6.11.2",
                "checks": checks,
                "qml_errors": errors,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"{len(checks)} native fixture views checked; no QML errors")


if __name__ == "__main__":
    main()
