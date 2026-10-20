from types import SimpleNamespace

from djconnect_pi.expiry_clock import ExpiryClock


def test_backward_correction_and_repeated_reads_never_extend_original_deadline():
    host = SimpleNamespace(wall=1000, tick=50)
    clock = ExpiryClock(lambda: host.wall, lambda: host.tick)
    assert clock.now() == 1000
    host.wall = 100  # host clock corrected backwards
    host.tick = 55
    assert clock.now() == 1005
    assert clock.now() == 1005  # rereading has no TTL reset
    host.tick = 60
    assert clock.now() == 1010


def test_forward_correction_is_conservative_and_elapsed_time_keeps_advancing():
    host = SimpleNamespace(wall=1000, tick=50)
    clock = ExpiryClock(lambda: host.wall, lambda: host.tick)
    host.wall = 2000
    assert clock.now() == 2000
    host.wall = 1001
    host.tick = 53
    assert clock.now() == 2003
