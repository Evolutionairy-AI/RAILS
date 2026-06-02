from rails_ref.admissibility import Class
from rails_ref.objects import EvidenceEnvelope, EvidenceItem, Verdict
from rails_ref.verifiers import PolicyVerifier, NaiveVerifier


def test_policy_verifier_fails_on_violation_with_att_basis():
    env = EvidenceEnvelope("o", [EvidenceItem("pkg_delta", Class.ATT, Class.ATT, reveals_defect=True)])
    out = PolicyVerifier(watch_kind="pkg_delta").verify("o", env)
    assert out.verdict == Verdict.FAIL
    assert Class.ATT in out.declared_basis


def test_policy_verifier_passes_when_clean():
    env = EvidenceEnvelope("o", [EvidenceItem("pkg_delta", Class.ATT, Class.ATT, reveals_defect=False)])
    out = PolicyVerifier(watch_kind="pkg_delta").verify("o", env)
    assert out.verdict == Verdict.PASS


def test_naive_verifier_passes_with_low_basis():
    env = EvidenceEnvelope("o", [EvidenceItem("self_report", Class.SELF, Class.SELF, reveals_defect=False)])
    out = NaiveVerifier(relies_on_kind="self_report").verify("o", env)
    assert out.verdict == Verdict.PASS
    assert out.declared_basis == (Class.SELF,)
