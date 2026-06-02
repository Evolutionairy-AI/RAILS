"""The seven RAILS primitives as typed dataclasses (paper Appendix A.3 shapes).

These carry fields, not exact JSON keys. Two fields on EvidenceItem are
simulation ground-truth and are NEVER visible to verifiers:
  - true_class: the admissibility the item's provenance actually supports
  - reveals_defect: whether this item exposes the obligation's defect
The intake verifier compares claimed_class against true_class; everything
downstream of intake sees only claimed_class.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

from rails_ref.admissibility import Class


class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ABSTAIN = "ABSTAIN"


class Finality(Enum):
    PROVISIONAL = "PROVISIONAL"
    FINAL = "FINAL"
    NONE = "NONE"


@dataclass(frozen=True)
class EvidenceItem:
    kind: str
    claimed_class: Class          # what the item asserts about its own admissibility
    true_class: Class             # ground-truth provenance support (sim-only)
    reveals_defect: bool = False  # ground-truth: does this item expose the defect?
    payload_ref: str = ""


@dataclass
class EvidenceEnvelope:
    obligation_id: str
    items: list[EvidenceItem] = field(default_factory=list)


@dataclass(frozen=True)
class ObligationObject:
    id: str
    floor: Class
    task: str
    acceptance: str
    parties: tuple[str, ...]
    loss_if_bad: float = 0.0   # used by the loss/exposure experiment
    material: bool = True      # is this a financially-material settlement (floor applies)?


@dataclass(frozen=True)
class VerifierOutput:
    verifier_id: str
    verdict: Verdict
    confidence: float
    declared_basis: tuple[Class, ...]  # classes the verifier claims it relied on


@dataclass
class ClearingDecision:
    obligation_id: str
    performance: Verdict
    policy: Verdict
    cls_basis: Class
    confidence: float
    finality: Finality
    emitted: bool              # False => downgraded (UNVERIFIABLE/DISPUTED), no settlement
    reason: str = ""
