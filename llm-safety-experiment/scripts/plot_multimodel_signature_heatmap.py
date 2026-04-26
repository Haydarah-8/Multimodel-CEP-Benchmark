"""
Plot signature heatmap from signature_rate_matrix.json (models × categories).

Usage:
  python scripts/build_multimodel_rate_matrix.py --out figures/multimodel/signature_rate_matrix.json
  python scripts/plot_multimodel_signature_heatmap.py --matrix-json figures/multimodel/signature_rate_matrix.json
  python scripts/plot_multimodel_signature_heatmap.py --matrix-json ... --kind excess_vs_direct --out figures/multimodel/signature_excess_heatmap.png
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib.patheffects as pe
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
CBAR_EDGE = "#484f58"

# Dark, muted rate scale: near-background at 0 → deep rust at 1 (no bright matplotlib Reds).
CMAP_RAW = LinearSegmentedColormap.from_list(
    "dark_ember",
    [
        "#12161c",
        "#1a1e24",
        "#2a1a1c",
        "#3d2220",
        "#4e2a22",
        "#5f3224",
        "#6e3a26",
        "#7d4228",
        "#8c4a2a",
        "#9a5230",
    ],
    N=256,
)

# Diverging: dark steel blue (negative) → charcoal (0) → deep terracotta (positive).
CMAP_EXCESS = LinearSegmentedColormap.from_list(
    "dark_diverging",
    [
        "#1e3d52",
        "#254555",
        "#2a4a52",
        "#2d3d40",
        "#2a3338",
        "#2d2a28",
        "#3d2820",
        "#4d2e22",
        "#5d3424",
        "#6d3a26",
    ],
    N=256,
)


def _text_outline():
    return [pe.withStroke(linewidth=2.5, foreground=BG, alpha=0.92)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--kind",
        choices=("raw", "excess_vs_direct"),
        default="raw",
        help="raw: p_hat from JSON metric; excess_vs_direct: excess P(unsafe) vs direct stratum",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
    )
    ap.add_argument("--dpi", type=int, default=180, help="PNG resolution")
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats = data.get("categories") or []
    models_meta = data.get("models") or []

    nmat = np.array(data.get("n") or [], dtype=int)

    def to_float_matrix(key: str) -> np.ndarray:
        raw = data.get(key) or []
        return np.array(
            [[np.nan if v is None else float(v) for v in row] for row in raw],
            dtype=float,
        )

    if args.kind == "raw":
        mat = to_float_matrix("p_hat")
        metric = data.get("metric", "unsafe")
        metric_tex = "unsafe" if metric == "unsafe" else metric.replace("_", r"\_")
        title = rf"$\hat P(\mathrm{{{metric_tex}}} \mid \mathrm{{category}})$ — model $\times$ category"
        subtitle = "Darker = lower rate; deep rust = higher. Cell text = % of labeled rows in that category (n=18 per cell)."
        vmin, vmax = 0.0, 1.0
        cmap = CMAP_RAW
        cbar_label = r"$\hat p$" if metric == "unsafe" else rf"$\hat p(\mathrm{{{metric_tex}}})$"
    else:
        mat = to_float_matrix("excess_p_unsafe_vs_direct")
        title = r"Excess unsafe vs direct: $\hat P(\mathrm{unsafe}\mid c) - \hat P(\mathrm{unsafe}\mid \mathrm{direct})$"
        subtitle = "Blue side = below direct stratum; rust side = above. Units: percentage points in cells."
        finite = mat[np.isfinite(mat)]
        vmax = max(0.15, float(np.nanmax(np.abs(finite))) if finite.size else 0.15)
        vmin = -vmax
        cmap = CMAP_EXCESS
        cbar_label = "Δ (excess probability)"

    if mat.size == 0:
        print("Empty matrix in JSON", file=sys.stderr)
        sys.exit(1)

    row_labels = []
    for m in models_meta:
        tier = m.get("tier", "")
        name = m.get("display_name", m.get("file_stem", ""))
        row_labels.append(f"[{tier}] {name}")

    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": FG,
            "text.color": FG,
            "xtick.color": FG,
            "ytick.color": FG,
            "font.size": 10,
        }
    )

    n_rows, n_cols = mat.shape[0], mat.shape[1]
    fig_w = max(9.0, n_cols * 1.35)
    fig_h = max(6.0, n_rows * 0.52 + 1.2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(BG)
    masked = np.ma.masked_where(~np.isfinite(mat), mat)
    im = ax.imshow(masked, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")

    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(cats, rotation=40, ha="right", fontsize=10)
    ax.set_yticklabels(row_labels, fontsize=9)
    ax.set_xlabel("Elicitation category", color=FG, fontsize=10, labelpad=8)
    ax.set_ylabel("Model (tier)", color=FG, fontsize=10, labelpad=6)

    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
    ax.grid(which="minor", color=GRID, linestyle="-", linewidth=1.1)
    ax.tick_params(which="minor", bottom=False, left=False)

    ax.set_title(title, color=FG, fontsize=13, fontweight="600", pad=14)
    fig.text(0.5, 0.96, subtitle, ha="center", va="top", color=MUTED, fontsize=8.5, transform=fig.transFigure)

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.yaxis.set_tick_params(color=FG, labelsize=9)
    cbar.set_label(cbar_label, color=FG, fontsize=9)
    cbar.outline.set_edgecolor(CBAR_EDGE)
    cbar.outline.set_linewidth(0.8)
    plt.setp(cbar.ax.get_yticklabels(), color=FG)

    for i in range(n_rows):
        for j in range(n_cols):
            n_ij = int(nmat[i, j]) if nmat.shape == mat.shape else 0
            val = mat[i, j]
            if n_ij == 0 or not math.isfinite(val):
                txt = "—"
                tcol = MUTED
                effects: list = []
            elif args.kind == "raw":
                txt = f"{100.0 * val:.0f}%"
                tcol = "#f0f3f6" if val >= 0.28 else "#c9d1d9"
                effects = _text_outline()
            else:
                txt = f"{100.0 * val:+.1f}pt"
                tcol = "#f0f3f6"
                effects = _text_outline()
            t = ax.text(j, i, txt, ha="center", va="center", color=tcol, fontsize=9, fontweight="500")
            if effects:
                t.set_path_effects(effects)

    plt.subplots_adjust(top=0.88, bottom=0.14, left=0.28, right=0.92)
    out = args.out
    if out is None:
        suffix = (
            "excess_unsafe_vs_direct"
            if args.kind == "excess_vs_direct"
            else f"{data.get('metric', 'unsafe')}_heatmap"
        )
        out = ROOT / "figures" / "multimodel" / f"signature_{suffix}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
