"""Process-local conservative UTC floor for original server expiry deadlines."""
from __future__ import annotations

import time
from threading import Lock


def elapsed_time():
    # Linux/Pi BOOTTIME includes suspend; wall time is still checked independently.
    if hasattr(time, "CLOCK_BOOTTIME"):
        return time.clock_gettime(time.CLOCK_BOOTTIME)
    return time.monotonic()


class ExpiryClock:
    """A backward wall-clock correction cannot extend an already observed lifetime.

    Original wire deadlines are never modified or renewed on reads. A forward
    clock correction is deliberately conservative until actual UTC catches up.
    This is not a substitute for a synchronized host clock or server authority.
    """

    def __init__(self, wall=time.time, elapsed=elapsed_time):
        self._wall = wall
        self._elapsed = elapsed
        self._lock = Lock()
        self._utc = wall()
        self._tick = elapsed()

    def now(self):
        with self._lock:
            tick = self._elapsed()
            self._utc = max(self._wall(), self._utc + max(0, tick - self._tick))
            self._tick = tick
            return self._utc
