"""The three attack-family generators (RAILS threat model, paper Sec 10).

Each generator PRODUCES an attempt to violate the soundness property; the
defenses (intake, the floor gate, the binding guard) are what should defeat it.
The simulation measures whether, and how quickly, they do.
"""
from __future__ import annotations
import random
from dataclasses import replace

from rails_ref.admissibility import Class, leq
from rails_ref.objects import EvidenceItem, ObligationObject, VerifierOutput, Verdict


def forge_up_item(target_class: Class, rng: random.Random,
                  kind: str = "forged_attestation") -> EvidenceItem:
    """FORGE-UP: fabricate an item claiming target_class with provenance that does
    not support it (true_class is some class that does not dominate target_class)."""
    unsupported = [c for c in Class if not leq(target_class, c)]
    if not unsupported:
        raise ValueError("cannot forge up to the bottom class")
    true_class = rng.choice(unsupported)
    return EvidenceItem(kind, claimed_class=target_class, true_class=true_class, reveals_defect=False)


def downgrade_floor(o: ObligationObject, to: Class) -> ObligationObject:
    """DOWNGRADE-FLOOR: attempt to bind the obligation with a weaker floor."""
    return replace(o, floor=to)


def launder_basis_output(verifier_id: str, floor: Class, true_consulted: Class) -> VerifierOutput:
    """LAUNDER-BASIS: a colluding verifier returns PASS and declares an admissible
    basis (>= floor) it did not actually consult (it truly consulted
    `true_consulted`). The lie is invisible in a single round; the simulation
    tracks `true_consulted` separately to measure detection latency over rounds."""
    return VerifierOutput(verifier_id, Verdict.PASS, 0.9, declared_basis=(floor,))
