"""Loss / exposure reframe (Adrian wishlist item 4).

The same headline result, expressed the way a payment network reasons about
fraud and chargebacks: the no-clearing baseline is the LLM judge alone; exposure
is the dollar value of defective settlements that clear. Reported on the
self-report-only slice (where agents self-attest, the common case) and across
all defective settlements. Modeling assumptions are explicit and conservative.

Reads results/headline.json; writes results/loss.json. No API calls.
"""
from __future__ import annotations
import json
from pathlib import Path

RESULTS = Path(__file__).parent.parent / "results"

N = 10_000               # settlements considered
DEFECT_RATE = 0.10       # share of agent settlements that are defective (modeling assumption)
LOSS_PER_BAD = 200.0     # average loss per cleared-but-defective settlement (worked-scenario figure)


def _exposure(false_clear_rate: float) -> dict:
    bad_cleared = N * DEFECT_RATE * false_clear_rate
    return {"bad_settlements_cleared_per_10k": round(bad_cleared, 1),
            "loss_usd_per_10k": round(bad_cleared * LOSS_PER_BAD, 2)}


def _reduction(base: float, rails: float):
    return round(1 - rails / base, 4) if base > 0 else None


def main() -> None:
    h = json.loads((RESULTS / "headline.json").read_text())
    out = {
        "assumptions": {"settlements": N, "defect_rate": DEFECT_RATE,
                        "loss_per_bad_usd": LOSS_PER_BAD,
                        "baseline": "no-clearing baseline is the LLM judge alone"},
        "models": [],
    }
    for m in h["models"]:
        ja_sf = m["judge_alone_sub_floor"]["rate"]
        ra_sf = m["rails_sub_floor"]["rate"]
        ja_all = m["judge_alone_all_defective"]["rate"]
        ra_all = m["rails_all_defective"]["rate"]
        out["models"].append({
            "model": m["model"],
            "self_report_slice": {
                "baseline_judge": _exposure(ja_sf),
                "rails": _exposure(ra_sf),
                "exposure_reduction": _reduction(ja_sf, ra_sf),
            },
            "all_defective": {
                "baseline_judge": _exposure(ja_all),
                "rails": _exposure(ra_all),
                "exposure_reduction": _reduction(ja_all, ra_all),
            },
        })
    (RESULTS / "loss.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    for m in out["models"]:
        s = m["self_report_slice"]
        print(f"{m['model']}  self-report slice: "
              f"baseline ${s['baseline_judge']['loss_usd_per_10k']:,.0f} -> "
              f"RAILS ${s['rails']['loss_usd_per_10k']:,.0f} per 10k "
              f"(exposure reduction {s['exposure_reduction']})")
    print(f"wrote {RESULTS / 'loss.json'}")


if __name__ == "__main__":
    main()
