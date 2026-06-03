"""Loss/exposure figure (A3): cleared-but-defective exposure on the inadmissible-
evidence (self-report) slice, swept over the defect rate (no single asserted rate).
Baseline is a permissive judge; RAILS carries $0 on this slice at every defect rate.
The card-dispute rate (~0.5-1%) is shaded as the lower anchor. The exposure number
is paired with the approval-rate impact in the caption, per A3."""
from __future__ import annotations
import json
from pathlib import Path

from figures._style import save, GOLD, TERRA, NAVY, IVORY, GREY

RESULTS = Path(__file__).parent.parent / "results"


def make() -> None:
    d = json.loads((RESULTS / "loss.json").read_text())
    base = d["baseline_judge"]
    rates = [float(k) for k in base["exposure_curve_usd_per_10k"].keys()]
    base_exp = list(base["exposure_curve_usd_per_10k"].values())
    rails_exp = list(d["rails"]["exposure_curve_usd_per_10k"].values())
    xs = [r * 100 for r in rates]   # percent

    # most permissive judge's decline rate, for the approval-impact pairing
    decl = {m["model"]: m for m in d["approval_impact_declines_per_10k"]}
    base_model = base["model"]
    base_decline = decl[base_model]["judge_alone_decline_rate"] if base_model in decl else None

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    fig.patch.set_facecolor(IVORY); ax.set_facecolor(IVORY)

    # card-dispute lower-anchor band (~0.5-1%)
    ax.axvspan(0.5, 1.0, color=GREY, alpha=0.16, zorder=0)
    ax.text(0.75, max(base_exp) * 0.55, "card dispute\nrate (~0.5-1%)", fontsize=8,
            color=NAVY, ha="center", va="center")

    ax.fill_between(xs, rails_exp, base_exp, color=TERRA, alpha=0.12, zorder=1)
    ax.plot(xs, base_exp, "-o", color=TERRA, lw=2, zorder=3,
            label=f"permissive judge ({base_model.split('/')[-1]}, {base['sub_floor_false_clear_rate']:.0%} false-clear)")
    ax.plot(xs, rails_exp, "-o", color=GOLD, lw=2, zorder=3, label="RAILS (floor enforcement)")
    for x, v in zip(xs, base_exp):
        ax.annotate(f"${v/1000:.0f}k", (x, v), textcoords="offset points", xytext=(0, 7),
                    fontsize=8, color=NAVY, ha="center")

    ax.set_xlabel("defect rate among agent settlements (%, swept — no single asserted rate)")
    ax.set_ylabel("cleared-defective exposure, USD per 10k settlements")
    ax.set_title("Exposure of inadmissible-evidence settlements that clear\n"
                 "($200 per defective settlement; permissive baseline vs RAILS)", fontsize=11)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(True, color="#E4DCCB", lw=0.7)

    pair = ""
    if base_decline is not None:
        pair = (f"  Approval-impact pairing: this permissive baseline declines only "
                f"{base_decline:.0%} of legitimate work but carries the exposure above; RAILS' fixed-ATT "
                f"floor over-declines, which the exposure-variable floor recovers (fig_variable_floor).")
    fig.text(0.5, 0.005,
             "Anchors: avg chargeback ~$110 US / $120 travel; card fraud 6.43c per $100 (Nilson 2026); "
             "dispute cost $9-10 (Mastercard 2025)." + pair,
             ha="center", fontsize=7.2, color=NAVY, wrap=True)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    save(fig, "fig_loss")


if __name__ == "__main__":
    make()
