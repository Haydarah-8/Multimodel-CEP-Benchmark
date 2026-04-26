"""
Empirical **logit** profiles across categories (variance-stabilizing transform for binomial p).

Uses continuity $\\mathrm{logit}\\bigl(\\frac{k+0.5}{n+1}\\bigr)$ with $n=18$ and observed unsafe counts.

Usage:
  python scripts/plot_multimodel_logit_category_profile.py --matrix-json figures/multimodel/signature_rate_matrix.json
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

COLORS = [
    ACCENT["blue"],
    ACCENT["orange"],
    ACCENT["green"],
    ACCENT["sky"],
    ACCENT["vermillion"],
    "#b59f3b",
    "#6a9fb5",
    "#b07aa1",
    "#9a703e",
]


def emplogit(k: int, n: int) -> float:
    p = (k + 0.5) / (n + 1)
    p = min(1.0 - 1e-9, max(1e-9, p))
    return math.log(p / (1.0 - p))


def short_label(m: dict) -> str:
    t = str(m.get("tier", ""))[:1].upper()
    mod = str(m.get("model", ""))
    return f"{t}:{mod[:16]}{'…' if len(mod) > 16 else ''}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_logit_category_profiles_unsafe.png",
    )
    ap.add_argument("--dpi", type=int, default=220)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    per_file: list[dict] = list(data.get("per_file") or [])

    if len(models) != len(per_file):
        sys.exit("per_file mismatch")

    apply_academic_style(dark=True)
    fig, ax = plt.subplots(figsize=(11, 6.2))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    x = np.arange(len(cats))
    for i, (m, pf) in enumerate(zip(models, per_file, strict=True)):
        k_list = list(pf.get("unsafe_count_per_category") or [])
        n_list = list(pf.get("n_per_category") or [])
        ys = []
        for j in range(len(cats)):
            if j >= len(k_list) or j >= len(n_list):
                ys.append(float("nan"))
            else:
                ys.append(emplogit(int(k_list[j]), int(n_list[j])))
        ax.plot(
            x,
            ys,
            "o-",
            color=COLORS[i % len(COLORS)],
            linewidth=1.9,
            markersize=6,
            label=short_label(m),
            alpha=0.92,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=10)
    ax.axhline(0.0, color="#484f58", linewidth=0.9, linestyle="--", alpha=0.8)
    ax.set_ylabel(r"Empirical logit $\left(\frac{k+0.5}{n+1}\right)$, UNSAFE", fontsize=10.5)
    ax.set_xlabel("Elicitation category", fontsize=10.5)
    ax.set_title(
        "Variance-stabilizing profiles (logit scale)\n"
        r"$n=18$ prompts/category; 0 $\approx$ rate $\approx 50\%$ on the adjusted probability scale.",
        fontsize=11,
        fontweight="600",
    )
    leg = ax.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        framealpha=0.94,
        facecolor="#161b22",
        edgecolor="#30363d",
    )
    for t in leg.get_texts():
        t.set_color("#e6edf3")

    plt.subplots_adjust(left=0.09, right=0.72, top=0.88, bottom=0.14)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
