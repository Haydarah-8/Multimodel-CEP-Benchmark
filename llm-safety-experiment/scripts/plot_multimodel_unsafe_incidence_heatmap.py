"""
Binary incidence matrix: **prompts × runs** (UNSAFE = 1). Rows sorted by how many runs flagged UNSAFE.

Shows which items drive cross-model disagreement vs consensus.

Usage:
  python scripts/plot_multimodel_unsafe_incidence_heatmap.py --root results/multimodel
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

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


def load_row_meta_and_unsafe(path: Path) -> tuple[dict[int, tuple[str, int]], str]:
    """id -> (category, unsafe01), column label."""
    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    out: dict[int, tuple[str, int]] = {}
    for r in rows:
        try:
            pid = int(r["id"])
        except (TypeError, ValueError, KeyError):
            continue
        lab = str(r.get("label") or "").strip().lower()
        if lab not in VALID:
            continue
        cat = str(r.get("category") or "").strip().lower()
        out[pid] = (cat, 1 if lab == "unsafe" else 0)
    tier = next((t for t in ("cheap", "mid", "expensive") if t in {x.lower() for x in path.parts}), "?")
    prov = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
    model = next((str(r.get("model")) for r in rows if r.get("model")), path.stem)
    return out, f"{tier[:1].upper()}:{prov[:3]}:{model[:12]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "phd_unsafe_incidence_prompts_by_run.png",
    )
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    args = ap.parse_args()

    files = discover(args.root)
    if len(files) < 2:
        sys.exit("Need ≥2 results")

    col_labels: list[str] = []
    matrices: list[dict[int, int]] = []
    cat_by_id: dict[int, str] = {}
    for fp in files:
        meta, clab = load_row_meta_and_unsafe(fp)
        col_labels.append(clab)
        m = {pid: t[1] for pid, t in meta.items()}
        matrices.append(m)
        for pid, t in meta.items():
            cat_by_id.setdefault(pid, t[0])

    common = set.intersection(*(set(m) for m in matrices))
    ids = sorted(common)

    Z = np.zeros((len(ids), len(matrices)), dtype=float)
    for j, m in enumerate(matrices):
        for i, pid in enumerate(ids):
            Z[i, j] = float(m.get(pid, 0))

    row_sum = Z.sum(axis=1)
    order = np.argsort(-row_sum, kind="stable")
    Z = Z[order, :]
    ids_ord = [ids[i] for i in order]
    row_labels = [f"id {ids_ord[i]} · {cat_by_id[ids_ord[i]]}" for i in range(len(ids_ord))]

    apply_academic_style(dark=True)
    fig_h = max(10, 0.11 * len(ids))
    fig, ax = plt.subplots(figsize=(10, fig_h))
    fig.patch.set_facecolor("#0d1117")
    cmap = ListedColormap(["#161b22", "#c45c4a"])

    im = ax.imshow(Z, aspect="auto", cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=55, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=6)
    ax.set_xlabel("Model run", fontsize=10)
    ax.set_ylabel("Prompt (sorted by # runs UNSAFE, desc.)", fontsize=10)
    ax.set_title(
        "UNSAFE incidence: prompts × runs (binary)\nShared prompt ids; dark = not unsafe, rust = UNSAFE",
        fontsize=11,
        fontweight="600",
    )

    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02, ticks=[0, 1])
    cbar.ax.set_yticklabels(["not UNSAFE", "UNSAFE"], color="#e6edf3", fontsize=8)

    plt.subplots_adjust(left=0.14, right=0.92, top=0.94, bottom=0.2)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=args.dpi, facecolor="#0d1117", edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
