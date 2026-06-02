"""Spec-conformance suite: one test per empirical claim the paper makes, tying
the committed results to checks a third party can re-run."""
import json
from pathlib import Path

from rails_ref.simulate import run_population, run_launder_detection

RESULTS = Path(__file__).parent.parent / "results"


def test_soundness_floor_invariant_at_scale():
    # Emit(S) => cls(B) >= phi_O holds across a mixed adversarial population
    r = run_population(20000, {"forge_up": 0.5, "launder": 0.5, "downgrade": 0.5},
                       seed=99, sophistication=0.7)
    assert r.floor_violations == 0


def test_forge_up_catch_monotone_in_sophistication():
    lo = run_population(8000, {"forge_up": 1.0}, seed=1, sophistication=0.1)
    hi = run_population(8000, {"forge_up": 1.0}, seed=1, sophistication=0.9)
    assert lo.forge_up_catch_rate > hi.forge_up_catch_rate


def test_launder_colluders_eventually_detected():
    d = run_launder_detection(2000, n_verifiers=20, collusion_fraction=0.3, audit_rate=0.3, seed=2)
    assert d["detected"] == d["colluders"]


def test_downgrade_rejected():
    r = run_population(5000, {"downgrade": 1.0}, seed=3)
    assert r.downgrade_rejection_rate == 1.0


def test_headline_claims_hold():
    h = json.loads((RESULTS / "headline.json").read_text())
    # RAILS clears zero inadmissible-evidence defectives, for EVERY judge
    for m in h["models"]:
        assert m["rails_sub_floor"]["rate"] == 0.0, m["model"]
    # the divergence: at least one judge clears a material fraction, at least one near zero
    sub = [m["judge_alone_sub_floor"]["rate"] for m in h["models"]]
    assert max(sub) >= 0.5 and min(sub) <= 0.1
