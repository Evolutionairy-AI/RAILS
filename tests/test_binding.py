from rails_ref.admissibility import Class
from rails_ref.objects import ObligationObject
from rails_ref.binding import bind_obligation
from rails_ref.attacks import downgrade_floor


def _ob(floor):
    return ObligationObject("o", floor, "t", "a", ("acme", "provider"))


def test_honest_binding_accepted():
    o = _ob(Class.ATT)
    assert bind_obligation(o, {"acme", "provider"}, template_floor=Class.ATT) is o


def test_stronger_floor_than_template_accepted():
    o = _ob(Class.PROOF)
    assert bind_obligation(o, {"acme", "provider"}, template_floor=Class.ATT) is o


def test_downgrade_rejected():
    o = downgrade_floor(_ob(Class.ATT), to=Class.SELF)
    assert bind_obligation(o, {"acme", "provider"}, template_floor=Class.ATT) is None


def test_missing_signature_rejected():
    o = _ob(Class.ATT)
    assert bind_obligation(o, {"acme"}, template_floor=Class.ATT) is None
