"""Synthetic adversarial population (RAILS soundness-at-scale study).

run_population generates many synthetic clearing events, a configurable fraction
under each per-event attack family (FORGE-UP, DOWNGRADE-FLOOR, and a single-round
LAUNDER-BASIS injection), runs them through the real clearing core, and records:

  - floor_violations: claimed-space gate-invariant breaches (must be 0 — the gate
    guarantees this; reported for completeness, NOT the headline result).
  - forge_up_catch_rate: fraction of forged items downgraded at intake.
  - forge_up_truth_breaches: emitted decisions whose claimed basis met the floor
    only because a forgery passed intake while its TRUE provenance is sub-floor.
    This is the non-tautological FORGE-UP curve (rises with sophistication).
  - downgrade_rejection_rate: fraction of binding downgrade attempts rejected.
  - false_clears: emitted PASS-performance on a defective obligation.

LAUNDER-BASIS detection is inherently temporal; run_launder_detection runs the
multi-round study that yields detection latency.
"""
from __future__ import annotations
import random
from dataclasses import dataclass

from rails_ref.admissibility import Class, meets_floor
from rails_ref.objects import (
    ObligationObject, EvidenceEnvelope, EvidenceItem, VerifierOutput, Verdict,
)
from rails_ref.intake import admit
from rails_ref.verifiers import PolicyVerifier, NaiveVerifier
from rails_ref.attacks import forge_up_item, downgrade_floor, launder_basis_output
from rails_ref.binding import bind_obligation
from rails_ref.mesh import clear

FLOOR = Class.ATT            # material obligations require an ATT floor (worked-scenario default)
TEMPLATE_FLOOR = Class.ATT
LOSS = 200.0


class _ForgeReliantVerifier:
    """Sim-only verifier: when a forged attestation is present it relies on it and
    PASSes, declaring that item's (claimed) class as its basis. If the forgery
    passed intake at ATT, this verifier's claimed basis meets the floor while its
    true support does not."""
    verifier_id = "forge_reliant"

    def verify(self, oid: str, env: EvidenceEnvelope) -> VerifierOutput:
        forged = next((it for it in env.items if it.kind == "forged_attestation"), None)
        if forged:
            return VerifierOutput(self.verifier_id, Verdict.PASS, 0.85, (forged.claimed_class,))
        return VerifierOutput(self.verifier_id, Verdict.ABSTAIN, 0.0, (Class.SELF,))


@dataclass
class PopulationResult:
    n: int
    emissions: int
    floor_violations: int
    forged: int
    forge_up_caught: int
    forge_up_truth_breaches: int
    downgrade_attempts: int
    downgrade_rejected: int
    false_clears: int
    seed: int
    sophistication: float

    @property
    def forge_up_catch_rate(self) -> float:
        return (self.forge_up_caught / self.forged) if self.forged else 1.0

    @property
    def downgrade_rejection_rate(self) -> float:
        return (self.downgrade_rejected / self.downgrade_attempts) if self.downgrade_attempts else 1.0

    def summary(self) -> dict:
        return {
            "n": self.n,
            "emissions": self.emissions,
            "floor_violations": self.floor_violations,
            "forge_up_catch_rate": round(self.forge_up_catch_rate, 6),
            "forge_up_truth_breaches": self.forge_up_truth_breaches,
            "downgrade_rejection_rate": round(self.downgrade_rejection_rate, 6),
            "false_clears": self.false_clears,
            "sophistication": self.sophistication,
        }


