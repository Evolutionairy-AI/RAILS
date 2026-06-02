import random

from rails_ref.admissibility import Class, meets_floor
from rails_ref.objects import ObligationObject, VerifierOutput, Verdict
from rails_ref.mesh import clear


def _ob(floor):
    return ObligationObject("o", floor, "t", "a", ("p", "q"))


def test_sub_floor_only_does_not_emit():
    o = _ob(Class.ATT)
    vs = [VerifierOutput("v1", Verdict.PASS, 0.9, (Class.SELF,)),
          VerifierOutput("v2", Verdict.PASS, 0.8, (Class.SIGN,))]
    d = clear(o, vs)
    assert d.emitted is False


def test_emits_when_a_survivor_meets_floor():
    o = _ob(Class.ATT)
    vs = [VerifierOutput("v1", Verdict.PASS, 0.9, (Class.ATT,)),
          VerifierOutput("v2", Verdict.PASS, 0.5, (Class.SELF,))]  # weight 0
    d = clear(o, vs)
    assert d.emitted is True
    assert meets_floor(d.cls_basis, o.floor)


def test_sub_floor_verifier_excluded_from_vote():
    # one ATT verifier says FAIL; a sub-floor SELF verifier says PASS loudly.
    # the SELF verifier is excluded, so policy FAIL must fire on the ATT verifier.
    o = _ob(Class.ATT)
    vs = [VerifierOutput("att", Verdict.FAIL, 0.9, (Class.ATT,)),
          VerifierOutput("self", Verdict.PASS, 1.0, (Class.SELF,))]
    d = clear(o, vs)
    assert d.emitted is True
    assert d.performance == Verdict.FAIL  # the excluded PASS did not flip it
    assert d.policy == Verdict.FAIL


def test_invariant_holds_under_random_adversarial_inputs():
    rng = random.Random(1234)
    classes = list(Class)
    verdicts = list(Verdict)
    for _ in range(20000):
        o = _ob(rng.choice(classes))
        vs = [VerifierOutput(f"v{i}", rng.choice(verdicts), rng.random(),
                             tuple(rng.sample(classes, rng.randint(1, 3))))
              for i in range(rng.randint(1, 6))]
        d = clear(o, vs)
        if d.emitted:
            # THE soundness property: every emitted (material) settlement meets the floor
            assert meets_floor(d.cls_basis, o.floor), (o.floor, vs, d)
