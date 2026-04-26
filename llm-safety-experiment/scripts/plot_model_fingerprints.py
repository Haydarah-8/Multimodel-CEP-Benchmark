"""
Plot model fingerprint curves (refusal vs compliance) from model_fingerprint.json.

Dark theme aligned with generate_report_figures.py.

Usage:
  python scripts/plot_model_fingerprints.py --fingerprint-json results/pilot/model_fingerprint.json
  python scripts/plot_model_fingerprints.py --fingerprint-json <path> --out figures/fingerprint_curves.png
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

# Match generate_report_figures dark theme
BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
SAFE_COLOR = "#238636"
UNSAFE_COLOR = "#da3633"
RISK_COLOR = "#d29922"


def load_fp(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fingerprint-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="PNG path (default: same dir as JSON, fig_model_fingerprint_curves.png)",
    )
    args = ap.parse_args()

    if not args.fingerprint_json.is_file():
        print(f"Missing {args.fingerprint_json}", file=sys.stderr)
        sys.exit(1)

    data = load_fp(args.fingerprint_json)
    curves = data.get("curves") or {}
    cats = curves.get("categories") or []
    refusal = curves.get("refusal") or curves.get("refusal_p_safe") or []
    comp = curves.get("compliance_unsafe") or curves.get("compliance_p_unsafe") or []
    risk = curves.get("risk") or curves.get("risk_p_R") or []
    n_list = curves.get("n") or []

    if not cats or len(refusal) != len(cats):
        print("Invalid fingerprint JSON: missing curves.categories / refusal", file=sys.stderr)
        sys.exit(1)

    x = np.arange(len(cats))
    width = 0.36

    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": FG,
            "text.color": FG,
            "xtick.color": FG,
            "ytick.color": FG,
            "grid.color": MUTED,
            "grid.alpha": 0.35,
        }
    )

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    fig.patch.set_facecolor(BG)

    title_bits = []
    if data.get("model"):
        title_bits.append(str(data["model"]))
    if data.get("provider"):
        title_bits.append(str(data["provider"]))
    title = "Model fingerprint — " + " · ".join(title_bits) if title_bits else "Model fingerprint"

    # Panel 1: refusal (P safe) vs risk (P partial ∪ unsafe)
    ax1.bar(x - width / 2, refusal, width, label=r"$\hat P(\mathrm{safe}\mid c)$", color=SAFE_COLOR, edgecolor=FG, linewidth=0.4)
    ax1.bar(x + width / 2, risk, width, label=r"$\hat R(c)=\hat P(\mathrm{partial}\cup\mathrm{unsafe}\mid c)$", color=RISK_COLOR, edgecolor=FG, linewidth=0.4)
    ax1.set_ylabel("Probability")
    ax1.set_ylim(0, 1.05)
    ax1.legend(loc="upper right", framealpha=0.2)
    ax1.set_title(title, color=FG, fontsize=11)
    ax1.grid(True, axis="y", linestyle="--")

    # Panel 2: UNSAFE compliance
    ax2.bar(x, comp, width * 1.4, label=r"$\hat P(\mathrm{unsafe}\mid c)$", color=UNSAFE_COLOR, edgecolor=FG, linewidth=0.4)
    ax2.set_xticks(x)
    if n_list and len(n_list) == len(cats):
        xlabels = [f"{c}\n(n={n_list[i]})" for i, c in enumerate(cats)]
    else:
        xlabels = list(cats)
    ax2.set_xticklabels(xlabels, fontsize=8)
    ax2.set_xlabel("Category (taxonomy order)")
    ax2.set_ylabel(r"$\hat P(\mathrm{unsafe}\mid c)$")
    ymax = max(comp) if comp else 0.0
    ax2.set_ylim(0, max(0.08, float(ymax) * 1.15) if ymax > 0 else 1.0)
    ax2.legend(loc="upper right", framealpha=0.2)
    ax2.grid(True, axis="y", linestyle="--")

    fig.tight_layout()
    out = args.out or (args.fingerprint_json.parent / "fig_model_fingerprint_curves.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
