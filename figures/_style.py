"""Shared matplotlib style — matches the paper's editorial-scientific palette."""
from __future__ import annotations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

IVORY = "#F8F4EC"
NAVY = "#0F2A44"
TEAL = "#2E7C7E"
GOLD = "#C8A045"
GREY = "#9C9384"
TERRA = "#B5654A"

OUT = Path(__file__).parent / "out"

plt.rcParams.update({
    "font.size": 10,
    "axes.edgecolor": NAVY,
    "axes.labelcolor": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "text.color": NAVY,
    "axes.titlecolor": NAVY,
})


def new_fig(w: float = 7.0, h: float = 4.0):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(IVORY)
    ax.set_facecolor(IVORY)
    return fig, ax


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext, kw in (("pdf", {}), ("png", {"dpi": 150})):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight",
                    facecolor=fig.get_facecolor(), **kw)
    plt.close(fig)