def run_population(n: int, attack_mix: dict, seed: int, sophistication: float = 0.0) -> PopulationResult:
    rng = random.Random(seed)
    pf = attack_mix.get("forge_up", 0.0)
    pl = attack_mix.get("launder", 0.0)
    pd = attack_mix.get("downgrade", 0.0)

    policy = PolicyVerifier(watch_kind="pkg_delta")
    naive = NaiveVerifier(relies_on_kind="self_report")
    forge_v = _ForgeReliantVerifier()

    emissions = floor_violations = forged = caught = truth_breaches = 0
    downgrade_attempts = downgrade_rejected = false_clears = 0

    for i in range(n):
        defective = rng.random() < 0.5
        items = [EvidenceItem("self_report", Class.SELF, Class.SELF, reveals_defect=False)]
        if defective:
            items.append(EvidenceItem("pkg_delta", Class.ATT, Class.ATT, reveals_defect=True))

        this_forged = rng.random() < pf
        forged_item = None
        if this_forged:
            forged_item = forge_up_item(Class.ATT, rng)
            items.append(forged_item)
            forged += 1

        o = ObligationObject(f"o{i}", FLOOR, "task", "acc", ("acme", "provider"), loss_if_bad=LOSS)

        if rng.random() < pd:
            downgrade_attempts += 1
            attempt = downgrade_floor(o, to=Class.SELF)
            if bind_obligation(attempt, {"acme", "provider"}, TEMPLATE_FLOOR) is None:
                downgrade_rejected += 1

        admitted = [admit(it, sophistication, rng) for it in items]
        forged_passed = this_forged and any(
            it.kind == "forged_attestation" and it.claimed_class == Class.ATT for it in admitted)
        if this_forged and not forged_passed:
            caught += 1

        env = EvidenceEnvelope(o.id, admitted)
        outs = [policy.verify(o.id, env), naive.verify(o.id, env)]
        if forged_passed:
            outs.append(forge_v.verify(o.id, env))
        if rng.random() < pl:
            outs.append(launder_basis_output("v_launder", o.floor, true_consulted=Class.SELF))

        d = clear(o, outs)
        if d.emitted:
            emissions += 1
            if not meets_floor(d.cls_basis, o.floor):
                floor_violations += 1  # claimed-space breach — must never happen
            if forged_passed and forged_item is not None and not meets_floor(forged_item.true_class, o.floor):
                truth_breaches += 1
            if defective and d.performance == Verdict.PASS:
                false_clears += 1

    return PopulationResult(n, emissions, floor_violations, forged, caught, truth_breaches,
                            downgrade_attempts, downgrade_rejected, false_clears, seed, sophistication)


def run_launder_detection(rounds: int, n_verifiers: int = 10, collusion_fraction: float = 0.3,
                          audit_rate: float = 0.2, defect_rate: float = 0.5,
                          detect_threshold: float = 0.25, min_samples: int = 8,
                          seed: int = 0) -> dict:
    """Multi-round LAUNDER-BASIS study. Colluding verifiers always PASS (favoring
    the attacker) regardless of ground truth; honest verifiers track truth. Each
    round, with probability audit_rate an audit checks one verifier's historical
    disagreement with ground truth and flags it once the disagreement exceeds the
    threshold (with enough samples). Returns per-colluder detection latency."""
    rng = random.Random(seed)
    n_colluders = int(round(n_verifiers * collusion_fraction))
    colluders = set(range(n_colluders))
    wrong = [0] * n_verifiers
    seen = [0] * n_verifiers
    detected_at: dict[int, int] = {}

    for r in range(rounds):
        defective = rng.random() < defect_rate
        correct_pass = not defective
        for i in range(n_verifiers):
            seen[i] += 1
            verdict_pass = True if i in colluders else (not defective)
            if verdict_pass != correct_pass:
                wrong[i] += 1
        if rng.random() < audit_rate:
            cand = rng.randrange(n_verifiers)
            if cand not in detected_at and seen[cand] >= min_samples:
                if wrong[cand] / seen[cand] > detect_threshold:
                    detected_at[cand] = r

    latencies = sorted(detected_at[c] for c in colluders if c in detected_at)
    return {
        "colluders": len(colluders),
        "detected": len(latencies),
        "latencies": latencies,
        "median_latency": (latencies[len(latencies) // 2] if latencies else None),
        "audit_rate": audit_rate,
    }
