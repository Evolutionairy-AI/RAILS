from rails_ref.simulate import run_population, run_launder_detection
from rails_ref.metrics import wilson_ci


def test_population_floor_never_violated_and_reproducible():
    mix = {"forge_up": 0.3, "launder": 0.3, "downgrade": 0.2}
    r1 = run_population(n=5000, attack_mix=mix, seed=7)
    r2 = run_population(n=5000, attack_mix=mix, seed=7)
    assert r1.floor_violations == 0          # the gate never emits below the floor
    assert r1.summary() == r2.summary()       # deterministic given the seed
    assert 0.0 <= r1.forge_up_catch_rate <= 1.0


def test_downgrade_always_rejected():
    r = run_population(n=2000, attack_mix={"downgrade": 1.0}, seed=1)
    assert r.downgrade_attempts > 0
    assert r.downgrade_rejection_rate == 1.0


def test_forge_up_catch_rate_tracks_sophistication():
    lo = run_population(n=4000, attack_mix={"forge_up": 1.0}, seed=2, sophistication=0.0)
    hi = run_population(n=4000, attack_mix={"forge_up": 1.0}, seed=2, sophistication=0.8)
    assert lo.forge_up_catch_rate > 0.95          # at zero sophistication, ~all forgeries caught
    assert lo.forge_up_truth_breaches == 0        # nothing slips through
    assert hi.forge_up_catch_rate < lo.forge_up_catch_rate
    assert hi.forge_up_truth_breaches > 0         # some forgeries slip -> truth-space breaches


def test_floor_holds_even_at_high_sophistication():
    # the CLAIMED-space gate invariant holds regardless; only TRUTH-space breaches rise
    r = run_population(n=4000, attack_mix={"forge_up": 1.0, "launder": 0.5}, seed=5, sophistication=0.9)
    assert r.floor_violations == 0


def test_wilson_ci_bounds():
    lo, hi = wilson_ci(30, 100)
    assert 0.0 <= lo < 0.30 < hi <= 1.0


def test_launder_all_detected_with_enough_audits():
    r = run_launder_detection(rounds=2000, n_verifiers=10, collusion_fraction=0.3,
                              audit_rate=0.4, seed=1)
    assert r["detected"] == r["colluders"]
    assert all(latency > 0 for latency in r["latencies"])


def test_launder_audit_rate_affects_detection():
    lo = run_launder_detection(rounds=60, audit_rate=0.02, collusion_fraction=0.3, seed=3)
    hi = run_launder_detection(rounds=60, audit_rate=0.6, collusion_fraction=0.3, seed=3)
    assert hi["detected"] >= lo["detected"]
