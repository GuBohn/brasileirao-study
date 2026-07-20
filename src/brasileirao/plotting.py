"""One place for figure style so every chart matches."""
import matplotlib.pyplot as plt

from .paths import FIGURES

COLORS = {"main": "#1a6b4a", "accent": "#c0392b", "muted": "#7f8c8d"}


def style() -> None:
    plt.rcParams.update({
        "figure.figsize": (9, 5),
        "figure.dpi": 120,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "font.size": 11,
    })


def save(fig, name: str) -> None:
    fig.savefig(FIGURES / f"{name}.png", bbox_inches="tight")
