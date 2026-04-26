"""
Risk vs refusal scatter from model fingerprints (weighted by per-category n).

Optional convex hull (descriptive, not a Pareto claim) and optional frontier polyline.

See INTERPRETABILITY_VIZ.md.

Usage:
  python scripts/plot_safety_frontier.py --root results/multimodel
  python scripts/plot_safety_frontier.py --root results/multimodel --color-by tier --line --out figures/multimodel/safety_frontier.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from causal_proxy_data import tier_from_path  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
LINE_COLOR = "#58a6ff"


def discover_fingerprints(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("model_fingerprint.json"))


def aggregates_from_fingerprint(data: dict[str, Any]) -> tuple[float, float] | None:
    curves = data.get("curves") or {}
    n_list = curves.get("n") or []
    refusal = curves.get("refusal") or []
    risk = curves.get("risk") or []
    if not n_list or len(refusal) != len(n_list) or len(risk) != len(n_list):
        return None
    num = float(sum(int(x) for x in n_list))
    if num <= 0:
        return None
    r_agg = sum(int(n) * float(r) for n, r in zip(n_list, refusal)) / num
    k_agg = sum(int(n) * float(r) for n, r in zip(n_list, risk)) / num
    return r_agg, k_agg


def short_label(model: str, max_len: int = 22) -> str:
    s = model or "?"
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT / "results" / "multimodel")
    ap.add_argument("--out", type=Path, default=ROOT / "figures" / "multimodel" / "safety_frontier.png")
    ap.add_argument("--color-by", choices=("provider", "tier"), default="provider")
    ap.add_argument("--hull", action="store_true", help="Draw convex hull when >= 3 points")
    ap.add_argument("--line", action="store_true", help="Connect points sorted by refusal (desc)")
    ap.add_argument("--max-models", type=int, default=0)
    args = ap.parse_args()

    paths = discover_fingerprints(args.root)
    if args.max_models and len(paths) > args.max_models:
        paths = paths[: args.max_models]

    points: list[tuple[float, float, str, str, str, str]] = []
    for fp in paths:
        data = json.loads(fp.read_text(encoding="utf-8"))
        agg = aggregates_from_fingerprint(data)
        if agg is None:
            continue
        r_agg, k_agg = agg
        prov = str(data.get("provider") or "unknown")
        model = str(data.get("model") or "")
        tier = tier_from_path(fp) or "unsorted"
        points.append((r_agg, k_agg, prov, model, tier, str(fp)))

    if len(points) < 2:
        print(
            f"Need at least 2 fingerprint JSONs with curves; found {len(points)} under {args.root}.",
            file=sys.stderr,
        )
        sys.exit(1)

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

    xs = np.array([p[0] for p in points])
    ys = np.array([p[1] for p in points])
    color_key = [p[4] if args.color_by == "tier" else p[2] for p in points]
    uniq = sorted(set(color_key))
    n_u = max(len(uniq), 1)
    try:
        cmap = mpl.colormaps["tab10"].resampled(n_u)
    except (AttributeError, KeyError, TypeError):
        cmap = mpl.cm.get_cmap("tab10", n_u)
    idx_map = {u: i for i, u in enumerate(uniq)}

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(BG)
    for i, p in enumerate(points):
        u = color_key[i]
        t = idx_map[u] / max(len(uniq) - 1, 1) if len(uniq) > 1 else 0.0
        try:
            c = cmap(t)
        except Exception:
            c = cmap(i % 10)
        ax.scatter(p[0], p[1], c=[c], s=85, edgecolors=FG, linewidths=0.5, zorder=3)
        ax.annotate(
            short_label(p[3]),
            (p[0], p[1]),
            fontsize=7,
            color=FG,
            alpha=0.9,
            xytext=(4, 4),
            textcoords="offset points",
            zorder=4,
        )

    if args.line and len(points) >= 2:
        order = sorted(range(len(points)), key=lambda i: points[i][0], reverse=True)
        lx = [points[i][0] for i in order]
        ly = [points[i][1] for i in order]
        ax.plot(lx, ly, color=LINE_COLOR, linewidth=1.2, alpha=0.65, linestyle="--", zorder=2, label="Sorted tour (desc refusal)")

    if args.hull and len(points) >= 3:
        pts2 = np.column_stack([xs, ys])
        try:
            hull = ConvexHull(pts2, qhull_options="QJ")
        except Exception:
            hull = None
        if hull is not None:
            for simplex in hull.simplices:
                ax.plot(
                    pts2[simplex, 0],
                    pts2[simplex, 1],
                    color=MUTED,
                    linewidth=1.0,
                    alpha=0.7,
                    zorder=1,
                )

    handles = []
    for i, u in enumerate(uniq):
        t = i / max(len(uniq) - 1, 1) if len(uniq) > 1 else 0.0
        try:
            c = cmap(t)
        except Exception:
            c = cmap(i % 10)
        handles.append(Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=8, label=u))
    ax.legend(handles=handles, title=args.color_by, loc="best", framealpha=0.2, fontsize=8)

    ax.set_xlabel(r"Weighted $\hat P(\mathrm{safe})$ (refusal proxy)", color=FG)
    ax.set_ylabel(r"Weighted $\hat R=\hat P(\mathrm{partial}\cup\mathrm{unsafe})$ (risk)", color=FG)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_title("Safety frontier sketch — risk vs refusal (per model)", color=FG, fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.text(
        0.5,
        0.01,
        "Descriptive geometry only — not a Pareto or causal frontier.",
        ha="center",
        fontsize=8,
        color=MUTED,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out} ({len(points)} models)", file=sys.stderr)


if __name__ == "__main__":
    main()
