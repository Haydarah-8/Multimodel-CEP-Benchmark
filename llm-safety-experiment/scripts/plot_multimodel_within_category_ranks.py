"""
Heatmap of **within-category ranks**: for each category, rank the nine runs by $\\hat p(\\mathrm{unsafe})$
(1 = lowest in that column, 9 = highest). Descriptive; highlights relative standing.

Usage:
  python scripts/plot_multimodel_within_category_ranks.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from academic_plot_style import DEFAULT_DPI  # noqa: E402


BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"

CMAP = LinearSegmentedColormap.from_list(
    "rank_muted",
    ["#1a2f3d", "#2d3d45", "#3d4a42", "#5c4a32", "#7a4a2e", "#8f5530"],
    N=256,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_within_category_ranks_unsafe.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    p_hat = np.array(data.get("p_hat") or [], dtype=float)

    n_row, n_col = p_hat.shape
    ranks = np.full_like(p_hat, np.nan, dtype=float)
    for j in range(n_col):
        col = p_hat[:, j]
        valid = np.isfinite(col)
        if not np.any(valid):
            continue
        idx = np.where(valid)[0]
        vc = col[idx]
        rk = rankdata(vc, method="ordinal")
        ranks[idx, j] = rk

    row_labels = [f"[{m.get('tier')}] {m.get('provider')}/{m.get('model')}" for m in models]

    fig, ax = plt.subplots(figsize=(max(8, n_col * 1.15), max(6, n_row * 0.42)))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    masked = np.ma.masked_invalid(ranks)
    im = ax.imshow(masked, aspect="auto", cmap=CMAP, vmin=1, vmax=9, interpolation="nearest")

    ax.set_xticks(np.arange(n_col))
    ax.set_yticks(np.arange(n_row))
    ax.set_xticklabels(cats, rotation=35, ha="right", fontsize=10, color=FG)
    ax.set_yticklabels(row_labels, fontsize=8, color=FG)
    ax.set_xlabel("Category (rank computed within column)", color=FG, fontsize=10)
    ax.set_ylabel("Model run", color=FG, fontsize=10)

    for i in range(n_row):
        for j in range(n_col):
            v = ranks[i, j]
            if not math.isfinite(v):
                continue
            tcol = FG if v < 5.5 else "#f0f3f6"
            ax.text(j, i, f"{int(v)}", ha="center", va="center", color=tcol, fontsize=9, fontweight="600")

    ax.set_title(
        "Within-category rank of $\\hat P(\\mathrm{unsafe})$ (9 = highest in column)",
        color=FG,
        fontsize=12,
        fontweight="600",
        pad=12,
    )
    for spine in ax.spines.values():
        spine.set_color(GRID)
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Rank (1–9)", color=FG, fontsize=9)
    plt.setp(cbar.ax.get_yticklabels(), color=FG)

    fig.text(
        0.5,
        0.01,
        "Nine runs; ties broken by sort order; Gemini mid/expensive are separate runs.",
        ha="center",
        fontsize=8,
        color=MUTED,
    )
    plt.subplots_adjust(left=0.32, right=0.92, bottom=0.14, top=0.92)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
