"""
Category clustering view: heatmap of failure-mode (or label) profiles + dendrogram.

Primary: category × failure_mode proportions, Jensen–Shannon distance, average linkage.
Fallback: category × (safe, partial, unsafe) if too few rows have failure_mode.

See INTERPRETABILITY_VIZ.md.

Usage:
  python scripts/plot_failure_mode_category_heatmap.py --results results/pilot/results.json
  python scripts/plot_failure_mode_category_heatmap.py --results results/multimodel/cheap/results_openai_gpt-4o-mini.json --out-png figures/fm_category.png
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage
from scipy.spatial.distance import jensenshannon, squareform

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from compute_significance import CAT_ORDER  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"

MIN_FM_ABSOLUTE = 10
MIN_FM_FRACTION = 0.05


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("results must be JSON array")
    return data


def build_fm_matrix(
    rows: list[dict[str, Any]],
) -> tuple[np.ndarray, list[str], list[str], str]:
    """
    Returns P (n_cat x n_col), row_labels (categories present), col_labels, mode tag.
    """
    n = len(rows)
    fm_count = sum(1 for r in rows if str(r.get("failure_mode") or "").strip())
    use_fm = fm_count >= MIN_FM_ABSOLUTE and (n == 0 or fm_count / n >= MIN_FM_FRACTION)

    cat_to_idx = {c: i for i, c in enumerate(CAT_ORDER)}
    if use_fm:
        cols_set: dict[str, int] = {}
        counts: dict[str, dict[str, int]] = {c: defaultdict(int) for c in CAT_ORDER}
        cat_totals = {c: 0 for c in CAT_ORDER}
        for r in rows:
            cat = str(r.get("category") or "").strip().lower()
            if cat not in cat_to_idx:
                continue
            fm = str(r.get("failure_mode") or "").strip()
            if not fm:
                fm = "(uncoded)"
            cols_set.setdefault(fm, 0)
            counts[cat][fm] += 1
            cat_totals[cat] += 1
        col_labels = sorted(cols_set.keys())
        col_index = {c: i for i, c in enumerate(col_labels)}
        row_labels = [c for c in CAT_ORDER if cat_totals[c] > 0]
        P = np.zeros((len(row_labels), len(col_labels)), dtype=float)
        for i, cat in enumerate(row_labels):
            tot = cat_totals[cat]
            if tot <= 0:
                continue
            for fm, k in counts[cat].items():
                if fm in col_index:
                    P[i, col_index[fm]] = k / tot
        return P, row_labels, col_labels, "failure_mode"
    # fallback: label distribution
    col_labels = ["safe", "partial", "unsafe"]
    counts = {c: {"safe": 0, "partial": 0, "unsafe": 0} for c in CAT_ORDER}
    cat_totals = {c: 0 for c in CAT_ORDER}
    for r in rows:
        cat = str(r.get("category") or "").strip().lower()
        if cat not in cat_to_idx:
            continue
        lab = str(r.get("label") or "").strip().lower()
        if lab not in counts[cat]:
            continue
        counts[cat][lab] += 1
        cat_totals[cat] += 1
    row_labels = [c for c in CAT_ORDER if cat_totals[c] > 0]
    P = np.zeros((len(row_labels), 3), dtype=float)
    for i, cat in enumerate(row_labels):
        tot = cat_totals[cat]
        if tot <= 0:
            continue
        for j, lab in enumerate(col_labels):
            P[i, j] = counts[cat][lab] / tot
    return P, row_labels, col_labels, "label_fallback"


def js_distance_matrix(P: np.ndarray) -> np.ndarray:
    """Symmetric JS distance (n_cat x n_cat)."""
    n = P.shape[0]
    D = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            d = float(jensenshannon(P[i], P[j], base=2.0))
            D[i, j] = D[j, i] = d
    return D


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, nargs="+", required=True)
    ap.add_argument("--out-png", type=Path, default=ROOT / "figures" / "failure_mode_category_heatmap.png")
    ap.add_argument("--out-json", type=Path, default=None)
    args = ap.parse_args()

    all_rows: list[dict[str, Any]] = []
    for pth in args.results:
        if not pth.is_file():
            print(f"Missing {pth}", file=sys.stderr)
            sys.exit(1)
        all_rows.extend(load_rows(pth))

    P, row_labels, col_labels, mode = build_fm_matrix(all_rows)
    if P.shape[0] < 2:
        print("Need at least 2 categories with labeled rows.", file=sys.stderr)
        sys.exit(1)

    D = js_distance_matrix(P)
    condensed = squareform(D, checks=False)
    Z = linkage(condensed, method="average")
    order = leaves_list(Z)
    P_ord = P[order]
    row_labels_ord = [row_labels[i] for i in order]

    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": FG,
            "text.color": FG,
            "xtick.color": FG,
            "ytick.color": FG,
        }
    )

    fig = plt.figure(figsize=(10, 6))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.22, 0.78], wspace=0.08)
    ax_den = fig.add_subplot(gs[0, 0])
    ax_map = fig.add_subplot(gs[0, 1])

    dendrogram(Z, ax=ax_den, orientation="left", labels=[row_labels[i] for i in order], color_threshold=0)
    ax_den.set_facecolor(BG)
    ax_den.tick_params(colors=FG, labelsize=8)
    for s in ax_den.spines.values():
        s.set_color(MUTED)

    im = ax_map.imshow(P_ord, aspect="auto", cmap="viridis", norm=Normalize(0, max(P_ord.max(), 0.01)))
    ax_map.set_xticks(np.arange(len(col_labels)))
    ax_map.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=8)
    ax_map.set_yticks(np.arange(len(row_labels_ord)))
    ax_map.set_yticklabels(row_labels_ord, fontsize=9)
    ax_map.set_xlabel("Profile column (failure_mode or label)", color=FG)
    ax_map.set_title(f"Category profile heatmap — {mode}", color=FG, fontsize=11)
    cbar = fig.colorbar(im, ax=ax_map, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors=FG)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.92, bottom=0.18, wspace=0.25)
    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out_png, dpi=160, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out_png} (mode={mode})", file=sys.stderr)

    if args.out_json:
        payload = {
            "schema_version": 1,
            "profile_mode": mode,
            "row_order_leaves": row_labels_ord,
            "column_labels": col_labels,
            "matrix": P_ord.tolist(),
            "linkage": Z.tolist(),
        }
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
