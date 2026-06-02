"""Intake verifier: the FORGE-UP defense.

Compares an item's claimed class against its true provenance support. An item
is an OVER-CLAIM when its claimed class is not supported by its provenance
(claimed_class is not <= true_class in Lambda). Over-claims are downgraded to
their true class UNLESS the forgery defeats the provenance check, modeled by
`sophistication` in [0, 1] = P(a given forgery passes intake). Honest items
(claimed_class <= true_class) are admitted unchanged.
"""
from __future__ import annotations
import random
from dataclasses import replace

from rails_ref.admissibility import leq
from rails_ref.objects import EvidenceItem


def is_overclaim(item: EvidenceItem) -> bool:
    """An item over-claims when its provenance does not support its claimed class."""
    return not leq(item.claimed_class, item.true_class)


def admit(item: EvidenceItem, sophistication: float, rng: random.Random) -> EvidenceItem:
    """Return the item as admitted into the envelope (possibly downgraded)."""
    if not is_overclaim(item):
        return item
    if rng.random() < sophistication:
        return item  # forgery passed the provenance check
    return replace(item, claimed_class=item.true_class)  # caught -> downgrade to truth
