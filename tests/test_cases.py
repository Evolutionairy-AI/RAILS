import statistics

from rails_ref.admissibility import meets_floor
from rails_ref.dataset import load_cases


def test_dataset_loaded_and_labeled():
    cases = load_cases()
    assert len(cases) >= 180  # v2 synthetic set; real cases only add to this
    assert all(c.label in ("clean", "defective") for c in cases)
    sub_floor_def = [c for c in cases if c.label == "defective" and c.deception == "sub_floor"]
    assert len(sub_floor_def) >= 60


def test_sub_floor_cases_have_only_inadmissible_evidence():
    # the whole point: nothing in the envelope meets the floor, so RAILS must abstain
    for c in load_cases():
        if c.deception in ("sub_floor", "sub_floor_clean"):
            assert all(not meets_floor(it.claimed_class, c.floor) for it in c.items), c.id


def test_admissible_defectives_revealed_by_att():
    for c in load_cases():
        if c.deception == "admissible":
            rev = [it for it in c.items if it.reveals_defect]
            assert rev and all(it.claimed_class.name == "ATT" for it in rev), c.id


def test_clean_cases_have_no_revealing_item():
    for c in load_cases():
        if c.label == "clean":
            assert not any(it.reveals_defect for it in c.items), c.id


# --- v2 dataset-integrity contract: the three fixes the rebuild had to enforce ---
# These guard the SYNTHETIC set (hand-labelled real rows are exempt, source=="real").

def _synthetic():
    return [c for c in load_cases() if c.source == "synthetic"]


def test_no_byte_identical_prompts():
    # v1 had duplicates (case_0000 == case_0003); v2 must have none anywhere.
    prompts = [c.artifact_text for c in _synthetic()]
    assert len(prompts) == len(set(prompts))


def test_sub_floor_diversity():
    # >= 20 distinct tasks and a distinct-scenario count well above the old ~8,
    # so a skeptic cannot dismiss the headline as a handful of resampled items.
    sub_def = [c for c in _synthetic() if c.deception == "sub_floor" and c.label == "defective"]
    assert len({c.task for c in sub_def}) >= 20
    assert len({c.scenario_key for c in sub_def}) >= 48


def test_sub_floor_matched_twins():
    # Clean sub_floor scenarios must reappear as defective twins, so the only
    # difference is the hidden outcome: the text cannot encode the label.
    syn = _synthetic()
    clean_keys = {c.scenario_key for c in syn if c.deception == "sub_floor_clean"}
    def_keys = {c.scenario_key for c in syn if c.deception == "sub_floor" and c.label == "defective"}
    assert clean_keys and clean_keys <= def_keys


def test_sub_floor_no_length_tell():
    # Prompt length must not predict the label (a surface tell would be a confound).
    syn = _synthetic()
    d = [len(c.artifact_text) for c in syn if c.deception == "sub_floor" and c.label == "defective"]
    cl = [len(c.artifact_text) for c in syn if c.deception == "sub_floor_clean"]
    assert abs(statistics.mean(d) - statistics.mean(cl)) < 25
