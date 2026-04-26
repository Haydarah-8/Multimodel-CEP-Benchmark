"""
5×5 correlation matrix: pairwise correlation of category rate columns across the nine model runs.

Noisy with n=9; descriptive only.

Usage:
  python scripts/plot_category_correlation_across_models.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"

CMAP = LinearSegmentedColormap.from_list(
    "corr_div",
    [
        "#1e3d52",
        "#2d3d40",
        "#2a3338",
        "#3d2820",
        "#6d3a26",
    ],
    N=256,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_category_correlation_across_models.png",
    )
    ap.add_argument("--dpi", type=int, default=180)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    mat = np.array(data.get("p_hat") or [], dtype=float)
    metric = data.get("metric", "unsafe")

    if mat.shape[0] < 2 or mat.shape[1] < 2:
        print("Need at least 2 runs and 2 categories", file=sys.stderr)
        sys.exit(1)

    n_cat = mat.shape[1]
    c = np.eye(n_cat)
    for i in range(n_cat):
        for j in range(i + 1, n_cat):
            xi, xj = mat[:, i], mat[:, j]
            if float(np.std(xi)) < 1e-14 or float(np.std(xj)) < 1e-14:
                r = float("nan")
            else:
                r = float(np.corrcoef(xi, xj)[0, 1])
            c[i, j] = r
            c[j, i] = r

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    c_plot = np.ma.masked_invalid(c)
    im = ax.imshow(c_plot, cmap=CMAP, vmin=-1, vmax=1, interpolation="nearest")
    ax.set_xticks(np.arange(len(cats)))
    ax.set_yticks(np.arange(len(cats)))
    ax.set_xticklabels(cats, rotation=35, ha="right", fontsize=10, color=FG)
    ax.set_yticklabels(cats, fontsize=10, color=FG)
    for i in range(len(cats)):
        for j in range(len(cats)):
            val = c[i, j]
            if val != val:
                ax.text(j, i, "—", ha="center", va="center", color=MUTED, fontsize=9)
            else:
                tcol = FG if abs(val) < 0.5 else "#f0f3f6"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=tcol, fontsize=9)

    ax.set_title(
        f"Category correlation across runs ({metric} rates)\nPearson r; n_runs={mat.shape[0]}",
        color=FG,
        fontsize=11,
        fontweight="600",
    )
    for spine in ax.spines.values():
        spine.set_color(GRID)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.setp(cbar.ax.get_yticklabels(), color=FG)
    cbar.set_label("Pearson r", color=FG, fontsize=9)

    fig.text(
        0.5,
        0.02,
        "Only nine independent runs → sampling noise; do not over-interpret off-diagonal r.",
        ha="center",
        fontsize=8,
        color=MUTED,
    )
    plt.subplots_adjust(bottom=0.18, top=0.88)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
