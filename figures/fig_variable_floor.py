"""Variable-floor figure (answers the over-declining objection). Two panels over
three regimes: (A) throughput on legitimate work, (B) residual defective-dollar
exposure (log scale). The fixed ATT floor over-declines (0% throughput); the
exposure-variable floor recovers low-stakes throughput while holding exposure far
below a permissive judge. Effort follows the money."""
from __future__ import annotations
import json
from pathlib import Path

from figures._style import save, GOLD, GREY, NAVY, IVORY, TERRA

RESULTS = Path(__file__).parent.parent / "results"
ORDER = ["fixed_att", "variable", "permissive_judge"]
LABELS = {"fixed_att": "fixed ATT floor\n(headline run)",
          "variable": "exposure-variable\nfloor (Sec 7)",
          "permissive_judge": "permissive judge\n(no floor)"}
COLORS = {"fixed_att": GREY, "variable": GOLD, "permissive_judge": TERRA}


def make() -> None:
    d = json.loads((RESULTS / "variable_floor.json").read_text())
    reg = d["regimes"]
    e = d["variable_floor_effort_follows_money"]

    import matplotlib.pyplot as plt
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax in (axA, axB):
        ax.set_facecolor(IVORY)
    fig.patch.set_facecolor(IVORY)

    x = list(range(len(ORDER)))
    names = [LABELS[k] for k in ORDER]
    cols = [COLORS[k] for k in ORDER]

    tput = [reg[k]["throughput"] for k in ORDER]
    axA.bar(x, tput, 0.6, color=cols)
    for xi, v in zip(x, tput):
        axA.text(xi, v + 0.02, f"{v:.0%}", ha="center", fontsize=10)
    axA.set_xticks(x); axA.set_xticklabels(names, fontsize=9)
    axA.set_ylim(0, 1.12); axA.set_ylabel("legitimate work cleared (higher is better)")
    axA.set_title("A. Throughput")

    exp = [max(reg[k]["residual_defective_exposure_per_10k"], 1.0) for k in ORDER]
    axB.bar(x, exp, 0.6, color=cols)
    axB.set_yscale("log")
    for xi, v, raw in zip(x, exp, [reg[k]["residual_defective_exposure_per_10k"] for k in ORDER]):
        axB.text(xi, v * 1.3, f"${raw:,.0f}", ha="center", fontsize=9)
    axB.set_xticks(x); axB.set_xticklabels(names, fontsize=9)
    axB.set_ylabel("residual defective exposure per 10k  (log, lower is better)")
    axB.set_title("B. Exposure of cleared-but-defective work")

    fig.suptitle("The exposure-variable floor recovers throughput where it is cheap and "
                 "escalates where the money is", fontsize=12, color=NAVY)
    fig.text(0.5, 0.005,
             f"Variable floor clears {e['transactions_cleared_pct']}% of transactions on cheap "
             f"evidence while {e['dollars_requiring_att_or_higher_pct']}% of dollars still require "
             f"ATT-or-higher.  Soundness: {d['soundness']['floor_violations_total']} floor violations.",
             ha="center", fontsize=9, color=NAVY)
    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    save(fig, "fig_variable_floor")


if __name__ == "__main__":
    make()
