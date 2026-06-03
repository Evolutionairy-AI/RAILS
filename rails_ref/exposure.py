"""Exposure-driven floor policy (paper Sec 7).

The soundness invariant always holds against an obligation's floor; what varies by
stakes is the floor HEIGHT, not whether the invariant applies. This ladder is the
ratified default mapping from dollar exposure to admissibility floor: cheap,
low-stakes work clears on cheap evidence, and verification effort escalates with
the money at risk. The rungs are a chain on the exposure axis (WIT/REC are
alternative routes to ATT, not floor heights), so the floor is non-decreasing in
exposure.
"""
from __future__ import annotations

from rails_ref.admissibility import Class

# (exclusive upper bound in USD, floor for exposures below it)
_LADDER = [
    (10.0, Class.SELF),     # micro: a self-report suffices
    (100.0, Class.SIGN),    # low: a signed self-report
    (1000.0, Class.ATT),    # material: an independent attestation
    (float("inf"), Class.PROOF),  # high: a cryptographic proof
]


def floor_for_exposure(loss_usd: float) -> Class:
    """Return the admissibility floor required at a given dollar exposure."""
    for upper, cls in _LADDER:
        if loss_usd < upper:
            return cls
    return Class.PROOF
