"""
Horizontal stacked bars: SAFE / PARTIAL / UNSAFE shares per multimodel run.

Usage:
  python scripts/plot_multimodel_label_composition.py --root results/multimodel
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
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from academic_plot_style import DEFAULT_DPI  # noqa: E402


from paths import MULTIMODEL_DIR  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"
SAFE_C = "#238636"
PARTIAL_C = "#9e6a03"
UNSAFE_C = "#da3633"


VALID = frozenset({"safe", "partial", "unsafe"})


def discover(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("results_*.json"))


def tier_from_path(p: Path) -> str:
    parts = {x.lower() for x in p.parts}
    for t in ("cheap", "mid", "expensive"):
        if t in parts:
            return t
    return "?"


def counts_for_file(path: Path) -> tuple[str, dict[str, int], int]:
    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    labeled = [r for r in rows if str(r.get("label", "")).strip().lower() in VALID]
    c = {"safe": 0, "partial": 0, "unsafe": 0}
    for r in labeled:
        c[str(r.get("label")).lower()] += 1
    model = next((str(r.get("model")) for r in rows if r.get("model")), path.stem)
    prov = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
    tier = tier_from_path(path)
    label = f"[{tier}] {prov}/{model}"
    return label, c, len(labeled)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "combined_label_composition_stacked.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    files = discover(args.root)
    if not files:
        print(f"No results under {args.root}", file=sys.stderr)
        sys.exit(1)

    rows_data: list[tuple[str, dict[str, int], int]] = [counts_for_file(p) for p in files]
    rows_data.sort(key=lambda x: -x[1]["unsafe"] / max(1, x[2]))

    labels = [t[0] for t in rows_data]
    n = len(labels)
    safe = np.array([t[1]["safe"] / t[2] if t[2] else 0 for t in rows_data])
    partial = np.array([t[1]["partial"] / t[2] if t[2] else 0 for t in rows_data])
    unsafe = np.array([t[1]["unsafe"] / t[2] if t[2] else 0 for t in rows_data])

    fig_h = max(5.5, 0.38 * n)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    y = np.arange(n)

    ax.barh(y, safe, color=SAFE_C, label="SAFE", height=0.72)
    ax.barh(y, partial, left=safe, color=PARTIAL_C, label="PARTIAL", height=0.72)
    ax.barh(y, unsafe, left=safe + partial, color=UNSAFE_C, label="UNSAFE", height=0.72)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8, color=FG)
    ax.set_xlabel("Share of labeled rows", color=FG, fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_title(
        "Label composition per API run (sorted by % UNSAFE)",
        color=FG,
        fontsize=12,
        fontweight="600",
        pad=10,
    )
    ax.tick_params(axis="x", colors=FG)
    ax.grid(axis="x", color=GRID, alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    leg = ax.legend(loc="lower right", framealpha=0.92, facecolor="#161b22", edgecolor=GRID)
    for t in leg.get_texts():
        t.set_color(FG)

    fig.text(
        0.5,
        0.01,
        "Nine runs; eight unique provider×model-id (Gemini mid/expensive same SKU).",
        ha="center",
        fontsize=8,
        color=MUTED,
    )
    plt.subplots_adjust(left=0.34, right=0.96, bottom=0.1, top=0.94)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
