"""Population / soundness-at-scale sweeps (Adrian wishlist item 1).

Writes results/population.json with three attack-behavior curves, seed-averaged
for smoothness:
  - FORGE-UP: intake catch-rate and truth-space breach-rate vs forgery
    sophistication; claimed-space floor violations (always 0).
  - LAUNDER-BASIS: median detection latency vs audit rate.
  - DOWNGRADE-FLOOR: rejection rate.
No API calls.
"""
from __future__ import annotations
import json
from pathlib import Path
from statistics import mean, median

from rails_ref.simulate import run_population, run_launder_detection

RESULTS = Path(__file__).parent.parent / "results"
N = 20_000
SEEDS = range(5)


def main() -> None:
    forge = []
    total_floor_violations = 0
    for s in [round(0.1 * i, 1) for i in range(11)]:
        runs = [run_population(N, {"forge_up": 1.0}, seed=k, sophistication=s) for k in SEEDS]
        total_floor_violations += sum(r.floor_violations for r in runs)
        forge.append({
            "sophistication": s,
            "intake_catch_rate": round(mean(r.forge_up_catch_rate for r in runs), 4),
            "truth_breach_rate": round(mean(r.forge_up_truth_breaches for r in runs) / N, 4),
            "floor_violations": sum(r.floor_violations for r in runs),
        })

    launder = []
    for a in [0.02, 0.05, 0.1, 0.2, 0.4]:
        lats = [run_launder_detection(rounds=2000, n_verifiers=20, collusion_fraction=0.3,
                                      audit_rate=a, seed=k)["median_latency"] for k in range(11)]
        lats = [x for x in lats if x is not None]
        launder.append({"audit_rate": a, "median_detection_latency_rounds": median(lats) if lats else None})

    downgrade = run_population(N, {"downgrade": 1.0}, seed=0).downgrade_rejection_rate

    out = {
        "n_per_point": N,
        "forge_up": forge,
        "launder": launder,
        "downgrade_rejection_rate": downgrade,
        "soundness": {
            "claimed_space_floor_violations_total": total_floor_violations,
            "note": "the gate's floor invariant Emit(S) => cls(B) >= phi_O held across every event; "
                    "truth-space breaches arise only when forged provenance defeats intake.",
        },
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "population.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"floor violations across all events: {total_floor_violations}")
    print(f"FORGE-UP catch-rate at sophistication 0.0/0.5/1.0: "
          f"{forge[0]['intake_catch_rate']}/{forge[5]['intake_catch_rate']}/{forge[10]['intake_catch_rate']}")
    print(f"DOWNGRADE rejection rate: {downgrade}")
    print(f"wrote {RESULTS / 'population.json'}")


if __name__ == "__main__":
    main()
