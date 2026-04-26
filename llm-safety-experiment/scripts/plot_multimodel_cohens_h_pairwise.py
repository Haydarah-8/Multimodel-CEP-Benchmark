"""
Symmetric heatmap of **Cohen's h** for overall UNSAFE rate between each pair of runs.

$h = 2\\bigl(\\arcsin\\sqrt{p_1} - \\arcsin\\sqrt{p_2}\\bigr)$ (arcsin square-root transform).

Usage:
  python scripts/plot_multimodel_cohens_h_pairwise.py --root results/multimodel
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from academic_plot_style import DEFAULT_DPI, apply_academic_style  # noqa: E402
from paths import MULTIMODEL_DIR  # noqa: E402

VALID = frozenset({"safe", "partial", "unsafe"})


def discover(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("results_*.json") if "archive" not in p.parts)


def overall_p_unsafe(path: Path) -> tuple[float, str]:
    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    labeled = [r for r in rows if str(r.get("label") or "").strip().lower() in VALID]
    if not labeled:
        return 0.0, path.stem
    u = sum(1 for r in labeled if str(r.get("label")).lower() == "unsafe")
    p = u / len(labeled)
    tier = next((t for t in ("cheap", "mid", "expensive") if t in {x.lower() for x in path.parts}), "?")
    prov = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
    model = next((str(r.get("model")) for r in rows if r.get("model")), path.stem)
    return p, f"{tier}|{prov}|{model}"


def cohens_h(p1: float, p2: float) -> float:
    p1 = min(1.0, max(0.0, p1))
    p2 = min(1.0, max(0.0, p2))
    return 2.0 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_cohens_h_pairwise_overall.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    files = discover(args.root)
    if len(files) < 2:
        sys.exit("Need ≥2 results")

    ps: list[float] = []
    labels: list[str] = []
    for fp in files:
        p, lab = overall_p_unsafe(fp)
        ps.append(p)
        labels.append(lab)

    n = len(ps)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                H[i, j] = 0.0
            else:
                H[i, j] = cohens_h(ps[i], ps[j])

    vmax = max(0.35, float(np.nanmax(np.abs(H))) if H.size else 0.35)
    apply_academic_style(dark=True)
    cmap = LinearSegmentedColormap.from_list(
        "divh",
        ["#1e4a6e", "#2d3d48", "#2a2a2a", "#4a3028", "#8f4a28", "#c45c3a"],
        N=256,
    )

    fig, ax = plt.subplots(figsize=(max(10, 0.55 * n), max(9, 0.5 * n)))
    fig.patch.set_facecolor("#0d1117")
    Hplot = ma.masked_where(np.eye(n, dtype=bool), H)
    im = ax.imshow(Hplot, cmap=cmap, aspect="auto", vmin=-vmax, vmax=vmax, interpolation="nearest")
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(labels, rotation=75, ha="right", fontsize=7)
    ax.set_yticklabels(labels, fontsize=7)

    for i in range(n):
        for j in range(n):
            if i == j:
                ax.text(j, i, "—", ha="center", va="center", color="#8b949e", fontsize=7)
            else:
                ax.text(
                    j,
                    i,
                    f"{H[i, j]:+.2f}",
                    ha="center",
                    va="center",
                    color="#f0f3f6" if abs(H[i, j]) > 0.5 * vmax else "#e6edf3",
                    fontsize=6,
                )

    ax.set_title(
        r"Cohen's $h$ (overall UNSAFE rate): row $-$ column"
        "\nArcsin $\\sqrt{p}$ effect size; symmetric except sign.",
        fontsize=11,
        fontweight="600",
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label(r"Cohen's $h$", color="#e6edf3", fontsize=9)
    cbar.ax.yaxis.set_tick_params(colors="#e6edf3")

    fig.text(
        0.5,
        0.02,
        "Descriptive pairwise contrasts; not adjusted for multiple comparisons.",
        ha="center",
        fontsize=8,
        color="#8b949e",
    )
    plt.subplots_adjust(left=0.26, right=0.9, bottom=0.28, top=0.9)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
