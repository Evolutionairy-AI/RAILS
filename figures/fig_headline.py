"""Headline figure — LEADS WITH THE DIVERGENCE between frontier judges, and
RAILS's model-independence. Two panels: (A) false-clear rate on defective work
backed only by a self-report; (B) throughput on legitimate work. In both, the
two judges-alone diverge sharply while RAILS is consistent."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

from figures._style import new_fig, save, TEAL, GOLD, GREY, NAVY

RESULTS = Path(__file__).parent.parent / "results"


def make() -> None:
    h = json.loads((RESULTS / "headline.json").read_text())
    models = h["models"]
    names = [m["model"].split("/")[-1] for m in models]
    x = np.arange(len(models))
    w = 0.35

    import matplotlib.pyplot as plt
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax in (axA, axB):
        ax.set_facecolor("#F8F4EC")
    fig.patch.set_facecolor("#F8F4EC")

    # Panel A: false-clear on self-report-only defective work (lower is better)
    ja = [m["judge_alone_sub_floor"]["rate"] for m in models]
    ra = [m["rails_sub_floor"]["rate"] for m in models]
    axA.bar(x - w / 2, ja, w, label="LLM judge alone", color=GREY)
    axA.bar(x + w / 2, ra, w, label="RAILS", color=GOLD)
    for xi, v in zip(x - w / 2, ja):
        axA.text(xi, v + 0.02, f"{v:.0%}", ha="center", fontsize=9)
    for xi, v in zip(x + w / 2, ra):
        axA.text(xi, v + 0.02, f"{v:.0%}", ha="center", fontsize=9)
    axA.set_xticks(x); axA.set_xticklabels(names)
    axA.set_ylim(0, 1.08); axA.set_ylabel("false-clear rate (lower is better)")
    axA.set_title("A. Defective work, self-report only\n(evidence below the floor)")
    axA.legend(frameon=False, loc="upper right")

    # Panel B: throughput on clean work (higher is better)
    jt = [m["judge_alone_clean_throughput"]["rate"] for m in models]
    rt = [m["rails_clean_throughput"]["rate"] for m in models]
    axB.bar(x - w / 2, jt, w, label="LLM judge alone", color=GREY)
    axB.bar(x + w / 2, rt, w, label="RAILS", color=TEAL)
    for xi, v in zip(x - w / 2, jt):
        axB.text(xi, v + 0.02, f"{v:.0%}", ha="center", fontsize=9)
    for xi, v in zip(x + w / 2, rt):
        axB.text(xi, v + 0.02, f"{v:.0%}", ha="center", fontsize=9)
    axB.set_xticks(x); axB.set_xticklabels(names)
    axB.set_ylim(0, 1.08); axB.set_ylabel("clears legitimate work (higher is better)")
    axB.set_title("B. Legitimate work\n(throughput / specificity)")
    axB.legend(frameon=False, loc="upper right")

    fig.suptitle("The LLM judge is ungoverned and model-dependent; RAILS is not",
                 fontsize=12, color=NAVY)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    save(fig, "fig_headline")


if __name__ == "__main__":
    make()
