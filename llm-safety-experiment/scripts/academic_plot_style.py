"""
Shared matplotlib rc for publication-style (modern sans, minimal spines, higher DPI).

Use in PhD-level figure scripts: `apply_academic_style()` before building figures.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

# Muted, color-blind–friendly accent sequence (Okabe–Ito inspired, darkened for slides).
ACCENT = {
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "sky": "#56B4E9",
    "vermillion": "#CC79A7",
    "yellow": "#E69F00",
}

BG_DARK = "#0d1117"
FG_DARK = "#e6edf3"
MUTED_DARK = "#8b949e"
GRID_DARK = "#30363d"


def apply_academic_style(*, dark: bool = True) -> None:
    if dark:
        plt.rcParams.update(
            {
                "figure.facecolor": BG_DARK,
                "axes.facecolor": BG_DARK,
                "axes.edgecolor": GRID_DARK,
                "axes.labelcolor": FG_DARK,
                "text.color": FG_DARK,
                "xtick.color": FG_DARK,
                "ytick.color": FG_DARK,
                "grid.color": GRID_DARK,
                "grid.alpha": 0.45,
                "axes.grid": True,
                "grid.linewidth": 0.6,
            }
        )
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10.5,
            "axes.titleweight": "600",
            "axes.linewidth": 0.9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": True,
            "legend.framealpha": 0.94,
            "figure.titlesize": 13,
            "figure.titleweight": "600",
            "lines.linewidth": 1.8,
            "lines.solid_capstyle": "round",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.08,
        }
    )
