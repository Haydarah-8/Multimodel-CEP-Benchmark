"""
Tier × provider **interaction** view: within each category, lines connect cheap → mid → expensive
for each provider ($\\hat P(\\mathrm{unsafe})$).

Modern small-multiples layout for reading non-additive tier effects.

Usage:
  python scripts/plot_multimodel_interaction_tier_provider.py --matrix-json figures/multimodel/signature_rate_matrix.json
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
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from academic_plot_style import ACCENT, apply_academic_style  # noqa: E402

TIER_ORDER = ("cheap", "mid", "expensive")
PROV_ORDER = ("openai", "anthropic", "gemini")
TIER_X = np.arange(3)
PROV_STYLE = {
    "openai": {"color": ACCENT["blue"], "marker": "o"},
    "anthropic": {"color": ACCENT["orange"], "marker": "s"},
    "gemini": {"color": ACCENT["green"], "marker": "^"},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_tier_provider_interaction_unsafe.png",
    )
    ap.add_argument("--dpi", type=int, default=220)
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

    apply_academic_style(dark=True)
    n_cat = len(cats)
    fig, axes = plt.subplots(1, n_cat, figsize=(3.6 * n_cat, 4.8), sharey=True)
    if n_cat == 1:
        axes = [axes]
    fig.patch.set_facecolor("#0d1117")

    for fi, cat in enumerate(cats):
        ax = axes[fi]
        ax.set_facecolor("#0d1117")
        for prov in PROV_ORDER:
            ys = []
            for tier in TIER_ORDER:
                idx = index.get((tier, prov))
                if idx is None:
                    ys.append(float("nan"))
                    continue
                row = p_hat[idx]
                v = row[fi] if fi < len(row) else None
                ys.append(
                    float(v)
                    if v is not None and isinstance(v, (int, float)) and math.isfinite(float(v))
                    else float("nan")
                )
            st = PROV_STYLE[prov]
            ax.plot(
                TIER_X,
                ys,
                marker=st["marker"],
                color=st["color"],
                linewidth=2.2,
                markersize=8,
                label=prov.capitalize(),
                alpha=0.92,
            )

        ax.set_xticks(TIER_X)
        ax.set_xticklabels([t.capitalize() for t in TIER_ORDER], fontsize=9)
        ax.set_ylim(-0.02, 1.02)
        ax.set_title(cat, fontsize=11, fontweight="600")
        ax.tick_params(axis="y", labelsize=8)
        if fi == 0:
            ax.set_ylabel(r"$\hat P(\mathrm{unsafe}\mid c)$", fontsize=10.5)

    handles, labels_leg = axes[0].get_legend_handles_labels()
    leg = fig.legend(
        handles,
        labels_leg,
        loc="lower center",
        ncol=3,
        fontsize=10,
        bbox_to_anchor=(0.5, -0.02),
        framealpha=0.94,
        facecolor="#161b22",
        edgecolor="#30363d",
    )
    for t in leg.get_texts():
        t.set_color("#e6edf3")

    fig.suptitle(
        "Tier × provider interaction (connected profiles)\n"
        "Gemini mid & expensive: same model id, separate runs.",
        fontsize=12,
        fontweight="600",
        y=1.05,
    )
    plt.subplots_adjust(left=0.07, right=0.99, top=0.82, bottom=0.18, wspace=0.22)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
