"""A5 scatter: every judge as a point in a safety-vs-throughput plane.

x = throughput   (share of legitimate work the judge clears; higher better)
y = soundness    (1 - false-clear on inadmissible-evidence defectives; higher better)

The judges trace a tradeoff: permissive judges (a current flagship like Mistral
Large, the prior-generation GPT-4.1, the small Gemini 2.5 Flash) buy high throughput
at low soundness; the soundness-safe judges (the Anthropic models, GPT-5.5) buy it by
over-declining, capping throughput near 50%. No judge reaches the top-right governed
corner. RAILS holds the soundness ceiling (y = 1.0, a guaranteed invariant) at
whatever throughput the exposure-variable floor policy targets -- so the whole top
edge is available to RAILS by policy, while the judges are stuck on the frontier
below. The claim is governance, not a benchmark win: the judge's disposition is
model-dependent and ungoverned; RAILS's soundness is proven and model-independent.

Population: this plane is the inadmissible-evidence (sub_floor) slice. x is computed
on the full clean set; y on the sub_floor defectives.

Honest boundary (kept visible, per A9): this plane is the inadmissible-evidence
(sub_floor) slice. On the at_floor slice -- defects revealed only by sub-floor
evidence -- careful judges catch what RAILS, by construction, does not.
"""
from __future__ import annotations
import json
from pathlib import Path

from figures._style import save, NAVY, TEAL, GOLD, GREY, TERRA, IVORY

RESULTS = Path(__file__).parent.parent / "results"
PROVIDER_COLOR = {"anthropic": NAVY, "openai": TEAL, "mistral": TERRA, "gemini": "#7A6E5D"}
PRIOR_GEN = {"gpt-4.1"}   # rendered as a cautionary reference, not a current-roster peer


def make() -> None:
    h = json.loads((RESULTS / "headline.json").read_text())
    pts = []
    for m in h["models"]:
        prov = m["model"].split("/")[0]
        name = m["model"].split("/")[-1]
        pts.append((
            m["judge_alone_clean_throughput"]["rate"],    # x
            1 - m["judge_alone_sub_floor"]["rate"],        # y
            prov, name,
        ))
    pts.sort(key=lambda p: p[0])

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    fig.patch.set_facecolor(IVORY); ax.set_facecolor(IVORY)

    # RAILS soundness ceiling + the governed corner the judges never reach
    ax.axhspan(0.992, 1.06, color=GOLD, alpha=0.12, zorder=0)
    ax.axhline(1.0, color=GOLD, lw=1.8, ls="--", zorder=1)
    ax.text(0.985, 1.028, "RAILS soundness ceiling — guaranteed at any policy-chosen throughput",
            color="#8f7320", fontsize=8.5, va="bottom", ha="right", fontweight="bold")
    ax.annotate("governed corner\nno judge reaches", (0.86, 0.55), fontsize=8.5, color="#8f7320",
                ha="center", va="center", style="italic")

    # markers
    seen = set()
    for x, y, prov, name in pts:
        col = PROVIDER_COLOR.get(prov, GREY)
        prior = name in PRIOR_GEN
        ax.scatter([x], [y], s=130, color=("none" if prior else col),
                   edgecolor=col, lw=(2.0 if prior else 0.7), zorder=3,
                   label=(prov if prov not in seen else None))
        seen.add(prov)

    # labels: ceiling-cluster (cautious) labels fan into a strip below the line with
    # leader lines, so coincident points stay legible; others label in place.
    top = [p for p in pts if p[1] > 0.95]
    low = [p for p in pts if p[1] <= 0.95]
    for k, (x, y, prov, name) in enumerate(top):
        lx = 0.06 + 0.92 * (k + 0.5) / max(len(top), 1)
        ax.annotate(name, (x, y), textcoords="data", xytext=(lx, 0.86 - 0.05 * (k % 2)),
                    fontsize=8, color=NAVY, ha="center",
                    arrowprops=dict(arrowstyle="-", color=GREY, lw=0.5, shrinkA=2, shrinkB=3))
    for x, y, prov, name in low:
        label = f"{name}\n(prior-gen, permissive)" if name in PRIOR_GEN else name
        ha, dx = ("right", -10) if x > 0.85 else ("left", 10)
        ax.annotate(label, (x, y), textcoords="offset points", xytext=(dx, 6),
                    fontsize=8, color=NAVY, ha=ha)

    # arrow tracing the tradeoff the judges are stuck on
    ax.annotate("", xy=(0.96, 0.08), xytext=(0.04, 0.99),
                arrowprops=dict(arrowstyle="->", color=GREY, lw=1.0, ls=":", alpha=0.7))
    ax.text(0.52, 0.50, "judges' safety–throughput frontier", fontsize=8.5, color=GREY,
            rotation=-32, ha="center", va="center", alpha=0.9)

    ax.set_xlim(-0.04, 1.06); ax.set_ylim(-0.02, 1.10)
    ax.set_xlabel("throughput — clears legitimate work (higher is better)")
    ax.set_ylabel("soundness — refuses inadmissible-evidence defectives (higher is better)")
    ax.set_title("The judge's disposition is model-dependent and ungoverned;\n"
                 "RAILS holds the soundness ceiling by construction", fontsize=11, color=NAVY)
    ax.legend(frameon=False, loc="lower left", ncol=4, fontsize=8, title="judge alone, by provider")
    ax.grid(True, color="#E4DCCB", lw=0.7)
    fig.tight_layout()
    save(fig, "fig_scatter")


if __name__ == "__main__":
    make()
