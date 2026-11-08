"""Observe the window's touch sequence without taking over a page's touch events."""

from PySide6.QtCore import QEvent, QObject, QTimer, Signal, Slot
from PySide6.QtGui import QInputDevice


class EdgeBackGesture(QObject):
    backRequested = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self._window = None
        self._start = None
        self._pending_route = ""
        self._dispatch = QTimer(self)
        self._dispatch.setSingleShot(True)
        self._dispatch.timeout.connect(self._emit_back)

    @Slot(QObject)
    def observe(self, window):
        self._window = window
        window.installEventFilter(self)
        window.destroyed.connect(self._detach)

    def _detach(self):
        self.cancel()
        self._window = None

    @Slot()
    def cancel(self):
        self._start = None
        self._pending_route = ""
        self._dispatch.stop()

    def _emit_back(self):
        route = self._pending_route
        self._pending_route = ""
        if route and self._window is not None and self._window.property("edgeBackRoute") == route:
            self.backRequested.emit(route)

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QEvent.Type.TouchCancel:
            self.cancel()
        elif event_type in (QEvent.Type.TouchBegin, QEvent.Type.TouchUpdate, QEvent.Type.TouchEnd):
            self._observe_touch(watched, event, event_type)
        return False

    def _observe_touch(self, window, event, event_type):
        if event.device().type() != QInputDevice.DeviceType.TouchScreen:
            return
        points = event.points()
        if len(points) != 1:
            self.cancel()
            return
        point = points[0]
        position = point.position()
        if event_type == QEvent.Type.TouchBegin:
            self.cancel()
            route = window.property("edgeBackRoute")
            if route and position.x() <= 20 and position.y() < window.height() - 112:
                self._start = point.id(), position, route
            return
        if self._start is None:
            return
        point_id, origin, route = self._start
        dx, dy = position.x() - origin.x(), abs(position.y() - origin.y())
        if point.id() != point_id or dx < -12 or (dy >= 22 and dy * 2 >= dx):
            self.cancel()
        elif event_type == QEvent.Type.TouchEnd:
            self._start = None
            if dx >= 84 and dx > 2 * dy:
                self._pending_route = route
                self._dispatch.start(0)
