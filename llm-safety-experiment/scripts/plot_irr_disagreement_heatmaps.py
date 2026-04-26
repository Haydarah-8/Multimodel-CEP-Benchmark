"""
Plot disagreement heatmaps from irr_multimodel_report.json.

Panel A: models (rows) × categories — cell = disagreement rate (1 - p_o).
Panel B: tiers × categories — pooled disagreement per tier.
Optional: global 3×3 P(compare | primary) from report global section.

Usage:
  python scripts/irr_multimodel_report.py --out results/multimodel/irr_multimodel_report.json
  python scripts/plot_irr_disagreement_heatmaps.py --report-json results/multimodel/irr_multimodel_report.json
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

from compute_significance import CAT_ORDER  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"

TIER_ORDER = ("cheap", "mid", "expensive")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-json", type=Path, default=ROOT / "results" / "multimodel" / "irr_multimodel_report.json")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Combined figure path (default: figures/multimodel/irr_disagreement_panels.png)",
    )
    ap.add_argument(
        "--out-conditional",
        type=Path,
        default=None,
        help="Path for global P(compare|primary) 3×3 PNG (default: figures/multimodel/...)",
    )
    ap.add_argument(
        "--no-conditional",
        action="store_true",
        help="Skip the 3×3 global conditional figure",
    )
    args = ap.parse_args()

    if not args.report_json.is_file():
        print(f"Missing {args.report_json}; run irr_multimodel_report.py first.", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.report_json.read_text(encoding="utf-8"))
    cats = data.get("categories_axis") or list(CAT_ORDER)
    per_file = data.get("per_file") or []
    per_tier = data.get("per_tier") or {}
    global_block = data.get("global") or {}

    if not per_file:
        print("Empty per_file in report", file=sys.stderr)
        sys.exit(1)

    n_models = len(per_file)
    n_cats = len(cats)
    disc_model = np.full((n_models, n_cats), np.nan, dtype=float)
    row_labels: list[str] = []
    for i, fe in enumerate(per_file):
        tier = fe.get("tier", "")
        row_labels.append(f"[{tier}] {fe.get('display_name', fe.get('file_stem', ''))}")
        bc = fe.get("by_category") or {}
        for j, c in enumerate(cats):
            block = bc.get(c)
            if not block:
                continue
            dr = block.get("disagreement_rate")
            if dr is None:
                continue
            if block.get("n_pairs", 0) == 0:
                continue
            disc_model[i, j] = float(dr)

    n_tier = len(TIER_ORDER)
    disc_tier = np.full((n_tier, n_cats), np.nan, dtype=float)
    tier_labels = list(TIER_ORDER)
    for ti, t in enumerate(TIER_ORDER):
        tb = per_tier.get(t) or {}
        bc = tb.get("by_category") or {}
        for j, c in enumerate(cats):
            block = bc.get(c)
            if not block:
                continue
            dr = block.get("disagreement_rate")
            if dr is None:
                continue
            if (block.get("n_pairs") or 0) == 0:
                continue
            disc_tier[ti, j] = float(dr)

    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": FG,
            "text.color": FG,
            "xtick.color": FG,
            "ytick.color": FG,
        }
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(4, n_models * 0.35)))
    fig.patch.set_facecolor(BG)
    title_note = data.get("note_compare", "")
    fig.suptitle(f"Inter-rater disagreement (1 − p_o) — {title_note}", color=FG, fontsize=12)

    vmax = 0.5
    finite = disc_model[np.isfinite(disc_model)]
    if finite.size:
        vmax = max(0.2, float(np.nanmax(finite)) * 1.1)

    im1 = ax1.imshow(disc_model, aspect="auto", cmap="Reds", vmin=0.0, vmax=vmax)
    ax1.set_xticks(np.arange(n_cats))
    ax1.set_yticks(np.arange(n_models))
    ax1.set_xticklabels(cats, rotation=30, ha="right")
    ax1.set_yticklabels(row_labels, fontsize=8)
    ax1.set_title("By model (file)", color=FG)
    fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)

    for i in range(n_models):
        for j in range(n_cats):
            v = disc_model[i, j]
            if not math.isfinite(v):
                ax1.text(j, i, "—", ha="center", va="center", color=MUTED, fontsize=7)
            else:
                ax1.text(j, i, f"{100*v:.0f}%", ha="center", va="center", color="white" if v > vmax * 0.45 else FG, fontsize=7)

    im2 = ax2.imshow(disc_tier, aspect="auto", cmap="Reds", vmin=0.0, vmax=vmax)
    ax2.set_xticks(np.arange(n_cats))
    ax2.set_yticks(np.arange(n_tier))
    ax2.set_xticklabels(cats, rotation=30, ha="right")
    ax2.set_yticklabels(tier_labels)
    ax2.set_title("Pooled by tier", color=FG)
    fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)

    for i in range(n_tier):
        for j in range(n_cats):
            v = disc_tier[i, j]
            if not math.isfinite(v):
                ax2.text(j, i, "—", ha="center", va="center", color=MUTED, fontsize=8)
            else:
                ax2.text(j, i, f"{100*v:.0f}%", ha="center", va="center", color="white" if v > vmax * 0.45 else FG, fontsize=8)

    fig.tight_layout()
    out = args.out or (ROOT / "figures" / "multimodel" / "irr_disagreement_panels.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {out}", file=sys.stderr)

    pcm = global_block.get("p_compare_given_primary")
    if pcm and not args.no_conditional:
        cond_out = args.out_conditional or (ROOT / "figures" / "multimodel" / "irr_global_p_compare_given_primary.png")
        fig2, ax = plt.subplots(figsize=(6, 5))
        fig2.patch.set_facecolor(BG)
        mat = np.array(pcm, dtype=float)
        im = ax.imshow(mat, aspect="equal", cmap="viridis", vmin=0.0, vmax=1.0)
        labs = ["safe", "partial", "unsafe"]
        ax.set_xticks(np.arange(3))
        ax.set_yticks(np.arange(3))
        ax.set_xticklabels(labs)
        ax.set_yticklabels(labs)
        ax.set_xlabel("Compare (rater2 / proxy)", color=FG)
        ax.set_ylabel("Primary label", color=FG)
        ax.set_title("Global P(compare | primary)", color=FG)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{mat[i,j]:.2f}", ha="center", va="center", color=FG, fontsize=10)
        fig2.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig2.tight_layout()
        cond_out.parent.mkdir(parents=True, exist_ok=True)
        fig2.savefig(cond_out, dpi=220, facecolor=BG, edgecolor="none")
        plt.close(fig2)
        print(f"Wrote {cond_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
