import time
from collections import defaultdict, deque

WINDOW_SECONDS = 3600
LIMIT_PER_WINDOW = 20

_hits: dict[str, deque] = defaultdict(deque)


def is_rate_limited(key: str, now: float | None = None) -> bool:
    now = now if now is not None else time.time()
    q = _hits[key]
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= LIMIT_PER_WINDOW:
        return True
    q.append(now)
    return False


def reset() -> None:
    """Test-only: clears all counters."""
    _hits.clear()
