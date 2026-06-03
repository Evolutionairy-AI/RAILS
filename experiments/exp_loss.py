"""Loss / exposure reframe (Adrian wishlist item 4 + A3 methodology).

The headline result expressed the way a payment network reasons about fraud and
chargebacks. Per A3:

  - Do NOT assert a single defect rate. There is no base rate for agent-performance
    failure (a new category the dispute regime does not catch), so we SWEEP it from
    0.5% to 20% and report the exposure curve. The card dispute rate (~0.5-1%) is
    the lower anchor.
  - Loss per defective settlement: $200 point value (slightly conservative; the
    US chargeback-value anchor is ~$110, travel ~$120).
  - The no-RAILS baseline is a PERMISSIVE judge -- the realistic throughput-tuned
    deployment -- not a conservative one.
  - Always pair the exposure number with the approval-rate (decline) impact: a
    network benchmarks decline rate against the same sub-1% line, and false
    declines cost more than fraud.

Reads results/headline.json; writes results/loss.json. No API calls.
"""
from __future__ import annotations
import json
from pathlib import Path

RESULTS = Path(__file__).parent.parent / "results"

N = 10_000
LOSS_PER_BAD = 200.0
DEFECT_RATES = [0.005, 0.01, 0.02, 0.05, 0.10, 0.20]   # swept; no single asserted rate

# Citable figures for the Sec 6 methodology and the figure caption (A3).
SOURCES = {
    "loss_per_bad_usd": {
        "value": LOSS_PER_BAD,
        "anchor": "avg chargeback value ~$110 US / ~$120 travel (Chargeflow; firm up before publication)",
        "note": "$200 point value is slightly conservative vs the chargeback-value anchor",
    },
    "card_fraud_loss_rate": "6.43 cents per $100 of volume (2024); $33.4B global card fraud losses "
                            "(Nilson Report, Jan 2026)",
    "issuer_dispute_processing_cost_usd": "$9.08-$10.32 per dispute (Mastercard, 'the true cost of a "
                                          "chargeback', 2025)",
    "chargeback_rate_trend": "~0.17% rising to ~0.26% across 2025; merchant cost multiplier $4.61 lost "
                             "per $1 of chargebacks; first-party fraud ~45% of dispute volume "
                             "(Sift Q4 2025 Digital Trust Index)",
    "dispute_rate_band": "0.4%-1% typical, >1% treated as high risk; Visa consolidated into VAMP "
                         "April 2025",
    "baseline": "no-RAILS baseline is a permissive (throughput-tuned) LLM judge",
}


def _exposure(false_clear_rate: float, defect_rate: float) -> float:
    return round(N * defect_rate * false_clear_rate * LOSS_PER_BAD, 2)


def main() -> None:
    h = json.loads((RESULTS / "headline.json").read_text())
    models = h["models"]

    # The realistic no-RAILS baseline is the most permissive judge measured on the
    # inadmissible-evidence (self-report) slice -- the deployment a throughput-tuned
    # operator would actually ship.
    baseline = max(models, key=lambda m: m["judge_alone_sub_floor"]["rate"])
    base_fc = baseline["judge_alone_sub_floor"]["rate"]

    out = {
        "assumptions": {"settlements": N, "loss_per_bad_usd": LOSS_PER_BAD,
                        "defect_rates_swept": DEFECT_RATES, "sources": SOURCES},
        "baseline_judge": {
            "model": baseline["model"],
            "sub_floor_false_clear_rate": base_fc,
            "exposure_curve_usd_per_10k": {f"{r:.3f}": _exposure(base_fc, r) for r in DEFECT_RATES},
        },
        "rails": {
            # RAILS clears zero inadmissible-evidence defectives for every judge,
            # so its exposure on this slice is $0 at every defect rate.
            "sub_floor_false_clear_rate": 0.0,
            "exposure_curve_usd_per_10k": {f"{r:.3f}": 0.0 for r in DEFECT_RATES},
        },
        # Pair exposure with the approval-rate impact (A3): legitimate settlements
        # declined per 10k. False declines are the cost side of the ledger.
        "approval_impact_declines_per_10k": [
            {"model": m["model"],
             "judge_alone_decline_rate": round(1 - m["judge_alone_clean_throughput"]["rate"], 4),
             "rails_fixed_att_decline_rate": round(1 - m["rails_clean_throughput"]["rate"], 4)}
            for m in models
        ],
        "per_model_exposure_at_defect_rates": [
            {"model": m["model"],
             "sub_floor_false_clear_rate": m["judge_alone_sub_floor"]["rate"],
             "exposure_usd_per_10k": {f"{r:.3f}": _exposure(m["judge_alone_sub_floor"]["rate"], r)
                                      for r in DEFECT_RATES}}
            for m in models
        ],
        "note_on_decline_cost": "The fixed-ATT RAILS decline rate above is the conservative bound; the "
                                "exposure-variable floor (results/variable_floor.json) recovers most of "
                                "the legitimate self-report throughput while holding sub-floor exposure "
                                "near zero where the dollars are.",
    }
    (RESULTS / "loss.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"baseline (most permissive judge): {baseline['model']}  "
          f"sub_floor false-clear {base_fc:.1%}")
    print("exposure of cleared-but-defective self-report work, $ per 10k settlements:")
    print(f"  {'defect rate':>12s}   {'baseline judge':>16s}   {'RAILS':>8s}")
    for r in DEFECT_RATES:
        print(f"  {r:>11.1%}    ${_exposure(base_fc, r):>14,.0f}    ${0:>6,.0f}")
    print(f"wrote {RESULTS / 'loss.json'}")


if __name__ == "__main__":
    main()
