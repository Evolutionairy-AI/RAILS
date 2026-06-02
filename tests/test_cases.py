from rails_ref.admissibility import meets_floor
from rails_ref.dataset import load_cases


def test_dataset_loaded_and_labeled():
    cases = load_cases()
    assert len(cases) >= 150
    assert all(c.label in ("clean", "defective") for c in cases)
    sub_floor_def = [c for c in cases if c.label == "defective" and c.deception == "sub_floor"]
    assert len(sub_floor_def) >= 30


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
