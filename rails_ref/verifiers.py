"""Verifiers: objects that inspect an Evidence Envelope and emit a VerifierOutput.

Every verifier must declare the admissibility class(es) of the basis it relied
on. That declaration is what the floor gate acts on.
"""
from __future__ import annotations
from typing import Protocol

from rails_ref.admissibility import Class, cls_join
from rails_ref.objects import EvidenceEnvelope, VerifierOutput, Verdict


class Verifier(Protocol):
    verifier_id: str
    def verify(self, obligation_id: str, env: EvidenceEnvelope) -> VerifierOutput: ...


class PolicyVerifier:
    """Honest deterministic verifier: inspects high-admissibility evidence of a
    given kind and FAILs when that evidence reveals a defect."""

    def __init__(self, watch_kind: str, verifier_id: str = "policy", confidence: float = 0.95):
        self.watch_kind = watch_kind
        self.verifier_id = verifier_id
        self.confidence = confidence

    def verify(self, obligation_id: str, env: EvidenceEnvelope) -> VerifierOutput:
        relevant = [it for it in env.items if it.kind == self.watch_kind]
        if relevant:
            basis = tuple(it.claimed_class for it in relevant)
            verdict = Verdict.FAIL if any(it.reveals_defect for it in relevant) else Verdict.PASS
        else:
            basis = (cls_join([it.claimed_class for it in env.items]),) if env.items else (Class.SELF,)
            verdict = Verdict.PASS
        return VerifierOutput(self.verifier_id, verdict, self.confidence, basis)


class NaiveVerifier:
    """Honest-but-fooled verifier — models today's naive LLM-as-judge. It relies on
    a low-admissibility item (e.g. the agent self-report), returns PASS, and
    HONESTLY declares the low-class basis it used, so the floor gate excludes it.
    (Contrast with the LAUNDER-BASIS attacker, which lies about its basis.)"""

    def __init__(self, relies_on_kind: str = "self_report",
                 verifier_id: str = "naive", confidence: float = 0.8):
        self.relies_on_kind = relies_on_kind
        self.verifier_id = verifier_id
        self.confidence = confidence

    def verify(self, obligation_id: str, env: EvidenceEnvelope) -> VerifierOutput:
        relied = next((it for it in env.items if it.kind == self.relies_on_kind), None)
        basis = (relied.claimed_class,) if relied else (Class.SELF,)
        return VerifierOutput(self.verifier_id, Verdict.PASS, self.confidence, basis)
