"""Loader for the curated settlement-case dataset (v2).

The dataset ships as one JSON object per line in ``data/rails_cases_v2.jsonl``
(see ``data/RAILS_dataset_v2_README.md``), rebuilt to remove the three flaws in
the original curated set: incoherent bug/fix pairs, unmatched clean/defective
prose, and thin/duplicated tasks. Each row carries the exact ``judge_prompt`` a
model receives plus its ground truth; this loader synthesises the structured
evidence envelope RAILS routes on, keyed by ``family``/``evidence_class``:

  - ``sub_floor``  (SELF): a bare self-report, no admissible evidence. RAILS has
    no verifier meeting the ATT floor, so it returns UNVERIFIABLE. This is the
    headline class; a judge-alone false-clear here is the metric surface.
  - ``admissible`` (ATT): a CI log that reflects ground truth (names the two
    failing tests for a defect, green for clean). Both judge and RAILS panel
    should catch defects here.
  - ``at_floor``   (WIT): an informal, unsigned reviewer note that reveals the
    defect but sits BELOW the ATT floor. RAILS excludes it by construction and
    misses; a judge reading everything can catch it. The honest soundness edge.

A ``Case``'s ``deception`` field preserves the vocabulary the experiment and the
digest subset on: defective sub_floor -> "sub_floor"; clean sub_floor ->
"sub_floor_clean"; defective admissible -> "admissible"; defective at_floor ->
"at_floor"; every clean case -> "none".

Real, hand-labelled anonymized rows can be dropped into ``data/real_cases.jsonl``
(same schema); they are appended automatically. Synthetic alone should not carry
the headline percentages unaided.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

from rails_ref.admissibility import Class
from rails_ref.objects import EvidenceItem

_DATA = Path(__file__).parent.parent / "data"
_V2_JSONL = _DATA / "rails_cases_v2.jsonl"
_REAL_JSONL = _DATA / "real_cases.jsonl"   # optional hand-labelled real cases (same schema)


@dataclass
class Case:
    id: str
    task: str
    acceptance: str
    artifact_text: str
    items: list[EvidenceItem]
    label: str            # "clean" | "defective"
    defect_type: str
    deception: str        # "sub_floor" | "sub_floor_clean" | "admissible" | "at_floor" | "none"
    revealing_kind: str   # evidence kind that reveals the defect ("" if clean)
    floor: Class
    scenario_key: str = ""   # (task, fix) identity; matched twins share a key
    source: str = "synthetic"  # "synthetic" | "real"


def _self() -> EvidenceItem:
    return EvidenceItem("self_report", Class.SELF, Class.SELF, False)


def _ci(reveals: bool) -> EvidenceItem:
    return EvidenceItem("ci_log", Class.ATT, Class.ATT, reveals)


def _reviewer_note(reveals: bool) -> EvidenceItem:
    return EvidenceItem("reviewer_note", Class.WIT, Class.WIT, reveals)


def _case_from_row(d: dict, source: str) -> Case:
    family = d["family"]
    label = d["label"]
    defective = label == "defective"
    if family == "sub_floor":
        items = [_self()]
        deception = "sub_floor" if defective else "sub_floor_clean"
        revealing_kind = ""
        defect_type = "false_self_report" if defective else "none"
    elif family == "admissible":
        items = [_self(), _ci(defective)]
        deception = "admissible" if defective else "none"
        revealing_kind = "ci_log" if defective else ""
        defect_type = "att_revealed_defect" if defective else "none"
    elif family == "at_floor":
        items = [_self(), _reviewer_note(defective)]
        deception = "at_floor" if defective else "none"
        revealing_kind = "reviewer_note" if defective else ""
        defect_type = "sub_floor_revealed_defect" if defective else "none"
    else:
        raise ValueError(f"{d['id']}: unknown family {family!r}")
    return Case(
        id=d["id"], task=d["task"], acceptance=d["acceptance_criteria"],
        artifact_text=d["judge_prompt"], items=items, label=label,
        defect_type=defect_type, deception=deception, revealing_kind=revealing_kind,
        floor=Class.ATT, scenario_key=d.get("scenario_key", ""), source=source,
    )


def _read_jsonl(path: Path, source: str) -> list[Case]:
    if not path.exists():
        return []
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(_case_from_row(json.loads(line), source))
    return cases


def load_cases(jsonl_path: Path | str | None = None) -> list[Case]:
    """Load the v2 dataset (synthetic) plus any hand-labelled real rows.

    With no argument: ``data/rails_cases_v2.jsonl`` + ``data/real_cases.jsonl``
    (the latter only if present). Pass a path to load a specific .jsonl instead.
    """
    if jsonl_path is not None:
        return _read_jsonl(Path(jsonl_path), "synthetic")
    return _read_jsonl(_V2_JSONL, "synthetic") + _read_jsonl(_REAL_JSONL, "real")
