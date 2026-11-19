"""Album pixels from the current Runtime's renderer-safe playback proxy."""
import re

from .session_forecast_image import ForecastImages, fetch_proxy_pixels
from .session_projection import session_playback
from .session_transport import SessionError, private_scope_allowed

PROXY_PATH = re.compile(r"/api/djconnect/v1/image_proxy/[A-Za-z0-9_-]{24}")


class PlaybackArtwork(ForecastImages):
    def sync(self):
        if self.closed:
            return
        owner = self.owner
        session = owner._session
        lease = binding = None
        if (self.visible and owner._foreground and owner._running_action not in {"start", "end"}
                and private_scope_allowed(owner)):
            playback = session_playback(session)
            if playback:
                path = session["broadcast"]["playback"].get("artwork_url")
                if isinstance(path, str) and PROXY_PATH.fullmatch(path):
                    try:
                        binding = owner.transport.binding()
                    except SessionError:
                        pass
                    else:
                        lease = {"session_id": session["session_id"], "item_id": playback["item_id"],
                                 "path": path, "deadline": None}
        self._set_lease(binding, lease)

    def _attempt_bucket(self):
        return self.desired["session_id"], self.desired["item_id"]

    def fetch(self, binding, lease, allowed):
        path = lease["path"]
        return fetch_proxy_pixels(binding, path, allowed) if PROXY_PATH.fullmatch(path) else ""

    def public_pixels(self, pixels):
        return {"source": pixels, "session_id": self.desired["session_id"], "item_id": self.desired["item_id"]}
