"""
Hierarchical clustering heatmap (models × categories) with dendrograms.

Uses average linkage on Euclidean distance; scipy + matplotlib only (no seaborn).

Publication-oriented layout: generous margins, dedicated colorbar column (no overlap
with heatmap labels), light neutral theme, readable typography.

Descriptive; exploratory ordering only (n=9 runs).

Usage:
  python scripts/plot_multimodel_clustermap.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import dendrogram, linkage, leaves_list
from scipy.spatial.distance import pdist

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from academic_plot_style import DEFAULT_DPI  # noqa: E402

BG = "#fafbfc"
FG = "#24292f"
MUTED = "#656d76"
GRID = "#d0d7de"
DENDRO = "#57606a"

CMAP = mcolors.LinearSegmentedColormap.from_list(
    "rate_blues",
    ["#f6f8fa", "#ddf4ff", "#54aeff", "#0969da", "#0550ae"],
    N=256,
)


def short_row_label(m: dict) -> str:
    tier = str(m.get("tier", "")).strip()
    prov = str(m.get("provider", "")).strip()
    mod = str(m.get("model", "")).strip()
    tier_s = {"cheap": "C", "mid": "M", "expensive": "E"}.get(tier.lower(), tier[:1].upper() or "?")
    prov_s = {"openai": "OAI", "anthropic": "Ant", "gemini": "Gem"}.get(prov.lower(), prov[:4])
    if len(mod) > 24:
        mod = mod[:22] + "…"
    return f"{tier_s}:{prov_s} · {mod}"


def _align_col_dendrogram(ax_top: plt.Axes, n_cols: int) -> None:
    ax_top.set_xlim(-0.5, n_cols - 0.5)
    ax_top.set_ylim(0.0, None)
    ax_top.invert_yaxis()


def _align_row_dendrogram(ax_left: plt.Axes, n_rows: int) -> None:
    ax_left.set_ylim(-0.5, n_rows - 0.5)
    ax_left.set_xlim(None, 0.0)
    ax_left.invert_xaxis()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_clustermap_rates.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    mat = np.array(data.get("p_hat") or [], dtype=float)
    metric = data.get("metric", "unsafe")

    if mat.size == 0:
        sys.exit("empty matrix")

    col_mean = np.nanmean(mat, axis=0)
    mat_filled = np.where(np.isfinite(mat), mat, col_mean)
    mat_filled = np.where(np.isfinite(mat_filled), mat_filled, 0.0)

    row_link = linkage(pdist(mat_filled, metric="euclidean"), method="average")
    col_link = linkage(pdist(mat_filled.T, metric="euclidean"), method="average")
    row_order = leaves_list(row_link)
    col_order = leaves_list(col_link)

    mat_ord = mat_filled[np.ix_(row_order, col_order)]
    row_labs = [short_row_label(models[i]) for i in row_order]
    col_labs = [cats[j] for j in col_order]

    n_r, n_c = mat_ord.shape

    fig = plt.figure(figsize=(15.0, 10.0), facecolor=BG)
    gs = GridSpec(
        2,
        3,
        width_ratios=[0.38, 1.0, 0.055],
        height_ratios=[0.42, 1.0],
        wspace=0.28,
        hspace=0.30,
        left=0.06,
        right=0.97,
        top=0.90,
        bottom=0.14,
    )

    ax_corner = fig.add_subplot(gs[0, 0])
    ax_corner.axis("off")

    ax_top = fig.add_subplot(gs[0, 1])
    ax_left = fig.add_subplot(gs[1, 0])
    ax_heat = fig.add_subplot(gs[1, 1])
    cax = fig.add_subplot(gs[1, 2])

    ax_pad = fig.add_subplot(gs[0, 2])
    ax_pad.axis("off")

    for ax in (ax_top, ax_left, ax_heat):
        ax.set_facecolor(BG)

    dendrogram(
        col_link,
        ax=ax_top,
        above_threshold_color=DENDRO,
        color_threshold=0,
        distance_sort="descending")
    ax_top.set_xticks([])
    ax_top.set_yticks([])
    ax_top.tick_params(colors=MUTED, labelsize=9)
    for spine in ax_top.spines.values():
        spine.set_visible(False)
    _align_col_dendrogram(ax_top, n_c)

    dendrogram(
        row_link,
        ax=ax_left,
        orientation="left",
        above_threshold_color=DENDRO,
        color_threshold=0,
        distance_sort="descending")
    ax_left.set_xticks([])
    ax_left.set_yticks([])
    ax_left.tick_params(colors=MUTED, labelsize=9)
    for spine in ax_left.spines.values():
        spine.set_visible(False)
    _align_row_dendrogram(ax_left, n_r)

    im = ax_heat.imshow(
        mat_ord,
        aspect="auto",
        cmap=CMAP,
        vmin=0,
        vmax=1,
        interpolation="nearest",
        extent=(-0.5, n_c - 0.5, n_r - 0.5, -0.5),
    )
    ax_heat.set_xticks(np.arange(n_c))
    ax_heat.set_xticklabels(
        col_labs,
        rotation=40,
        ha="right",
        fontsize=10,
        color=FG,
    )
    ax_heat.set_yticks(np.arange(n_r))
    ax_heat.set_yticklabels(row_labs, fontsize=9.5, color=FG)
    ax_heat.set_xlabel("Elicitation category (cluster order)", color=FG, fontsize=11, labelpad=10)
    ax_heat.set_ylabel("Model run (cluster order)", color=FG, fontsize=11, labelpad=10)
    for spine in ax_heat.spines.values():
        spine.set_color(GRID)
        spine.set_linewidth(0.8)

    ax_heat.tick_params(axis="both", colors=MUTED, length=0)
    ax_heat.set_xlim(-0.5, n_c - 0.5)
    ax_heat.set_ylim(n_r - 0.5, -0.5)

    cbar = fig.colorbar(im, cax=cax)
    cbar.ax.set_facecolor(BG)
    cbar.ax.yaxis.set_tick_params(colors=FG, labelsize=10)
    cbar.outline.set_edgecolor(GRID)
    cbar.set_label(r"Estimated rate $\hat{p}$" + f" ({metric})", color=FG, fontsize=10.5, labelpad=12)

    fig.suptitle(
        "Hierarchical clustering of multimodel rates",
        color=FG,
        fontsize=14,
        fontweight="600",
        y=0.96,
    )
    fig.text(
        0.5,
        0.935,
        "Rows and columns reordered by average linkage on Euclidean distance | exploratory only",
        ha="center",
        fontsize=10,
        color=MUTED,
    )
    fig.text(
        0.5,
        0.055,
        "Nine API configurations; fixed bank; rates are benchmark-conditional. "
        "Dendrogram topology is not a statistical test. See companion .md for interpretation.",
        ha="center",
        fontsize=9,
        color=MUTED,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        args.out,
        dpi=args.dpi,
        facecolor=BG,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.22,
    )
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()

