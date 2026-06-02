"""Mesh Aggregator Gamma + floor-enforcement gate.

Soundness invariant (RAILS paper, Sec 5.4):  Emit(S) => cls(B) >= phi_O.
This is asserted at emission. The simulation's purpose is to try to make this
assertion fire; a firing is a finding, never suppressed.

Spec-gap (spec Sec 12, ratified default): the survivor weighting function is not
pinned in the paper ("admissibility-weighted vote"). Working rule:
    weight_i = admissibility_rank(cls(B_i)) * confidence_i
applied only to verifiers that survive the floor. Approved as the default
2026-06-02; may warrant one sentence in Appendix A.
"""
from __future__ import annotations

from rails_ref.admissibility import Class, cls_join, meets_floor
from rails_ref.objects import (
    ObligationObject, VerifierOutput, Verdict, ClearingDecision, Finality,
)

# admissibility rank — used ONLY as a tie-break weight inside the vote,
# never for ordering decisions (those go through the poset).
_RANK = {
    Class.SELF: 1, Class.SIGN: 2, Class.WIT: 3, Class.REC: 3,
    Class.ATT: 4, Class.PROOF: 5,
}


def _not_emitted(o: ObligationObject, cls_basis: Class, reason: str) -> ClearingDecision:
    return ClearingDecision(
        o.id, Verdict.ABSTAIN, Verdict.ABSTAIN, cls_basis, 0.0,
        Finality.NONE, emitted=False, reason=reason,
    )


def clear(o: ObligationObject, outputs: list[VerifierOutput]) -> ClearingDecision:
    """Aggregate verifier outputs under the obligation floor and (maybe) emit."""
    # 1. floor enforcement: drop verifiers whose declared basis is below the floor
    survivors = [v for v in outputs
                 if meets_floor(cls_join(v.declared_basis), o.floor)]
    if not survivors:
        return _not_emitted(o, Class.SELF, "no verifier meets floor")

    # 2. aggregate basis class = join over the SURVIVORS' declared bases
    cls_basis = cls_join([c for v in survivors for c in v.declared_basis])

    # 3. redundant safety: the aggregate basis must meet the floor
    if not meets_floor(cls_basis, o.floor):
        return _not_emitted(o, cls_basis, "aggregate basis below floor")

    # 4. admissibility-weighted vote among survivors (working rule: rank * confidence)
    def w(v: VerifierOutput) -> float:
        return _RANK[cls_join(v.declared_basis)] * v.confidence

    pass_w = sum(w(v) for v in survivors if v.verdict == Verdict.PASS)
    fail_w = sum(w(v) for v in survivors if v.verdict == Verdict.FAIL)
    performance = Verdict.PASS if pass_w >= fail_w else Verdict.FAIL
    # policy violation fires if any surviving verifier reports FAIL
    policy = Verdict.FAIL if fail_w > 0 else Verdict.PASS
    total = pass_w + fail_w
    confidence = (max(pass_w, fail_w) / total) if total else 0.0

    # 5. EMIT — the soundness invariant is asserted here
    assert meets_floor(cls_basis, o.floor), "SOUNDNESS VIOLATION at emission"
    return ClearingDecision(
        o.id, performance, policy, cls_basis, confidence,
        Finality.PROVISIONAL, emitted=True,
    )
