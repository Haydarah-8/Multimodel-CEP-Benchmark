"""
Histogram: for each prompt id, how many of the multimodel runs labeled it **UNSAFE**?

Summarizes cross-model concordance on the same 90 prompts (k = 0..9).

Usage:
  python scripts/plot_multimodel_unsafe_concordance.py --root results/multimodel
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

from academic_plot_style import DEFAULT_DPI, apply_academic_style  # noqa: E402
from paths import MULTIMODEL_DIR  # noqa: E402

VALID = frozenset({"safe", "partial", "unsafe"})


def discover(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("results_*.json") if "archive" not in p.parts)


def load_unsafe_by_id(path: Path) -> dict[int, int]:
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
        out[pid] = 1 if lab == "unsafe" else 0
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_unsafe_concordance_histogram.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    files = discover(args.root)
    if len(files) < 2:
        print("Need ≥2 labeled results JSON", file=sys.stderr)
        sys.exit(1)

    maps = [load_unsafe_by_id(fp) for fp in files]
    common = set.intersection(*(set(m) for m in maps))
    if not common:
        print("No overlapping prompt ids", file=sys.stderr)
        sys.exit(1)

    ks = [sum(mi[pid] for mi in maps) for pid in sorted(common)]

    apply_academic_style(dark=True)
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    counts = np.bincount(np.array(ks, dtype=int), minlength=len(maps) + 1)
    x = np.arange(len(maps) + 1)
    ax.bar(x, counts, color="#4a6fa5", edgecolor="#7aa2d6", linewidth=0.8, width=0.82)
    for i, (xi, h) in enumerate(zip(x, counts)):
        if h > 0:
            ax.text(xi, h + 0.35, str(int(h)), ha="center", va="bottom", color="#e6edf3", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels([str(i) for i in x])
    ax.set_xlabel(r"$k$ = number of runs with UNSAFE (same prompt $id$)", fontsize=10.5)
    ax.set_ylabel("Number of prompts", fontsize=10.5)
    ax.set_title(
        f"Cross-model concordance on UNSAFE\n{len(maps)} runs, {len(common)} shared prompts",
        fontsize=12,
        fontweight="600",
    )
    fig.text(
        0.5,
        0.02,
        "k=0: no run unsafe; k=9: all runs unsafe on that prompt.",
        ha="center",
        fontsize=8,
        color="#8b949e",
    )
    plt.subplots_adjust(bottom=0.18)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
