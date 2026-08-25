"""A deliberately flawed in-memory session store used only for calibration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Lock


@dataclass(frozen=True)
class Session:
    session_id: str
    user_id: str
    scopes: list[str]
    expires_at: float
    last_seen_at: float


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def issue(
        self,
        session_id: str,
        user_id: str,
        scopes: list[str],
        *,
        now: float,
        ttl: float,
    ) -> Session:
        session = Session(session_id, user_id, scopes, now + ttl, now)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def validate(self, session_id: str, *, now: float) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
        return bool(session and now <= session.expires_at)

    def revoke(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def touch(self, session_id: str, *, now: float) -> bool:
        with self._lock:
            current = self._sessions.get(session_id)
        if current is None or now > current.expires_at:
            return False
        updated = replace(current, last_seen_at=now)
        with self._lock:
            self._sessions[session_id] = updated
        return True
