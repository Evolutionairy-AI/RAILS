from rails_ref.dataset import load_cases


def test_dataset_loaded_and_labeled():
    cases = load_cases()
    assert len(cases) >= 150
    assert all(c.label in ("clean", "defective") for c in cases)
    sub_floor = [c for c in cases if c.label == "defective" and c.deception == "sub_floor"]
    assert len(sub_floor) >= 30


def test_sub_floor_defectives_revealed_by_att_evidence():
    for c in load_cases():
        if c.deception == "sub_floor":
            revealing = [it for it in c.items if it.reveals_defect]
            assert revealing, c.id
            assert all(it.claimed_class.name == "ATT" for it in revealing), c.id


def test_clean_cases_have_no_revealing_item():
    for c in load_cases():
        if c.label == "clean":
            assert not any(it.reveals_defect for it in c.items), c.id
