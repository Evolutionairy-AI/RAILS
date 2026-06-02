from rails_ref.admissibility import (
    Class, PARTIAL_ORDER, leq, comparable, cls_join, meets_floor,
)


def test_six_classes_exist():
    assert {c.name for c in Class} == {"SELF", "SIGN", "WIT", "REC", "ATT", "PROOF"}


def test_top_and_bottom():
    # PROOF is top: every class <= PROOF; SELF is bottom: SELF <= every class
    for c in Class:
        assert leq(c, Class.PROOF)
        assert leq(Class.SELF, c)


def test_wit_rec_incomparable():
    assert not comparable(Class.WIT, Class.REC)


def test_join_wit_rec_is_att():
    # the paper's worked example: cls({WIT-ish, REC-ish}) = ATT
    assert cls_join([Class.WIT, Class.REC]) == Class.ATT


def test_join_with_att_and_rec_is_att():
    assert cls_join([Class.ATT, Class.REC]) == Class.ATT


def test_join_empty_is_self():
    assert cls_join([]) == Class.SELF


def test_join_self_proof_is_proof():
    assert cls_join([Class.SELF, Class.PROOF]) == Class.PROOF


def test_antisymmetry_and_reflexivity():
    for a in Class:
        assert leq(a, a)
        for b in Class:
            if leq(a, b) and leq(b, a):
                assert a == b


def test_transitivity():
    cs = list(Class)
    for a in cs:
        for b in cs:
            for c in cs:
                if leq(a, b) and leq(b, c):
                    assert leq(a, c)


def test_meets_floor():
    assert meets_floor(Class.ATT, Class.REC)      # ATT >= REC
    assert meets_floor(Class.PROOF, Class.ATT)
    assert meets_floor(Class.ATT, Class.ATT)
    assert not meets_floor(Class.SELF, Class.ATT)
    assert not meets_floor(Class.WIT, Class.ATT)  # WIT < ATT, incomparable to REC
