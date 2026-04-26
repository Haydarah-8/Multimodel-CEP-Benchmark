"""
Forest plot: Wilson 95% CIs for each model × category cell (from signature_rate_matrix.json).

Uses exact counts in per_file (unsafe_count_per_category or risk_count_per_category).

Usage:
  python scripts/plot_multimodel_forest_wilson.py --matrix-json figures/multimodel/signature_rate_matrix.json
  python scripts/plot_multimodel_forest_wilson.py --matrix-json figures/multimodel/signature_rate_matrix_risk.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from academic_plot_style import DEFAULT_DPI  # noqa: E402


from stats_utils import wilson_proportion_ci  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"

PROVIDER_COLORS = {
    "openai": "#58a6ff",
    "anthropic": "#c297ff",
    "gemini": "#3fb950",
}


def short_label(m: dict) -> str:
    tier = str(m.get("tier", ""))[:1].upper()
    model = str(m.get("model", ""))
    if len(model) > 22:
        model = model[:19] + "…"
    return f"[{tier}] {model}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    per_file: list[dict] = list(data.get("per_file") or [])
    metric = str(data.get("metric", "unsafe"))

    if len(per_file) != len(models):
        print("per_file length must match models", file=sys.stderr)
        sys.exit(1)

    use_risk = metric == "risk"
    n_facet = len(cats)
    fig, axes = plt.subplots(1, n_facet, figsize=(4.2 * n_facet, 8.0), sharex=True)
    if n_facet == 1:
        axes = [axes]
    fig.patch.set_facecolor(BG)

    for fi, cat in enumerate(cats):
        ax = axes[fi]
        ax.set_facecolor(BG)
        ys = np.arange(len(models))
        for i, (m, pf) in enumerate(zip(models, per_file, strict=True)):
            n_per = list(pf.get("n_per_category") or [])
            if use_risk:
                counts = list(pf.get("risk_count_per_category") or [])
            else:
                counts = list(pf.get("unsafe_count_per_category") or [])
            if fi >= len(n_per) or fi >= len(counts):
                continue
            n = int(n_per[fi])
            k = int(counts[fi])
            lo, hi, _ = wilson_proportion_ci(k, n)
            prov = str(m.get("provider", "")).lower()
            c = PROVIDER_COLORS.get(prov, MUTED)
            ax.plot([lo, hi], [i, i], color=c, linewidth=2.2, solid_capstyle="round", zorder=2)
            phat = k / n if n else 0.0
            ax.scatter([phat], [i], color=c, s=36, zorder=3, edgecolors=BG, linewidths=0.8)

        ax.set_yticks(ys)
        ax.set_yticklabels([short_label(m) for m in models], fontsize=7, color=FG)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.6, len(models) - 0.4)
        ax.axvline(0, color=GRID, linewidth=0.8)
        ax.set_title(cat, color=FG, fontsize=11, fontweight="600")
        ax.tick_params(axis="x", colors=FG, labelsize=8)
        ax.grid(axis="x", color=GRID, alpha=0.45)
        for spine in ax.spines.values():
            spine.set_color(GRID)

    metric_label = "risk (P∪U)" if use_risk else "unsafe"
    fig.suptitle(
        f"Forest plot: Wilson 95% CI for $\\hat P(\\mathrm{{{metric_label}}} \\mid c)$ by run",
        color=FG,
        fontsize=13,
        fontweight="600",
        y=0.98,
    )
    fig.text(
        0.5,
        0.94,
        "n=18 per category; nine runs; Gemini mid/expensive = same model id; exploratory.",
        ha="center",
        fontsize=8,
        color=MUTED,
    )
    fig.supxlabel("Probability", color=FG, fontsize=10)
    plt.subplots_adjust(left=0.22, right=0.98, top=0.88, bottom=0.08, wspace=0.35)

    out = args.out
    if out is None:
        suf = "risk" if use_risk else "unsafe"
        out = ROOT / "figures" / "multimodel" / f"combined_forest_wilson_{suf}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
