import random

from rails_ref.admissibility import Class, leq, cls_join, meets_floor
from rails_ref.attacks import forge_up_item, downgrade_floor, launder_basis_output
from rails_ref.objects import ObligationObject, Verdict


def test_forge_up_produces_overclaim():
    e = forge_up_item(Class.ATT, random.Random(0))
    assert e.claimed_class == Class.ATT and e.true_class != Class.ATT
    assert not leq(e.claimed_class, e.true_class)  # strict over-claim


def test_forge_up_to_bottom_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        forge_up_item(Class.SELF, random.Random(0))


def test_downgrade_floor_lowers_floor():
    o = ObligationObject("o", Class.ATT, "t", "a", ("p", "q"))
    assert downgrade_floor(o, to=Class.SELF).floor == Class.SELF


def test_launder_basis_declares_admissible_but_lies():
    out = launder_basis_output("v_evil", floor=Class.ATT, true_consulted=Class.SELF)
    assert out.verdict == Verdict.PASS
    assert meets_floor(cls_join(out.declared_basis), Class.ATT)
