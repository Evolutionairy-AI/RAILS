from rails_ref.admissibility import Class, leq
from rails_ref.exposure import floor_for_exposure


def test_low_stakes_gets_low_floor():
    assert floor_for_exposure(5) == Class.SELF
    assert floor_for_exposure(50) == Class.SIGN


def test_high_stakes_escalates():
    assert floor_for_exposure(500) == Class.ATT
    assert floor_for_exposure(50_000) == Class.PROOF


def test_worked_scenario_consistency():
    # the ~$200 charger obligation (interop_demo) maps to an ATT floor
    assert floor_for_exposure(200) == Class.ATT


def test_floor_nondecreasing_in_exposure():
    prev = Class.SELF
    for x in [1, 9, 10, 99, 100, 999, 1000, 9999, 10_000, 100_000]:
        f = floor_for_exposure(x)
        assert leq(prev, f)   # floor never decreases as exposure rises
        prev = f
