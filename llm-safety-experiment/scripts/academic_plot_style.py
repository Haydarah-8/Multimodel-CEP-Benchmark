"""
Shared matplotlib rc for publication-style figures (legible labels, high DPI, dark theme).

Use: `apply_academic_style()` before building figures; use `DEFAULT_DPI` for argparse / savefig.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

# Single source of truth for raster exports (slides, papers, README).
DEFAULT_DPI = 220

# Muted, color-blind-friendly accent sequence (Okabe-Ito inspired, darkened for slides).
ACCENT = {
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "sky": "#56B4E9",
    "vermillion": "#CC79A7",
    "yellow": "#E69F00",
}

BG_DARK = "#0d1117"
FG_DARK = "#f0f3f6"
MUTED_DARK = "#9aa7b5"
GRID_DARK = "#3d444d"
LEGEND_FACE = "#161b22"
LEGEND_EDGE = "#484f58"


def savefig_png(fig, path: str | Path, *, dpi: int | None = None, facecolor: str = BG_DARK) -> None:
    """Consistent PNG export: tight bbox, padding, no edge artefact."""
    fig.savefig(
        path,
        dpi=dpi or DEFAULT_DPI,
        facecolor=facecolor,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.14,
    )


def apply_academic_style(*, dark: bool = True) -> None:
    """Global rcParams for readable typography; call once per process before plotting."""
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
                "grid.alpha": 0.5,
                "axes.grid": True,
                "grid.linewidth": 0.65,
            }
        )
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"],
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11.5,
            "axes.titleweight": "600",
            "axes.linewidth": 1.0,
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "legend.fontsize": 10.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": True,
            "legend.framealpha": 0.96,
            "legend.edgecolor": LEGEND_EDGE,
            "legend.facecolor": LEGEND_FACE,
            "figure.titlesize": 14,
            "figure.titleweight": "600",
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "errorbar.capsize": 3.0,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.12,
            "savefig.dpi": DEFAULT_DPI,
        }
    )
