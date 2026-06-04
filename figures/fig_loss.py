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
    base_model = base["model"]

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    fig.patch.set_facecolor(IVORY); ax.set_facecolor(IVORY)
    ax.margins(y=0.14)

    # card-dispute lower-anchor band (~0.5-1%); labelled at the top so it never
    # collides with the curve or the per-point value labels (the source anchors and
    # the approval-impact pairing live in the report caption / prose, not the image)
    ax.axvspan(0.5, 1.0, color=GREY, alpha=0.16, zorder=0)
    ax.text(0.75, max(base_exp) * 1.0, "card-dispute\nrate (~0.5-1%)", fontsize=8,
            color=NAVY, ha="left", va="top")

    ax.fill_between(xs, rails_exp, base_exp, color=TERRA, alpha=0.12, zorder=1)
    flagship = " current flagship" if base.get("is_current_flagship") else ""
    ax.plot(xs, base_exp, "-o", color=TERRA, lw=2, zorder=3,
            label=f"permissive{flagship} judge ({base_model.split('/')[-1]}, {base['sub_floor_false_clear_rate']:.0%} false-clear)")
    ax.plot(xs, rails_exp, "-o", color=GOLD, lw=2, zorder=3, label="RAILS (floor enforcement, $0)")
    for x, v in zip(xs, base_exp):
        ax.annotate(f"${v/1000:.0f}k", (x, v), textcoords="offset points", xytext=(0, 8),
                    fontsize=8, color=NAVY, ha="center")

    ax.set_xlabel("defect rate among agent settlements (%, swept — no single asserted rate)")
    ax.set_ylabel("cleared-defective exposure, USD per 10k settlements")
    ax.set_title("Exposure of inadmissible-evidence settlements that clear\n"
                 "($200 per defective settlement; permissive current-flagship baseline vs RAILS)", fontsize=11)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(True, color="#E4DCCB", lw=0.7)
    fig.tight_layout()
    save(fig, "fig_loss")


if __name__ == "__main__":
    make()
