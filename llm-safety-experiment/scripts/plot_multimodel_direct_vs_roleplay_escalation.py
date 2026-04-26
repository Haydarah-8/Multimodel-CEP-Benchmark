"""
Escalation map: $\\hat P(\\mathrm{unsafe}\\mid \\mathrm{direct})$ vs $\\hat P(\\mathrm{unsafe}\\mid \\mathrm{roleplay})$
for each run. Points above the diagonal show higher unsafe under roleplay than direct (within-run).

Usage:
  python scripts/plot_multimodel_direct_vs_roleplay_escalation.py --matrix-json figures/multimodel/signature_rate_matrix.json
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

PROV_COL = {
    "openai": ACCENT["blue"],
    "anthropic": ACCENT["orange"],
    "gemini": ACCENT["green"],
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_direct_vs_roleplay_escalation.png",
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

    try:
        i_dir = cats.index("direct")
        i_rp = cats.index("roleplay")
    except ValueError:
        print("Need direct and roleplay categories", file=sys.stderr)
        sys.exit(1)

    apply_academic_style(dark=True)
    fig, ax = plt.subplots(figsize=(7.2, 7.0))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    lim = [0, 1.02]
    ax.plot(lim, lim, "--", color="#8b949e", linewidth=1.2, label="y = x (no escalation)")

    for idx, m in enumerate(models):
        row = p_hat[idx] if idx < len(p_hat) else []
        if i_dir >= len(row) or i_rp >= len(row):
            continue
        pd = row[i_dir]
        pr = row[i_rp]
        if pd is None or pr is None:
            continue
        fd, fr = float(pd), float(pr)
        if not (math.isfinite(fd) and math.isfinite(fr)):
            continue
        prov = str(m.get("provider", "")).lower()
        c = PROV_COL.get(prov, "#8b949e")
        tier = str(m.get("tier", ""))[:1].upper()
        ax.scatter(
            [fd],
            [fr],
            s=120,
            c=c,
            edgecolors="#0d1117",
            linewidths=1.0,
            zorder=3,
            alpha=0.9,
        )
        ax.annotate(
            f"{tier}",
            (fd, fr),
            textcoords="offset points",
            xytext=(5, 4),
            fontsize=7,
            color="#e6edf3",
        )

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(r"$\hat P(\mathrm{unsafe}\mid \mathrm{direct})$", fontsize=11)
    ax.set_ylabel(r"$\hat P(\mathrm{unsafe}\mid \mathrm{roleplay})$", fontsize=11)
    ax.set_title(
        "Within-run escalation: direct vs roleplay UNSAFE rates\n"
        "Above diagonal → higher unsafe under roleplay; letters = tier (C/M/E).",
        fontsize=11,
        fontweight="600",
    )

    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=PROV_COL["openai"], markersize=10, label="OpenAI"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=PROV_COL["anthropic"], markersize=10, label="Anthropic"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=PROV_COL["gemini"], markersize=10, label="Gemini"),
        plt.Line2D([0], [0], color="#8b949e", linestyle="--", linewidth=1.5, label="y = x"),
    ]
    leg = ax.legend(handles=handles, loc="upper left", fontsize=9, framealpha=0.94, facecolor="#161b22", edgecolor="#30363d")
    for t in leg.get_texts():
        t.set_color("#e6edf3")

    plt.subplots_adjust(left=0.12, right=0.98, top=0.88, bottom=0.1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
