"""
Parallel coordinates: each model is a polyline over category axes (rates from matrix JSON).

Descriptive only; n=18/binomial per category; nine runs, eight unique Gemini SKUs (mid/expensive same model id).

Usage:
  python scripts/plot_multimodel_parallel_coordinates.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"

PROVIDER_COLORS = {
    "openai": "#58a6ff",
    "anthropic": "#c297ff",
    "gemini": "#3fb950",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_parallel_coordinates.png",
    )
    ap.add_argument(
        "--color-by",
        choices=("provider", "tier"),
        default="provider",
    )
    ap.add_argument("--dpi", type=int, default=180)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    p_hat = np.array(data.get("p_hat") or [], dtype=float)
    metric = data.get("metric", "unsafe")

    if p_hat.size == 0 or len(models) != p_hat.shape[0]:
        print("Invalid matrix", file=sys.stderr)
        sys.exit(1)

    x = np.arange(len(cats))
    fig, ax = plt.subplots(figsize=(max(8, len(cats) * 1.4), 6.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    TIER_COLORS = {"cheap": "#79c0ff", "mid": "#56d364", "expensive": "#ffa657"}

    for i, m in enumerate(models):
        row = np.clip(p_hat[i], 0.0, 1.0)
        prov = str(m.get("provider", "")).lower()
        tier = str(m.get("tier", "")).lower()
        if args.color_by == "provider":
            c = PROVIDER_COLORS.get(prov, MUTED)
            alpha = 0.78
        else:
            c = TIER_COLORS.get(tier, MUTED)
            alpha = 0.88
        ax.plot(x, row, color=c, alpha=alpha, linewidth=1.6, linestyle="-", zorder=2)
        ax.scatter(x, row, color=c, s=22, alpha=0.92, zorder=3, edgecolors=BG, linewidths=0.6)

    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=30, ha="right", color=FG, fontsize=10)
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel(r"$\hat p$" + f" ({metric})", color=FG, fontsize=10)
    ax.set_xlabel("Elicitation category", color=FG, fontsize=10)
    ax.tick_params(axis="y", colors=FG)
    ax.grid(True, color=GRID, alpha=0.5, linestyle="-")
    for spine in ax.spines.values():
        spine.set_color(GRID)

    title = f"Parallel coordinates: model profiles over categories ({metric})"
    ax.set_title(title, color=FG, fontsize=12, fontweight="600", pad=12)
    foot = (
        "Nine API runs; Gemini mid & expensive share model id gemini-2.5-pro. "
        "n=18/category; descriptive not causal."
    )
    fig.text(0.5, 0.02, foot, ha="center", fontsize=8, color=MUTED)

    if args.color_by == "provider":
        handles = [
            plt.Line2D([0], [0], color=PROVIDER_COLORS["openai"], lw=2, label="OpenAI"),
            plt.Line2D([0], [0], color=PROVIDER_COLORS["anthropic"], lw=2, label="Anthropic"),
            plt.Line2D([0], [0], color=PROVIDER_COLORS["gemini"], lw=2, label="Gemini"),
        ]
    else:
        handles = [
            plt.Line2D([0], [0], color=TIER_COLORS["cheap"], lw=2, label="cheap"),
            plt.Line2D([0], [0], color=TIER_COLORS["mid"], lw=2, label="mid"),
            plt.Line2D([0], [0], color=TIER_COLORS["expensive"], lw=2, label="expensive"),
        ]
    leg = ax.legend(handles=handles, loc="upper left", framealpha=0.92, facecolor="#161b22", edgecolor=GRID)
    for t in leg.get_texts():
        t.set_color(FG)

    plt.subplots_adjust(bottom=0.18, top=0.92)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
