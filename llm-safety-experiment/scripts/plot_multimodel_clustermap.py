"""
Hierarchical clustering heatmap (models × categories) with dendrograms.

Uses average linkage on Euclidean distance; scipy only (no seaborn).

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
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from scipy.cluster.hierarchy import dendrogram, linkage, leaves_list
from scipy.spatial.distance import pdist

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"

CMAP = LinearSegmentedColormap.from_list(
    "dark_ember",
    [
        "#12161c",
        "#2a1a1c",
        "#4e2a22",
        "#6e3a26",
        "#9a5230",
    ],
    N=256,
)


def short_row_label(m: dict) -> str:
    t = str(m.get("tier", ""))[:1]
    p = str(m.get("provider", ""))[:3]
    mod = str(m.get("model", ""))
    if len(mod) > 18:
        mod = mod[:16] + "…"
    return f"{t}:{p}:{mod}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_clustermap_rates.png",
    )
    ap.add_argument("--dpi", type=int, default=180)
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

    fig = plt.figure(figsize=(11.5, 8.8))
    fig.patch.set_facecolor(BG)
    gs = GridSpec(
        2,
        2,
        width_ratios=[0.28, 1],
        height_ratios=[0.32, 1],
        wspace=0.07,
        hspace=0.07,
        left=0.07,
        right=0.88,
        top=0.92,
        bottom=0.14,
    )
    ax_corner = fig.add_subplot(gs[0, 0])
    ax_corner.axis("off")
    ax_top = fig.add_subplot(gs[0, 1])
    ax_left = fig.add_subplot(gs[1, 0])
    ax_heat = fig.add_subplot(gs[1, 1])

    for ax in (ax_top, ax_left, ax_heat):
        ax.set_facecolor(BG)

    dendrogram(
        col_link,
        ax=ax_top,
        above_threshold_color=MUTED,
        color_threshold=0,
    )
    ax_top.set_xticks([])
    ax_top.set_yticks([])
    for spine in ax_top.spines.values():
        spine.set_visible(False)

    dendrogram(
        row_link,
        ax=ax_left,
        orientation="left",
        above_threshold_color=MUTED,
        color_threshold=0,
    )
    ax_left.set_xticks([])
    ax_left.set_yticks([])
    for spine in ax_left.spines.values():
        spine.set_visible(False)

    im = ax_heat.imshow(
        mat_ord,
        aspect="auto",
        cmap=CMAP,
        vmin=0,
        vmax=1,
        interpolation="nearest",
    )
    ax_heat.set_xticks(np.arange(len(col_labs)))
    ax_heat.set_xticklabels(col_labs, rotation=35, ha="right", fontsize=10, color=FG)
    ax_heat.set_yticks(np.arange(len(row_labs)))
    ax_heat.set_yticklabels(row_labs, fontsize=8, color=FG)
    ax_heat.set_xlabel("Category", color=FG, fontsize=10)
    ax_heat.set_ylabel("Model run", color=FG, fontsize=10)
    for spine in ax_heat.spines.values():
        spine.set_color(GRID)

    cbar = fig.colorbar(im, ax=ax_heat, fraction=0.035, pad=0.04)
    cbar.ax.yaxis.set_tick_params(colors=FG)
    plt.setp(cbar.ax.get_yticklabels(), color=FG)
    cbar.set_label(r"$\hat p$" + f" ({metric})", color=FG, fontsize=9)

    fig.suptitle(
        f"Clustermap: {metric} rates (average linkage, Euclidean)",
        color=FG,
        fontsize=12,
        fontweight="600",
        y=0.97,
    )
    fig.text(
        0.5,
        0.06,
        "Nine runs; n=18/cell; Gemini mid/expensive same model id; dendrogram order is exploratory.",
        ha="center",
        fontsize=8,
        color=MUTED,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
