"""
Bar chart: sensitivity RR_unsafe (vs direct) for emotional, indirect, escalation.

Reads JSON from compute_category_stress_indices.py. Dark theme aligned with generate_report_figures.

Usage:
  python scripts/plot_category_stress.py --indices-json results/pilot/category_stress_indices.json
  python scripts/plot_category_stress.py --results results/pilot/results.json
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
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from compute_category_stress_indices import compute_indices  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#f0883e"
LINE = "#58a6ff"


def load_indices(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--indices-json", type=Path, default=None)
    ap.add_argument("--results", type=Path, default=None)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="PNG path (default: next to indices JSON or results)",
    )
    args = ap.parse_args()

    if args.indices_json:
        data = load_indices(args.indices_json)
        base = args.indices_json.parent
    elif args.results:
        data = compute_indices(args.results)
        base = args.results.parent
    else:
        print("Provide --indices-json or --results", file=sys.stderr)
        sys.exit(1)

    sens = data.get("sensitivity_vs_direct") or {}
    cats = ["emotional", "indirect", "escalation"]
    labels = [c.capitalize() for c in cats]
    vals = []
    for c in cats:
        v = sens.get(c, {}).get("RR_unsafe_vs_direct")
        vals.append(float(v) if v is not None else 0.0)

    out = args.out
    if out is None:
        out = base / "fig_category_stress_RR_unsafe.png"

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(cats))
    ax.bar(x, vals, color=ACCENT, width=0.55, edgecolor=MUTED, linewidth=0.8)
    ax.axhline(1.0, color=LINE, linestyle="--", linewidth=1.0, alpha=0.9, label="RR = 1 (parity with direct UNSAFE)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=FG, fontsize=11)
    ax.set_ylabel("RR_unsafe vs direct", color=FG, fontsize=11)
    ax.tick_params(axis="y", colors=FG)
    ax.spines["bottom"].set_color(MUTED)
    ax.spines["left"].set_color(MUTED)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Category stress: UNSAFE rate relative to direct baseline", color=FG, fontsize=12)
    ax.legend(facecolor=BG, edgecolor=MUTED, labelcolor=FG, fontsize=9, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=MUTED)

    cpi = data.get("coercion_pressure_index_CPI") or {}
    foot = (
        f"CPI_delta_risk(esc-direct)={cpi.get('delta_p_risk_escalation_minus_direct', 0):.3f}  "
        f"roleplay_amp={data.get('roleplay_amplification_factor', 0):.2f}x"
    )
    fig.text(0.5, 0.02, foot, ha="center", fontsize=9, color=MUTED)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.18)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
