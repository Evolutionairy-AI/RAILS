"""Conformance check for the paper's Sec 8.6 / 9.3 interop scenario: a VI-mandated
100W charger procured as 65W clears as a performance failure on admissible (ATT)
evidence, authorization clean, and routes the payment to resolution."""
from rails_ref.admissibility import Class, meets_floor
from rails_ref.objects import Verdict
from experiments.interop_demo import run_scenario, settlement_instruction
from rails_ref.objects import ClearingDecision, Finality


def test_charger_scenario_clears_as_performance_failure():
    o, items, authorization_clean, perf_out, decision, si = run_scenario()
    assert authorization_clean is True                      # VI credential / payment clean
    assert decision.emitted is True                         # verifiable on admissible evidence
    assert decision.performance == Verdict.FAIL             # the 65W-vs-100W mismatch
    assert meets_floor(decision.cls_basis, o.floor)         # cleared on >= ATT basis
    assert si["action"] == "hold_and_route_to_resolution"   # not released to merchant


def test_clean_fulfillment_would_settle():
    clean = ClearingDecision("x", Verdict.PASS, Verdict.PASS, Class.ATT, 0.9, Finality.PROVISIONAL,
                             emitted=True)
    assert settlement_instruction(clean)["action"] == "settle_to_merchant"
