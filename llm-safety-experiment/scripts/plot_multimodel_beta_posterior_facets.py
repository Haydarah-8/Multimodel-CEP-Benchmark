"""
Bayesian Beta–Binomial (Jeffreys prior) 95% **credible intervals** per run × category.

Each cell: posterior Beta(k+½, n−k+½) given observed unsafe count k of n=18.
Facets = elicitation categories; horizontal intervals with posterior mean marker.

Usage:
  python scripts/plot_multimodel_beta_posterior_facets.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from academic_plot_style import ACCENT, DEFAULT_DPI, apply_academic_style  # noqa: E402


def short_label(m: dict) -> str:
    t = str(m.get("tier", ""))[:1].upper()
    mod = str(m.get("model", ""))
    if len(mod) > 20:
        mod = mod[:18] + "…"
    return f"{t}:{mod}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_beta_posterior_unsafe_facets.png",
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

    if len(models) != len(per_file):
        sys.exit("per_file must match models")

    apply_academic_style(dark=True)
    n_models = len(models)
    n_cat = len(cats)
    fig, axes = plt.subplots(1, n_cat, figsize=(4.0 * n_cat, max(7, 0.38 * n_models)), sharex=True)
    if n_cat == 1:
        axes = [axes]
    fig.patch.set_facecolor("#0d1117")

    colors = [ACCENT["blue"], ACCENT["orange"], ACCENT["green"], ACCENT["sky"], ACCENT["vermillion"]]

    for fi, cat in enumerate(cats):
        ax = axes[fi]
        ax.set_facecolor("#0d1117")
        y = np.arange(n_models)
        for i, (m, pf) in enumerate(zip(models, per_file, strict=True)):
            k_list = list(pf.get("unsafe_count_per_category") or [])
            n_list = list(pf.get("n_per_category") or [])
            if fi >= len(k_list) or fi >= len(n_list):
                continue
            k, n = int(k_list[fi]), int(n_list[fi])
            a = k + 0.5
            bpar = n - k + 0.5
            lo, hi = beta.ppf([0.025, 0.975], a, bpar)
            mean = a / (a + bpar)
            c = colors[i % len(colors)]
            ax.plot([lo, hi], [i, i], color=c, linewidth=2.4, solid_capstyle="round", alpha=0.9)
            ax.scatter([mean], [i], color=c, s=42, zorder=3, edgecolors="#0d1117", linewidths=0.8)

        ax.set_yticks(y)
        ax.set_yticklabels([short_label(m) for m in models], fontsize=8)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.6, n_models - 0.4)
        ax.set_title(cat, fontsize=11, fontweight="600", pad=8)
        ax.tick_params(axis="x", labelsize=8)
        ax.axvline(0, color="#30363d", linewidth=0.7)

    fig.suptitle(
        r"Jeffreys Beta–Binomial posterior for $P(\mathrm{unsafe}\mid c)$ — 95% credible intervals"
        "\nPoint = posterior mean; n=18 prompts/stratum.",
        fontsize=12,
        fontweight="600",
        y=1.02,
    )
    fig.text(0.52, 0.02, "Probability", ha="center", fontsize=10.5, color="#e6edf3")
    plt.subplots_adjust(left=0.2, right=0.98, top=0.88, bottom=0.14, wspace=0.35)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
