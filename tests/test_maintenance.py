from djconnect_pi.maintenance import in_window


def test_empty_window_is_allowed() -> None:
    assert in_window("")

