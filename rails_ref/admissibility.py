"""The admissibility partial order Λ (RAILS paper, Fig 5 / Appendix A.1).

A POSET, not a total order: WIT and REC are incomparable. cls(B) is the join
(least upper bound). Working covering relations (confirm against Appendix A.1):

    SELF -> SIGN -> {WIT, REC} -> ATT -> PROOF

so join(WIT, REC) = ATT, matching the paper's worked example
cls({TEE-attested CI log, third-party scanner receipt}) = ATT.
"""
from __future__ import annotations
from enum import Enum


class Class(Enum):
    SELF = "SELF"
    SIGN = "SIGN"
    WIT = "WIT"
    REC = "REC"
    ATT = "ATT"
    PROOF = "PROOF"


# covering relations: node -> set of immediate parents (classes directly above it)
_COVERS = {
    Class.SELF: {Class.SIGN},
    Class.SIGN: {Class.WIT, Class.REC},
    Class.WIT: {Class.ATT},
    Class.REC: {Class.ATT},
    Class.ATT: {Class.PROOF},
    Class.PROOF: set(),
}


def _upset(c: Class) -> set[Class]:
    """All classes >= c (reflexive transitive closure upward)."""
    seen, frontier = {c}, [c]
    while frontier:
        x = frontier.pop()
        for p in _COVERS[x]:
            if p not in seen:
                seen.add(p)
                frontier.append(p)
    return seen


# precompute the full <= relation as up-sets: PARTIAL_ORDER[c] = {everything >= c}
PARTIAL_ORDER = {c: _upset(c) for c in Class}


def leq(a: Class, b: Class) -> bool:
    """True iff a <= b in Λ (a is at most as admissible as b)."""
    return b in PARTIAL_ORDER[a]


def comparable(a: Class, b: Class) -> bool:
    return leq(a, b) or leq(b, a)


def cls_join(classes) -> Class:
    """Least upper bound of a set of classes. Λ is a lattice so this exists.

    The empty set joins to SELF (bottom), the identity for join.
    """
    classes = list(classes)
    if not classes:
        return Class.SELF
    common = set(Class)
    for c in classes:
        common &= PARTIAL_ORDER[c]  # common upper bounds
    least = [u for u in common if all(leq(u, v) for v in common)]
    assert len(least) == 1, f"Lambda is not a lattice for {classes}: candidates {least}"
    return least[0]


def meets_floor(c: Class, floor: Class) -> bool:
    """Admissibility c satisfies obligation floor iff c >= floor."""
    return leq(floor, c)
