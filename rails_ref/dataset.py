"""Loader for the curated settlement-case dataset.

A Case is one obligation plus the artifact text a judge reads, an evidence
envelope with admissibility classes, and ground-truth labels. `deception`:
  - "sub_floor": the defect is revealed only by high-admissibility (ATT) evidence
    while a low-admissibility (SELF) self-report asserts the work is clean. This
    is the class where RAILS floor enforcement should win.
  - "at_floor": the defect is revealed only by evidence BELOW the obligation floor
    (e.g. WIT) — RAILS cannot catch it at an ATT floor. The honest boundary.
  - "none": clean case.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

from rails_ref.admissibility import Class
from rails_ref.objects import EvidenceItem

_DEFAULT_DIR = Path(__file__).parent.parent / "data" / "curated_cases"


@dataclass
class Case:
    id: str
    task: str
    acceptance: str
    artifact_text: str
    items: list[EvidenceItem]
    label: str            # "clean" | "defective"
    defect_type: str      # "unsanctioned_dependency" | "fabricated_tests" | "scope_drift" | "none"
    deception: str        # "sub_floor" | "at_floor" | "none"
    revealing_kind: str   # evidence kind that reveals the defect ("" if clean)
    floor: Class


def load_cases(directory: Path | str | None = None) -> list[Case]:
    directory = Path(directory) if directory else _DEFAULT_DIR
    cases: list[Case] = []
    for p in sorted(directory.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        items = [EvidenceItem(it["kind"], Class[it["claimed_class"]], Class[it["true_class"]],
                              it["reveals_defect"]) for it in d["items"]]
        cases.append(Case(d["id"], d["task"], d["acceptance"], d["artifact_text"], items,
                          d["label"], d["defect_type"], d["deception"], d["revealing_kind"],
                          Class[d["floor"]]))
    return cases
