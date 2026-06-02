import random

from rails_ref.admissibility import Class
from rails_ref.objects import EvidenceItem
from rails_ref.intake import admit, is_overclaim


def test_honest_item_admitted_at_claimed_class():
    e = EvidenceItem("ci_log", claimed_class=Class.ATT, true_class=Class.ATT)
    out = admit(e, sophistication=0.0, rng=random.Random(0))
    assert out.claimed_class == Class.ATT


def test_underclaim_is_not_overclaim():
    e = EvidenceItem("modest", claimed_class=Class.SELF, true_class=Class.ATT)
    assert not is_overclaim(e)
    out = admit(e, sophistication=0.0, rng=random.Random(0))
    assert out.claimed_class == Class.SELF  # unchanged


def test_overclaim_downgraded_when_detected():
    e = EvidenceItem("self_report", claimed_class=Class.ATT, true_class=Class.SELF)
    assert is_overclaim(e)
    out = admit(e, sophistication=0.0, rng=random.Random(0))
    assert out.claimed_class == Class.SELF  # downgraded to true class


def test_overclaim_passes_when_forgery_perfect():
    e = EvidenceItem("self_report", claimed_class=Class.ATT, true_class=Class.SELF)
    out = admit(e, sophistication=1.0, rng=random.Random(0))
    assert out.claimed_class == Class.ATT  # forgery fooled intake


def test_catch_rate_tracks_sophistication():
    # over many trials, fraction that pass ~ sophistication
    rng = random.Random(42)
    passed = 0
    n = 4000
    for _ in range(n):
        e = EvidenceItem("x", Class.ATT, Class.SELF)
        if admit(e, sophistication=0.3, rng=rng).claimed_class == Class.ATT:
            passed += 1
    assert 0.25 < passed / n < 0.35
