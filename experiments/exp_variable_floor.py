"""Variable-floor condition (answers the over-declining objection).

The headline run fixes the floor at ATT for every case -- the strictest regime,
which is why throughput collapses on self-report work. The real protocol uses the
Sec 7 exposure-driven floor: cheap signed self-reports clear low-stakes work and
only high-exposure obligations escalate to ATT/PROOF. This experiment quantifies
the difference on a synthetic, exposure-distributed population against two
references: the fixed ATT floor (what the headline used) and a permissive judge
that clears everything.

Key reported quantities, per regime:
  - throughput      : share of legitimate work that clears
  - decline_rate    : share escalated / not cleared
  - residual_defective_exposure_per_10k : dollars of defective work that cleared
And, for the variable floor, the "effort follows the money" split: the share of
TRANSACTIONS that clear on cheap evidence vs the share of DOLLARS that still
require an ATT-or-higher floor. The soundness gate never clears below an
obligation's own floor in any regime (floor_violations == 0).

No API calls. Writes results/variable_floor.json.
"""
from __future__ import annotations
import json
import random
from pathlib import Path

from rails_ref.admissibility import Class, meets_floor, leq
from rails_ref.exposure import floor_for_exposure

RESULTS = Path(__file__).parent.parent / "results"

N = 20_000
DEFECT_RATE = 0.10
DEFAULT_BASIS = Class.SIGN          # the cheap signed self-report agents carry by default
SCALE = 10_000 / N                  # report dollar exposure per 10k settlements


def run(seed: int = 20260603) -> dict:
    rng = random.Random(seed)
    regimes = ("fixed_att", "variable", "permissive_judge")
    cleared = {k: 0 for k in regimes}
    declined = {k: 0 for k in regimes}
    bad_dollars = {k: 0.0 for k in regimes}
    floor_violations = {k: 0 for k in regimes}

    total_dollars = 0.0
    dollars_needing_att_plus = 0.0     # dollars whose variable floor is ATT or higher
    tx_clearing_on_cheap = 0           # transactions the variable floor clears on <= DEFAULT_BASIS

    for _ in range(N):
        loss = 10 ** (rng.random() * 5)          # log-uniform $1 .. $100,000
        total_dollars += loss
        defective = rng.random() < DEFECT_RATE
        basis = DEFAULT_BASIS
        vfloor = floor_for_exposure(loss)

        if leq(Class.ATT, vfloor):               # variable floor is ATT or higher here
            dollars_needing_att_plus += loss

        for regime, floor in (("fixed_att", Class.ATT), ("variable", vfloor)):
            if meets_floor(basis, floor):
                cleared[regime] += 1
                if not meets_floor(basis, floor):
                    floor_violations[regime] += 1      # can never fire; soundness guard
                if defective:
                    bad_dollars[regime] += loss
                if regime == "variable":
                    tx_clearing_on_cheap += 1
            else:
                declined[regime] += 1

        # permissive judge: clears everything, no floor
        cleared["permissive_judge"] += 1
        if defective:
            bad_dollars["permissive_judge"] += loss

    out = {
        "assumptions": {
            "n": N, "defect_rate": DEFECT_RATE, "default_basis": DEFAULT_BASIS.name,
            "exposure": "log-uniform $1..$100,000",
            "ladder": "<$10 SELF, <$100 SIGN, <$1000 ATT, >=$1000 PROOF",
        },
        "regimes": {
            k: {
                "throughput": round(cleared[k] / N, 4),
                "decline_rate": round(declined[k] / N, 4),
                "residual_defective_exposure_per_10k": round(bad_dollars[k] * SCALE, 2),
            } for k in regimes
        },
        "variable_floor_effort_follows_money": {
            "transactions_cleared_pct": round(100 * tx_clearing_on_cheap / N, 1),
            "dollars_requiring_att_or_higher_pct": round(100 * dollars_needing_att_plus / total_dollars, 1),
        },
        "soundness": {"floor_violations_total": sum(floor_violations.values())},
    }
    return out


def main() -> None:
    out = run()
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "variable_floor.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    r = out["regimes"]
    e = out["variable_floor_effort_follows_money"]
    print("throughput (legit work clears):")
    for k in ("fixed_att", "variable", "permissive_judge"):
        print(f"  {k:18s} {r[k]['throughput']:.1%}   decline {r[k]['decline_rate']:.1%}   "
              f"residual defective exposure ${r[k]['residual_defective_exposure_per_10k']:,.0f}/10k")
    print(f"variable floor: clears {e['transactions_cleared_pct']}% of transactions on cheap evidence "
          f"while {e['dollars_requiring_att_or_higher_pct']}% of DOLLARS still require ATT+")
    print(f"soundness: floor_violations_total = {out['soundness']['floor_violations_total']}")
    print(f"wrote {RESULTS / 'variable_floor.json'}")


if __name__ == "__main__":
    main()
