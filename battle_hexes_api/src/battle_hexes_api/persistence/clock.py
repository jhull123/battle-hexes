"""Production and logical-expiry clock helpers."""

import time

from .contracts import Clock


class SystemClock:
    """A clock using whole Unix epoch seconds from the host system."""

    def now(self):
        return int(time.time())


def is_expired(expires_at, clock: Clock):
    """Return whether a persistence record is logically expired."""
    if isinstance(expires_at, bool) or not isinstance(expires_at, int):
        raise ValueError("expires_at must be an integral Unix epoch")
    now = clock.now()
    if isinstance(now, bool) or not isinstance(now, int):
        raise ValueError("clock must return an integral Unix epoch")
    return expires_at <= now
