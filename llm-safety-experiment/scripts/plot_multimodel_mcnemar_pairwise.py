"""
Paired McNemar tests: compare UNSAFE (or risk) labels across model runs on the **same** prompt ids.

Builds a 9×9 matrix of two-sided exact p-values (discordant pairs; Binomial test at 0.5).
Off-diagonal asymmetry: cell (i,j) tests row model vs column model (direction matters for b/c).

Usage:
  python scripts/plot_multimodel_mcnemar_pairwise.py --root results/multimodel
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from academic_plot_style import ACCENT, DEFAULT_DPI, apply_academic_style  # noqa: E402
from paths import MULTIMODEL_DIR  # noqa: E402

VALID = frozenset({"safe", "partial", "unsafe"})


def tier_from_path(p: Path) -> str:
    parts = {x.lower() for x in p.parts}
    for t in ("cheap", "mid", "expensive"):
        if t in parts:
            return t
    return "?"


def load_binary_by_id(path: Path, *, risk: bool) -> dict[int, int]:
    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    out: dict[int, int] = {}
    for r in rows:
        try:
            pid = int(r["id"])
        except (TypeError, ValueError, KeyError):
            continue
        lab = str(r.get("label") or "").strip().lower()
        if lab not in VALID:
            continue
        if risk:
            y = 1 if lab in ("partial", "unsafe") else 0
        else:
            y = 1 if lab == "unsafe" else 0
        out[pid] = y
    return out


def mcnemar_exact_two_sided(b: int, c: int) -> float:
    """Discordant counts: b = only first unsafe; c = only second unsafe."""
    n = b + c
    if n == 0:
        return 1.0
    return float(binomtest(b, n, 0.5, alternative="two-sided").pvalue)


def label_for_path(p: Path, rows: list[dict]) -> str:
    tier = tier_from_path(p)
    prov = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
    model = next((str(r.get("model")) for r in rows if r.get("model")), p.stem)
    return f"{tier}|{prov}|{model}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_mcnemar_pairwise_pvalues.png",
    )
    ap.add_argument(
        "--metric",
        choices=("unsafe", "risk"),
        default="unsafe",
        help="Binary outcome: strict UNSAFE vs risk (PARTIAL∪UNSAFE)",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    files = sorted(args.root.rglob("results_*.json"))
    files = [p for p in files if "archive" not in p.parts]
    if len(files) < 2:
        print("Need ≥2 results JSON", file=sys.stderr)
        sys.exit(1)

    risk = args.metric == "risk"
    labels: list[str] = []
    binaries: list[dict[int, int]] = []
    for fp in files:
        with fp.open(encoding="utf-8") as f:
            rows = json.load(f)
        if not isinstance(rows, list):
            continue
        labels.append(label_for_path(fp, rows))
        binaries.append(load_binary_by_id(fp, risk=risk))

    n = len(labels)
    p_mat = np.full((n, n), np.nan)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a = binaries[i]
            bmap = binaries[j]
            common = set(a) & set(bmap)
            discord_ij = sum(1 for k in common if a[k] == 1 and bmap[k] == 0)
            discord_ji = sum(1 for k in common if a[k] == 0 and bmap[k] == 1)
            p_mat[i, j] = mcnemar_exact_two_sided(discord_ij, discord_ji)

    apply_academic_style(dark=True)
    display = np.where(
        np.isfinite(p_mat),
        -np.log10(np.clip(p_mat, 1e-12, 1.0)),
        np.nan,
    )

    cmap = LinearSegmentedColormap.from_list(
        "sig",
        ["#1a2332", "#2d4a66", ACCENT["orange"], "#ff6b4a"],
        N=256,
    )

    fig_w = max(11, 0.55 * n)
    fig_h = max(10, 0.52 * n)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor("#0d1117")
    display_ma = np.ma.masked_invalid(display)
    im = ax.imshow(display_ma, cmap=cmap, aspect="auto", vmin=0, vmax=4, interpolation="nearest")

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(labels, rotation=75, ha="right", fontsize=7)
    ax.set_yticklabels(labels, fontsize=7)

    for i in range(n):
        for j in range(n):
            if i == j:
                ax.text(j, i, "—", ha="center", va="center", color="#8b949e", fontsize=8)
            else:
                pv = p_mat[i, j]
                star = ""
                if pv < 0.001:
                    star = "***"
                elif pv < 0.01:
                    star = "**"
                elif pv < 0.05:
                    star = "*"
                ax.text(
                    j,
                    i,
                    f"{pv:.3f}\n{star}".strip(),
                    ha="center",
                    va="center",
                    color="#f0f3f6" if display[i, j] > 2 else "#e6edf3",
                    fontsize=6,
                )

    metric_l = "UNSAFE" if not risk else "risk (P∪U)"
    ax.set_title(
        f"Paired McNemar (exact): row vs col on binary {metric_l}\n"
        r"Same prompt $id$; cells = two-sided $p$; $*$ $\alpha$=0.05, ** 0.01, *** 0.001",
        fontsize=11,
        pad=12,
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label(r"$-\log_{10}(p)$", fontsize=9, color="#e6edf3")
    cbar.ax.yaxis.set_tick_params(colors="#e6edf3")

    fig.text(
        0.5,
        0.02,
        "Asymmetric: ordering (i,j) follows discordant counts b(i unsafe only) vs c(j unsafe only).",
        ha="center",
        fontsize=8,
        color="#8b949e",
    )
    plt.subplots_adjust(left=0.28, right=0.88, bottom=0.28, top=0.88)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
