"""
3×3 polar “radar” grid: each cell plots $\\hat P(\\mathrm{unsafe}\\mid c)$ over the five categories.

Complements bar panels; same data as signature_rate_matrix.json. Muted fill, no neon.

Usage:
  python scripts/plot_multimodel_radar_grid.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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

PROVIDER_COLORS = {
    "openai": "#58a6ff",
    "anthropic": "#c297ff",
    "gemini": "#3fb950",
}

TIER_ORDER = ("cheap", "mid", "expensive")
PROV_ORDER = ("openai", "anthropic", "gemini")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_radar_grid_unsafe.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    p_hat: list[list[float | None]] = list(data.get("p_hat") or [])

    index: dict[tuple[str, str], int] = {}
    for i, m in enumerate(models):
        t = str(m.get("tier", "")).lower()
        p = str(m.get("provider", "")).lower()
        index[(t, p)] = i

    n_cat = len(cats)
    angles = np.linspace(0, 2 * np.pi, n_cat, endpoint=False)
    angles_closed = np.concatenate([angles, angles[:1]])

    fig, axes = plt.subplots(
        3,
        3,
        figsize=(14.5, 14.0),
        subplot_kw=dict(projection="polar"),
        gridspec_kw={"wspace": 0.35, "hspace": 0.42},
    )
    fig.patch.set_facecolor(BG)

    for ri, tier in enumerate(TIER_ORDER):
        for ci, prov in enumerate(PROV_ORDER):
            ax = axes[ri][ci]
            ax.set_facecolor(BG)
            ax.tick_params(colors=FG, labelsize=7)
            ax.grid(color=GRID, alpha=0.55, linestyle="-", linewidth=0.6)
            ax.set_ylim(0, 1.0)
            ax.set_yticks([0.25, 0.5, 0.75, 1.0])
            ax.set_yticklabels(["0.25", "0.5", "0.75", "1"], color=MUTED, fontsize=6)

            idx = index.get((tier, prov))
            if idx is None:
                ax.set_title("—", color=MUTED, fontsize=9, pad=12)
                continue
            row = p_hat[idx] if idx < len(p_hat) else []
            vals = [
                0.0
                if j >= len(row) or row[j] is None or (isinstance(row[j], float) and not math.isfinite(row[j]))
                else float(row[j])
                for j in range(n_cat)
            ]
            arr = np.array(vals)
            arr_closed = np.concatenate([arr, arr[:1]])

            color = PROVIDER_COLORS.get(prov, MUTED)
            ax.plot(
                angles_closed,
                arr_closed,
                color=color,
                linewidth=1.8,
                alpha=0.92,
            )
            ax.fill(angles_closed, arr_closed, color=color, alpha=0.14)

            ax.set_xticks(angles)
            ax.set_xticklabels(cats, color=FG, fontsize=7)
            m = models[idx]
            ax.set_title(
                f"{m.get('model', '?')}",
                color=FG,
                fontsize=8,
                pad=14,
                y=1.08,
            )

    fig.suptitle(
        r"Unsafe-rate profiles (radar): $\hat P(\mathrm{unsafe}\mid c)$ over categories",
        color=FG,
        fontsize=13,
        fontweight="600",
        y=0.995,
    )
    fig.text(
        0.5,
        0.96,
        "Rows: tier (cheap → expensive). Cols: provider. Gemini mid/expensive share gemini-2.5-pro. n=18/category.",
        ha="center",
        fontsize=9,
        color=MUTED,
    )

    handles = [
        plt.Line2D([0], [0], color=PROVIDER_COLORS["openai"], lw=3, label="OpenAI"),
        plt.Line2D([0], [0], color=PROVIDER_COLORS["anthropic"], lw=3, label="Anthropic"),
        plt.Line2D([0], [0], color=PROVIDER_COLORS["gemini"], lw=3, label="Gemini"),
    ]
    leg = fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        framealpha=0.94,
        facecolor="#161b22",
        edgecolor=GRID,
        fontsize=10,
        bbox_to_anchor=(0.5, 0.02),
    )
    for t in leg.get_texts():
        t.set_color(FG)

    plt.subplots_adjust(left=0.06, right=0.96, top=0.91, bottom=0.10)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
