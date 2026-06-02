"""Population figure — the non-tautological attack-behavior curves.
Panel A: FORGE-UP intake catch-rate and truth-space breach-rate vs forgery
sophistication, with the claimed-space floor-violation line flat at zero.
Panel B: LAUNDER-BASIS median detection latency vs audit rate."""
from __future__ import annotations
import json
from pathlib import Path

from figures._style import save, TEAL, GOLD, TERRA, NAVY

RESULTS = Path(__file__).parent.parent / "results"


def make() -> None:
    p = json.loads((RESULTS / "population.json").read_text())
    import matplotlib.pyplot as plt
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.2))
    fig.patch.set_facecolor("#F8F4EC")
    for ax in (axA, axB):
        ax.set_facecolor("#F8F4EC")

    f = p["forge_up"]
    s = [r["sophistication"] for r in f]
    catch = [r["intake_catch_rate"] for r in f]
    breach = [r["truth_breach_rate"] for r in f]
    fv = [r["floor_violations"] for r in f]
    axA.plot(s, catch, "-o", color=TEAL, label="intake catch-rate")
    axA.plot(s, breach, "-s", color=TERRA, label="truth-space breach-rate")
    axA.plot(s, fv, "-^", color=GOLD, label="claimed-space floor violations")
    axA.set_xlabel("forgery sophistication σ")
    axA.set_ylabel("rate")
    axA.set_ylim(-0.05, 1.05)
    axA.set_title("A. FORGE-UP: the gate never breaks (gold = 0);\nsoundness degrades in truth-space only as forgery wins")
    axA.legend(frameon=False, fontsize=8, loc="center left")

    lz = p["launder"]
    a = [r["audit_rate"] for r in lz]
    lat = [r["median_detection_latency_rounds"] for r in lz]
    axB.plot(a, lat, "-o", color=NAVY)
    axB.set_xlabel("basis-disclosure audit rate")
    axB.set_ylabel("median detection latency (rounds)")
    axB.set_title("B. LAUNDER-BASIS: colluders are caught,\nlatency shrinks as audits increase")

    fig.tight_layout()
    save(fig, "fig_population")


if __name__ == "__main__":
    make()
