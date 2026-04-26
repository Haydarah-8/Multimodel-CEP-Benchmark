"""
3×3 panel figure: UNSAFE rate by category for each tier × provider cell.

Reads figures/multimodel/signature_rate_matrix.json (run build_multimodel_rate_matrix.py first).
Muted bar palette + optional Wilson 95% CI error bars (from per_file counts).

Layout rows: cheap, mid, expensive — columns: OpenAI, Anthropic, Gemini.

Usage:
  python scripts/plot_multimodel_nine_panel.py
  python scripts/plot_multimodel_nine_panel.py --matrix-json figures/multimodel/signature_rate_matrix.json
  python scripts/plot_multimodel_nine_panel.py --no-ci
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from stats_utils import wilson_proportion_ci  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"
# Muted rust scale (non-neon); zero counts use cool gray bars.
BAR_POS = "#7a3d2e"
BAR_POS_EDGE = "#a66b52"
BAR_ZERO = "#2d333d"
BAR_ZERO_EDGE = "#484f58"
ERR_CAP = "#c9d1d9"

TIER_ORDER = ("cheap", "mid", "expensive")
PROV_ORDER = ("openai", "anthropic", "gemini")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--matrix-json",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "signature_rate_matrix.json",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_9panel_unsafe_by_category.png",
    )
    ap.add_argument(
        "--no-ci",
        action="store_true",
        help="Omit Wilson 95% CI error bars",
    )
    ap.add_argument("--dpi", type=int, default=190)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    p_hat: list[list[float | None]] = list(data.get("p_hat") or [])
    n_mat: list[list[int]] = list(data.get("n") or [])
    per_file: list[dict] = list(data.get("per_file") or [])

    if len(models) != len(p_hat):
        print("models length mismatch p_hat", file=sys.stderr)
        sys.exit(1)

    use_ci = (not args.no_ci) and len(per_file) == len(models)

    index: dict[tuple[str, str], int] = {}
    for i, m in enumerate(models):
        t = str(m.get("tier", "")).lower()
        p = str(m.get("provider", "")).lower()
        index[(t, p)] = i

    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": FG,
            "text.color": FG,
            "xtick.color": FG,
            "ytick.color": FG,
            "grid.color": "#21262d",
        }
    )

    fig, axes = plt.subplots(
        3,
        3,
        figsize=(15.2, 10.8),
        sharey=True,
        gridspec_kw={"wspace": 0.22, "hspace": 0.38},
    )
    fig.patch.set_facecolor(BG)
    x = np.arange(len(cats))
    bar_w = 0.62

    for ri, tier in enumerate(TIER_ORDER):
        for ci, prov in enumerate(PROV_ORDER):
            ax = axes[ri][ci]
            ax.set_facecolor("#0d1117")
            idx = index.get((tier, prov))
            if idx is None:
                ax.text(0.5, 0.5, "—", ha="center", va="center", color=MUTED, transform=ax.transAxes)
                ax.set_xticks([])
                ax.set_yticks([])
                continue
            row = p_hat[idx]
            ns = n_mat[idx] if idx < len(n_mat) else [0] * len(cats)
            vals = [
                0.0 if v is None or (isinstance(v, float) and not math.isfinite(v)) else float(v) for v in row
            ]
            face = [BAR_POS if v > 1e-9 else BAR_ZERO for v in vals]
            edge = [BAR_POS_EDGE if v > 1e-9 else BAR_ZERO_EDGE for v in vals]
            ax.bar(x, vals, color=face, edgecolor=edge, linewidth=0.85, width=bar_w, zorder=2)

            if use_ci:
                pf = per_file[idx]
                k_list = list(pf.get("unsafe_count_per_category") or [])
                n_list = list(pf.get("n_per_category") or [])
                yerr_lo: list[float] = []
                yerr_hi: list[float] = []
                for j in range(len(cats)):
                    if j >= len(k_list) or j >= len(n_list):
                        yerr_lo.append(0.0)
                        yerr_hi.append(0.0)
                        continue
                    kk, nn = int(k_list[j]), int(n_list[j])
                    lo, hi, _ = wilson_proportion_ci(kk, nn)
                    p = vals[j]
                    yerr_lo.append(max(0.0, p - lo))
                    yerr_hi.append(max(0.0, hi - p))
                ax.errorbar(
                    x,
                    vals,
                    yerr=[yerr_lo, yerr_hi],
                    fmt="none",
                    ecolor=ERR_CAP,
                    elinewidth=1.0,
                    capsize=2.5,
                    capthick=1.0,
                    alpha=0.75,
                    zorder=3,
                )

            ax.set_ylim(0, 1.0)
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
            ax.set_yticklabels(["0", "", "0.5", "", "1"], fontsize=8)
            ax.grid(axis="y", alpha=0.35, linestyle="-", linewidth=0.7)
            ax.set_axisbelow(True)
            if ri == 2:
                ax.set_xticks(x)
                ax.set_xticklabels(cats, rotation=40, ha="right", fontsize=8)
            else:
                ax.set_xticks(x)
                ax.set_xticklabels([])
            m = models[idx]
            n_cat = ns[0] if ns and all(n == ns[0] for n in ns) else 18
            title = f"{m.get('model', '?')}\n({n_cat} prompts/category)"
            ax.set_title(title, fontsize=8, color=FG, pad=6)

    for ci, prov in enumerate(PROV_ORDER):
        axes[0][ci].text(
            0.5,
            1.18,
            prov.upper(),
            transform=axes[0][ci].transAxes,
            ha="center",
            fontsize=11,
            color=FG,
            fontweight="bold",
        )
    for ri, tier in enumerate(TIER_ORDER):
        axes[ri][0].text(
            -0.42,
            0.5,
            tier.upper(),
            transform=axes[ri][0].transAxes,
            va="center",
            ha="right",
            fontsize=11,
            color=FG,
            fontweight="bold",
            rotation=90,
        )

    fig.suptitle(
        r"$\hat P(\mathrm{unsafe}\mid c)$ by category — nine tiered API runs (3×3 design)",
        color=FG,
        fontsize=12,
        fontweight="600",
        y=0.985,
    )
    fig.text(
        0.5,
        0.945,
        "Gemini mid & expensive: model id gemini-2.5-pro (two labeled runs). Bars: Wilson 95% CI when shown."
        if use_ci
        else "Gemini mid & expensive: model id gemini-2.5-pro (two labeled runs).",
        ha="center",
        fontsize=9,
        color=MUTED,
    )

    leg_elems = [
        mlines.Line2D([0], [0], marker="s", color="none", markerfacecolor=BAR_POS, markeredgecolor=BAR_POS_EDGE,
                      markersize=11, label=r"$\hat p_{\mathrm{unsafe}}>0$"),
        mlines.Line2D([0], [0], marker="s", color="none", markerfacecolor=BAR_ZERO, markeredgecolor=BAR_ZERO_EDGE,
                      markersize=11, label=r"$\hat p_{\mathrm{unsafe}}=0$"),
    ]
    if use_ci:
        leg_elems.append(
            mlines.Line2D([0], [0], color=ERR_CAP, linewidth=2, label="Wilson 95% CI"),
        )
    leg = fig.legend(
        handles=leg_elems,
        loc="lower center",
        ncol=3,
        framealpha=0.94,
        facecolor="#161b22",
        edgecolor=GRID,
        fontsize=9,
        bbox_to_anchor=(0.5, -0.02),
    )
    for t in leg.get_texts():
        t.set_color(FG)

    fig.supylabel(r"$\hat P(\mathrm{unsafe})$", color=FG, fontsize=11, x=0.04)
    plt.subplots_adjust(left=0.09, right=0.98, top=0.89, bottom=0.12)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
