"""Loss/exposure figure — defective-settlement exposure per 10k settlements on
the self-report-only slice: no-clearing baseline (LLM judge alone) vs RAILS."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from figures._style import save, GREY, GOLD

RESULTS = Path(__file__).parent.parent / "results"


def make() -> None:
    d = json.loads((RESULTS / "loss.json").read_text())
    models = d["models"]
    names = [m["model"].split("/")[-1] for m in models]
    base = [m["self_report_slice"]["baseline_judge"]["loss_usd_per_10k"] for m in models]
    rails = [m["self_report_slice"]["rails"]["loss_usd_per_10k"] for m in models]
    x = np.arange(len(models)); w = 0.35

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    fig.patch.set_facecolor("#F8F4EC"); ax.set_facecolor("#F8F4EC")
    ax.bar(x - w / 2, base, w, label="no-clearing baseline (LLM judge alone)", color=GREY)
    ax.bar(x + w / 2, rails, w, label="RAILS", color=GOLD)
    for xi, v in zip(x - w / 2, base):
        ax.text(xi, v + max(base) * 0.01 + 500, f"${v:,.0f}", ha="center", fontsize=9)
    for xi, v in zip(x + w / 2, rails):
        ax.text(xi, v + max(base) * 0.01 + 500, f"${v:,.0f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("cleared-defective exposure, USD per 10k settlements")
    a = d["assumptions"]
    ax.set_title(f"Exposure on self-report-only settlements\n"
                 f"(defect rate {a['defect_rate']:.0%}, ${a['loss_per_bad_usd']:.0f} avg loss)")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    save(fig, "fig_loss")


if __name__ == "__main__":
    make()
