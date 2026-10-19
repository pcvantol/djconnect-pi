"""Paired, Profile-bound Session HTTP transport shared by both Pi targets.

Core owns every identity, ordering, grant and effect. This transport has no
persistent Session cache and never automatically retries a write.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import quote

import requests

from .config import CLIENT_TYPE
from .i18n import locale_for_language

PREFIX = "/api/djconnect/v1/"
MOODS = frozenset({"chill", "groove", "energy", "party"})


class SessionError(Exception):
    def __init__(self, category: str, code: str = ""):
        self.category = category
        self.code = code
        super().__init__(category)  # Never surface private JSON, URLs or identifiers.


@dataclass(frozen=True)
class SessionBinding:
    ha_url: str
    device_id: str
    token: str = field(repr=False)
    profile_id: str
    resolved_profile_id: str
    private_session: bool
    profile_type: str
    privacy_mode: str
    language: str

    @classmethod
    def capture(cls, cfg):
        if not cfg.paired or not cfg.device_token or not cfg.ha_url:
            raise SessionError("unpaired")
        return cls(cfg.ha_url.rstrip("/"), cfg.device_id, cfg.device_token,
                   cfg.explicit_profile_id, cfg.active_profile_id,
                   cfg.private_session, cfg.active_profile_type, cfg.active_profile_privacy_mode, cfg.language)

    def identity(self) -> dict[str, Any]:
        result = {"device_id": self.device_id, "client_type": CLIENT_TYPE}
        if self.profile_id:
            result["profile_id"] = self.profile_id
        if self.private_session:
            result["private_session"] = True
        return result


def identifier(value: Any) -> str:
    if not isinstance(value, str) or not 0 < len(value) <= 512 or any(ord(c) < 32 for c in value):
        raise SessionError("invalid")
    return value


class SessionTransport:
    def __init__(self, config: Callable, timeout: float = 8.0):
        self.config = config
        self.timeout = timeout

    def binding(self) -> SessionBinding:
        return SessionBinding.capture(self.config())

    def _request(self, binding: SessionBinding, method: str, route: str, payload=None) -> dict:
        if binding != self.binding():
            raise SessionError("context_changed")
        headers = {
            "Authorization": "Bearer " + binding.token,
            "X-DJConnect-Device-ID": binding.device_id,
            "X-DJConnect-Client-Type": CLIENT_TYPE,
            "Accept": "application/json", "Cache-Control": "no-store",
            "Accept-Language": locale_for_language(binding.language),
        }
        if binding.profile_id:
            headers["X-DJConnect-Profile-ID"] = binding.profile_id
        body = {**binding.identity(), **(payload or {})}
        if method == "GET":
            body = {key: str(value).lower() if isinstance(value, bool) else value for key, value in body.items()}
        try:
            response = requests.request(method, binding.ha_url + PREFIX + route,
                headers=headers, timeout=self.timeout, allow_redirects=False,
                **({"params": body} if method == "GET" else {"json": body}))
        except requests.RequestException:
            raise SessionError("offline" if method == "GET" else "uncertain") from None
        if binding != self.binding():
            raise SessionError("context_changed")
        if 300 <= response.status_code < 400:
            raise SessionError("unavailable" if method == "GET" else "uncertain")
        if response.status_code >= 500:
            raise SessionError("unavailable" if method == "GET" else "uncertain")
        try:
            data = response.json()
        except (ValueError, TypeError):
            raise SessionError("invalid" if method == "GET" else "uncertain") from None
        if not isinstance(data, dict):
            raise SessionError("invalid")
        code = data.get("error") if isinstance(data.get("error"), str) else ""
        if response.status_code in (401, 403):
            raise SessionError("denied")
        if response.status_code in (404, 405, 426) or code == "history_contract_upgrade_required":
            raise SessionError("unavailable", code if code in {"history_unavailable", "active_session_not_found", "history_contract_upgrade_required"} else "")
        if response.status_code == 409:
            raise SessionError("conflict")
        if response.status_code >= 400 or data.get("success") is not True:
            raise SessionError("unavailable")
        return deepcopy(data)

    def capabilities(self, binding):
        return self._request(binding, "GET", "capabilities")

    def active(self, binding):
        return self._request(binding, "GET", "session/active")

    def start(self, binding, mood: str):
        if not isinstance(mood, str) or mood not in MOODS:
            raise SessionError("invalid")
        return self._request(binding, "POST", "session/start", {
            "mood": mood, "language": locale_for_language(binding.language)})

    def end(self, binding, session_id: str):
        return self._request(binding, "POST", "session/end", {"session_id": identifier(session_id)})

    def broadcast(self, binding, session_id: str):
        return self._request(binding, "GET", "session/broadcast/snapshot", {"session_id": identifier(session_id)})

    def history(self, binding, *, cursor: str = "", limit: int = 20):
        return self._request(binding, "GET", "session/history", self._page(cursor, limit))

    def timeline(self, binding, session_id: str, *, cursor: str = "", limit: int = 20,
                 window: str | None = "tail", anchor_entry_id: str = ""):
        if window not in {None, "tail", "anchor"} or (cursor and window is not None):
            raise SessionError("invalid")
        page = self._page(cursor, limit)
        if window is not None:
            page["window"] = window
        if window == "anchor":
            page["anchor_entry_id"] = identifier(anchor_entry_id)
        route = "session/history/" + quote(identifier(session_id), safe="")
        return self._request(binding, "GET", route, page)

    def search(self, binding, session_id: str, query: str, *, cursor: str = "", limit: int = 20):
        if not isinstance(query, str):
            raise SessionError("invalid")
        query = query.strip()
        if not 1 <= len(query) <= 200:
            raise SessionError("invalid")
        route = "session/history/" + quote(identifier(session_id), safe="") + "/search"
        return self._request(binding, "GET", route, {**self._page(cursor, limit), "q": query})

    def open_entry(self, binding, session_id: str, entry_id: str):
        return self._request(binding, "POST", "session/history/open", {
            "history_contract_version": 2,
            "action": {"kind": "open_session", "session_id": identifier(session_id),
                       "entry_id": identifier(entry_id), "navigation_only": True}})

    @staticmethod
    def _page(cursor, limit):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
            raise SessionError("invalid")
        page = {"limit": limit, "history_contract_version": 2}
        if cursor:
            if not isinstance(cursor, str) or len(cursor) > 8192 or any(ord(c) < 32 for c in cursor):
                raise SessionError("invalid")
            page["cursor"] = cursor
        return page
