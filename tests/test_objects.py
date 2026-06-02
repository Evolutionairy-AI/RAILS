from rails_ref.admissibility import Class
from rails_ref.objects import (
    ObligationObject, EvidenceItem, EvidenceEnvelope,
    VerifierOutput, Verdict, ClearingDecision, Finality,
)


def test_obligation_carries_floor():
    o = ObligationObject(id="o1", floor=Class.ATT, task="fix bug",
                         acceptance="tests pass", parties=("acme", "provider"))
    assert o.floor == Class.ATT
    assert o.material is True


def test_evidence_item_claimed_vs_true_class():
    e = EvidenceItem(kind="ci_log", claimed_class=Class.ATT, true_class=Class.ATT)
    assert e.claimed_class == Class.ATT and e.true_class == Class.ATT
    assert e.reveals_defect is False


def test_envelope_collects_items():
    env = EvidenceEnvelope("o1", [EvidenceItem("a", Class.SELF, Class.SELF)])
    assert env.obligation_id == "o1" and len(env.items) == 1


def test_verifier_output_holds_declared_basis():
    vo = VerifierOutput(verifier_id="v1", verdict=Verdict.PASS, confidence=0.9,
                        declared_basis=(Class.ATT,))
    assert vo.verdict == Verdict.PASS and Class.ATT in vo.declared_basis


def test_clearing_decision_emitted_flag():
    d = ClearingDecision("o1", Verdict.PASS, Verdict.PASS, Class.ATT, 0.9,
                         Finality.PROVISIONAL, emitted=True)
    assert d.emitted is True and d.finality == Finality.PROVISIONAL
