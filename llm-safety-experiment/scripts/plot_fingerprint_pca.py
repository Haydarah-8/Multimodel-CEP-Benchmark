"""
2D PCA embedding of model fingerprints (interpretability).

Feature recipe (v1): per category — refusal, compliance_unsafe, risk (15) +
ASS.value (0 if null), ESI risk gap, ESI unsafe gap (3) = 18 dims.

See INTERPRETABILITY_VIZ.md.

Usage:
  python scripts/plot_fingerprint_pca.py --root results/multimodel
  python scripts/plot_fingerprint_pca.py --root results/multimodel --out figures/multimodel/fingerprint_pca.png --meta-out figures/multimodel/fingerprint_pca_meta.json
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

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from compute_significance import CAT_ORDER  # noqa: E402
from paths import artifact_relpath  # noqa: E402

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"

FEATURE_VERSION = 1


def discover_fingerprints(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("model_fingerprint.json"))


def fingerprint_feature_vector(data: dict[str, Any]) -> np.ndarray | None:
    curves = data.get("curves") or {}
    cats = curves.get("categories") or []
    refusal = curves.get("refusal") or []
    comp = curves.get("compliance_unsafe") or []
    risk = curves.get("risk") or []
    if list(cats) != list(CAT_ORDER) or len(refusal) != len(CAT_ORDER):
        return None
    if len(comp) != len(CAT_ORDER) or len(risk) != len(CAT_ORDER):
        return None
    block15: list[float] = []
    for i in range(len(CAT_ORDER)):
        block15.extend([float(refusal[i]), float(comp[i]), float(risk[i])])
    ass = data.get("ASS") or {}
    ass_v = ass.get("value")
    ass_f = float(ass_v) if ass_v is not None and np.isfinite(ass_v) else 0.0
    esi = data.get("ESI") or {}
    esi_r = float(esi.get("ESI_risk_escalation_minus_direct", 0.0))
    esi_u = float(esi.get("ESI_unsafe_escalation_minus_direct", 0.0))
    vec = np.array(block15 + [ass_f, esi_r, esi_u], dtype=float)
    return vec


def pca_two_components(Z: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Z: n x p standardized. Returns scores (n x 2), Vt (2 x p or 1 x p padded), explained_ratio (length 2)."""
    n, p = Z.shape
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    total_var = float(np.sum(S**2)) if len(S) else 0.0
    k = min(2, len(S))
    scores_k = U[:, :k] * S[:k]
    if scores_k.shape[1] < 2:
        scores = np.column_stack([scores_k, np.zeros(n)])
    else:
        scores = scores_k[:, :2]
    Vt_out = Vt[:k, :]
    if Vt_out.shape[0] < 2:
        Vt_out = np.vstack([Vt_out, np.zeros((1, p))])
    expl: list[float] = []
    for i in range(2):
        if i < len(S) and total_var > 0:
            expl.append(float(S[i] ** 2 / total_var))
        else:
            expl.append(0.0)
    return scores[:, :2], Vt_out[:2, :], expl


def short_label(model: str, provider: str, max_len: int = 28) -> str:
    s = model or provider or "?"
    return (s[: max_len - 2] + "…") if len(s) > max_len else s


def main() -> None:
    ap = argparse.ArgumentParser(description="PCA scatter of model fingerprint feature vectors")
    ap.add_argument("--root", type=Path, default=ROOT / "results" / "multimodel")
    ap.add_argument("--out", type=Path, default=ROOT / "figures" / "multimodel" / "fingerprint_pca.png")
    ap.add_argument("--meta-out", type=Path, default=None, help="JSON with explained variance and loadings")
    ap.add_argument("--max-models", type=int, default=0, help="0 = no limit")
    ap.add_argument("--annotate", action="store_true", help="Draw short model labels")
    args = ap.parse_args()

    paths = discover_fingerprints(args.root)
    if args.max_models and len(paths) > args.max_models:
        paths = paths[: args.max_models]

    rows: list[dict[str, Any]] = []
    X_list: list[np.ndarray] = []
    for fp in paths:
        data = json.loads(fp.read_text(encoding="utf-8"))
        vec = fingerprint_feature_vector(data)
        if vec is None:
            continue
        prov = str(data.get("provider") or "")
        model = str(data.get("model") or "")
        X_list.append(vec)
        rows.append(
            {
                "path": artifact_relpath(fp),
                "provider": prov,
                "model": model,
                "label": short_label(model, prov),
            }
        )

    if len(X_list) < 3:
        print(
            f"Need at least 3 valid fingerprint JSONs; found {len(X_list)} under {args.root}. "
            "Run: python scripts/fingerprint_all_multimodel.py",
            file=sys.stderr,
        )
        sys.exit(1)

    X = np.stack(X_list, axis=0)
    col_mean = X.mean(axis=0)
    col_std = X.std(axis=0, ddof=0)
    col_std = np.where(col_std < 1e-12, 1.0, col_std)
    Z = (X - col_mean) / col_std

    if np.linalg.matrix_rank(Z) < 2:
        print("Feature matrix is (near) rank-deficient; cannot form a 2D PCA.", file=sys.stderr)
        sys.exit(1)

    scores, Vt, explained_ratio = pca_two_components(Z)
    feature_names = (
        [f"{c}_{s}" for c in CAT_ORDER for s in ("refusal", "unsafe", "risk")]
        + ["ASS_value_imputed", "ESI_risk_gap", "ESI_unsafe_gap"]
    )

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

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(BG)
    provs = [r["provider"] or "unknown" for r in rows]
    uniq = sorted(set(provs))
    n_u = max(len(uniq), 1)
    try:
        cmap = mpl.colormaps["tab10"].resampled(n_u)
    except (AttributeError, KeyError, TypeError):
        cmap = mpl.cm.get_cmap("tab10", n_u)
    prov_to_i = {p: i for i, p in enumerate(uniq)}

    def _color_for_index(i: int) -> tuple:
        t = i / max(n_u - 1, 1) if n_u > 1 else 0.0
        return cmap(t)

    colors = [_color_for_index(prov_to_i[p]) for p in provs]

    ax.scatter(scores[:, 0], scores[:, 1], c=colors, s=80, edgecolors=FG, linewidths=0.5, alpha=0.9)
    if args.annotate:
        for i, r in enumerate(rows):
            ax.annotate(
                r["label"],
                (scores[i, 0], scores[i, 1]),
                fontsize=7,
                color=FG,
                alpha=0.85,
                xytext=(4, 4),
                textcoords="offset points",
            )
    ax.set_xlabel(f"PC1 ({100 * explained_ratio[0]:.1f}% var.)", color=FG)
    ax.set_ylabel(f"PC2 ({100 * explained_ratio[1]:.1f}% var.)", color=FG)
    ax.set_title("Model fingerprints — PCA embedding", color=FG, fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.4)
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=_color_for_index(i),
            markersize=8,
            label=u,
        )
        for i, u in enumerate(uniq)
    ]
    ax.legend(handles=handles, loc="best", framealpha=0.2, fontsize=8)
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out}", file=sys.stderr)

    if args.meta_out:
        meta = {
            "schema_version": 1,
            "feature_version": FEATURE_VERSION,
            "n_models": len(rows),
            "explained_variance_ratio": explained_ratio,
            "feature_names": feature_names,
            "pc_loadings_rows_are_pcs": [[float(v) for v in Vt[i]] for i in range(Vt.shape[0])],
            "models": rows,
        }
        args.meta_out.parent.mkdir(parents=True, exist_ok=True)
        args.meta_out.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.meta_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
