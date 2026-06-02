"""Obligation binding guard: the DOWNGRADE-FLOOR defense.

Binding is rejected unless (a) the proposed floor meets the vetted template
floor and (b) every party to the obligation has signed. A unilateral attempt to
slip in a weaker floor than the template, or a binding missing a signature, is
rejected.
"""
from __future__ import annotations
from collections.abc import Iterable

from rails_ref.admissibility import Class, meets_floor
from rails_ref.objects import ObligationObject


def bind_obligation(proposed: ObligationObject,
                    party_signatures: Iterable[str],
                    template_floor: Class) -> ObligationObject | None:
    """Return the bound obligation, or None if binding is rejected."""
    if not meets_floor(proposed.floor, template_floor):
        return None  # floor weaker than the vetted template
    if not set(proposed.parties).issubset(set(party_signatures)):
        return None  # not all parties signed
    return proposed
