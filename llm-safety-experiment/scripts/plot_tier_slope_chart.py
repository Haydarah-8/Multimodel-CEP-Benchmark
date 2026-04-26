"""
Tier ladder: within each provider, connect cheap → mid → expensive overall % unsafe and % risk.

Uses per_file aggregates from signature_rate_matrix.json (sums counts / 90).

Usage:
  python scripts/plot_tier_slope_chart.py --matrix-json figures/multimodel/signature_rate_matrix.json
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

TIER_X = {"cheap": 0, "mid": 1, "expensive": 2}
TIER_LABELS = ["cheap", "mid", "expensive"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_tier_slope_overall_rates.png",
    )
    ap.add_argument("--dpi", type=int, default=180)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    models: list[dict] = list(data.get("models") or [])
    per_file: list[dict] = list(data.get("per_file") or [])

    if len(models) != len(per_file):
        sys.exit("models/per_file mismatch")

    by_prov: dict[str, list[tuple[str, float, float]]] = {}
    for m, pf in zip(models, per_file, strict=True):
        prov = str(m.get("provider", "")).lower()
        tier = str(m.get("tier", "")).lower()
        u = sum(int(x) for x in (pf.get("unsafe_count_per_category") or []))
        r = sum(int(x) for x in (pf.get("risk_count_per_category") or []))
        ntot = int(pf.get("n_labeled_total") or 90)
        if ntot <= 0:
            continue
        pu, pr = u / ntot, r / ntot
        by_prov.setdefault(prov, []).append((tier, pu, pr))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5))
    fig.patch.set_facecolor(BG)
    for ax in (ax1, ax2):
        ax.set_facecolor(BG)

    xs = np.arange(3)
    for prov, triples in sorted(by_prov.items()):
        c = PROVIDER_COLORS.get(prov, MUTED)
        triples = sorted(triples, key=lambda t: TIER_X.get(t[0], 0))
        if len(triples) < 3:
            continue
        pu_y = [t[1] for t in triples]
        pr_y = [t[2] for t in triples]
        ax1.plot(xs, pu_y, "o-", color=c, linewidth=2, markersize=8, label=prov)
        ax2.plot(xs, pr_y, "s--", color=c, linewidth=2, markersize=7, label=prov)

    for ax, title, ylab in (
        (ax1, "Overall % UNSAFE (tier ladder)", r"$\hat P(\mathrm{unsafe})$"),
        (ax2, "Overall % risk PARTIAL∪UNSAFE", r"$\hat P(\mathrm{risk})$"),
    ):
        ax.set_xticks(xs)
        ax.set_xticklabels(TIER_LABELS, color=FG, fontsize=10)
        ax.set_ylabel(ylab, color=FG, fontsize=10)
        ax.set_title(title, color=FG, fontsize=11, fontweight="600")
        ax.tick_params(axis="y", colors=FG)
        ax.set_ylim(-0.02, 1.02)
        ax.grid(True, color=GRID, alpha=0.45)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        leg = ax.legend(loc="upper left", framealpha=0.9, facecolor="#161b22", edgecolor=GRID)
        for t in leg.get_texts():
            t.set_color(FG)

    fig.text(
        0.5,
        0.02,
        "Gemini mid & expensive use the same model id; slopes may still differ slightly between two runs.",
        ha="center",
        fontsize=8,
        color=MUTED,
    )
    plt.subplots_adjust(bottom=0.18, wspace=0.25)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
