from app.core.throttle import LIMIT_PER_WINDOW, is_rate_limited, reset


def test_allows_up_to_limit_then_blocks():
    reset()
    now = 1000.0
    for _ in range(LIMIT_PER_WINDOW):
        assert not is_rate_limited("1.2.3.4", now)
    assert is_rate_limited("1.2.3.4", now)


def test_window_expires():
    reset()
    now = 1000.0
    for _ in range(LIMIT_PER_WINDOW):
        is_rate_limited("5.6.7.8", now)
    assert is_rate_limited("5.6.7.8", now)
    assert not is_rate_limited("5.6.7.8", now + 3601)


def test_different_ips_independent():
    reset()
    now = 1000.0
    for _ in range(LIMIT_PER_WINDOW):
        is_rate_limited("9.9.9.9", now)
    assert not is_rate_limited("1.1.1.1", now)
