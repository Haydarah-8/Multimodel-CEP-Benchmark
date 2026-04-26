"""
Row-level data for lightweight LPM / regression proxies (see CAUSAL_PROXIES.md).

Joins labeled results to prompt_pressure_scores on canonical prompt id via pressure_join_id.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from compute_significance import CAT_ORDER  # noqa: E402
from paths import artifact_relpath  # noqa: E402

TIER_ORDER = ("cheap", "mid", "expensive")
VALID_LABELS = frozenset({"safe", "partial", "unsafe"})
REF_CATEGORY = "direct"
REF_TIER_IDX = 0  # cheap

PRESSURE_FEATURE = "pressure_composite"


def pressure_join_id(row: dict[str, Any]) -> Any:
    """Canonical prompts.json id for joining prompt_pressure_scores."""
    if row.get("parent_prompt_id") is not None:
        return row["parent_prompt_id"]
    if row.get("parent_id") is not None:
        return row["parent_id"]
    return row.get("id")


def tier_from_path(path: Path) -> str | None:
    """Infer cheap | mid | expensive from .../multimodel/<tier>/..."""
    parts = {p.lower() for p in path.parts}
    for t in TIER_ORDER:
        if t in parts:
            return t
    return None


def tier_to_numeric(tier: str | None) -> float | None:
    if tier is None or tier not in TIER_ORDER:
        return None
    return float(TIER_ORDER.index(tier))


def discover_result_files(root: Path, include_archive: bool) -> list[Path]:
    if not root.is_dir():
        return []
    files = sorted(root.rglob("results_*.json"))
    if not include_archive:
        files = [p for p in files if "archive" not in p.parts]
    return files


def load_pressure_scores(path: Path) -> dict[Any, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scores = data.get("scores") or []
    out: dict[Any, dict[str, Any]] = {}
    for s in scores:
        out[s["id"]] = s
    return out


def load_results_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def category_index(cat: str) -> int | None:
    c = (cat or "").strip().lower()
    if c not in CAT_ORDER:
        return None
    return CAT_ORDER.index(c)


def build_design_category_dummies(category: str) -> np.ndarray:
    """K-1 dummies with direct omitted; order matches CAT_ORDER[1:]."""
    idx = category_index(category)
    if idx is None:
        return np.full(len(CAT_ORDER) - 1, np.nan)
    ref_i = CAT_ORDER.index(REF_CATEGORY)
    d = np.zeros(len(CAT_ORDER) - 1, dtype=float)
    di = 0
    for j, cname in enumerate(CAT_ORDER):
        if cname == REF_CATEGORY:
            continue
        if j == idx:
            d[di] = 1.0
        di += 1
    return d


def pooled_labeled_rows(
    files: list[Path],
    by_pressure_id: dict[Any, dict[str, Any]],
    *,
    require_pressure: bool,
) -> list[dict[str, Any]]:
    rows_out: list[dict[str, Any]] = []
    for fp in files:
        tier = tier_from_path(fp)
        try:
            rows = load_results_rows(fp)
        except (json.JSONDecodeError, ValueError):
            continue
        for r in rows:
            lab = str(r.get("label", "")).strip().lower()
            if lab not in VALID_LABELS:
                continue
            pid = pressure_join_id(r)
            if require_pressure and pid not in by_pressure_id:
                continue
            cat = str(r.get("category") or "").strip().lower()
            if category_index(cat) is None:
                continue
            feat = by_pressure_id.get(pid) if pid in by_pressure_id else None
            pc = float(feat[PRESSURE_FEATURE]) if feat and PRESSURE_FEATURE in feat else None
            if require_pressure and pc is None:
                continue
            rows_out.append(
                {
                    "file": artifact_relpath(fp),
                    "tier": tier,
                    "tier_num": tier_to_numeric(tier),
                    "pressure_join_id": pid,
                    "category": cat,
                    "category_idx": category_index(cat),
                    "label": lab,
                    "y_unsafe": 1.0 if lab == "unsafe" else 0.0,
                    "y_safe": 1.0 if lab == "safe" else 0.0,
                    "y_risk": 1.0 if lab in ("partial", "unsafe") else 0.0,
                    "pressure_composite": pc,
                    "provider": str(r.get("provider") or ""),
                    "model": str(r.get("model") or ""),
                }
            )
    return rows_out


def matrix_pressure_unsafe(
    rows: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, list[str], list[Any]]:
    """X: intercept + pressure_composite + category dummies (direct ref). y: unsafe."""
    colnames = ["intercept", PRESSURE_FEATURE] + [f"cat__{c}" for c in CAT_ORDER if c != REF_CATEGORY]
    X_list: list[list[float]] = []
    y_list: list[float] = []
    clusters: list[Any] = []
    for r in rows:
        pc = r.get("pressure_composite")
        if pc is None or not np.isfinite(pc):
            continue
        dums = build_design_category_dummies(r["category"])
        if not np.all(np.isfinite(dums)):
            continue
        X_list.append([1.0, float(pc)] + dums.tolist())
        y_list.append(r["y_unsafe"])
        clusters.append(r["pressure_join_id"])
    if not X_list:
        z = np.zeros((0, len(colnames)))
        return z, np.array([]), colnames, []
    return np.array(X_list, dtype=float), np.array(y_list, dtype=float), colnames, clusters


def matrix_refusal(
    rows: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, list[str], list[Any]]:
    """y_safe ~ intercept + category dummies (direct ref). No pressure required."""
    colnames = ["intercept"] + [f"cat__{c}" for c in CAT_ORDER if c != REF_CATEGORY]
    X_list: list[list[float]] = []
    y_list: list[float] = []
    clusters: list[Any] = []
    for r in rows:
        dums = build_design_category_dummies(r["category"])
        if not np.all(np.isfinite(dums)):
            continue
        X_list.append([1.0] + dums.tolist())
        y_list.append(r["y_safe"])
        clusters.append(r["pressure_join_id"])
    if not X_list:
        z = np.zeros((0, len(colnames)))
        return z, np.array([]), colnames, []
    return np.array(X_list, dtype=float), np.array(y_list, dtype=float), colnames, clusters


def matrix_tier_interaction(
    rows: list[dict[str, Any]],
) -> tuple[np.ndarray, np.ndarray, list[str], list[Any]] | None:
    """
    y_unsafe ~ intercept + cat dummies + tier_m + tier_e + cat_j * tier_m + cat_j * tier_e
    Reference: direct category, cheap tier (tier dummies 0 for cheap).
    Rows with missing tier skipped.
    """
    other_cats = [c for c in CAT_ORDER if c != REF_CATEGORY]
    colnames = (
        ["intercept"]
        + [f"cat__{c}" for c in other_cats]
        + ["tier_mid", "tier_expensive"]
        + [f"cat__{c}__x_tier_mid" for c in other_cats]
        + [f"cat__{c}__x_tier_expensive" for c in other_cats]
    )
    X_list: list[list[float]] = []
    y_list: list[float] = []
    clusters: list[Any] = []
    for r in rows:
        tn = r.get("tier_num")
        if tn is None or not np.isfinite(tn):
            continue
        dums = build_design_category_dummies(r["category"])
        if not np.all(np.isfinite(dums)):
            continue
        t_mid = 1.0 if r.get("tier") == "mid" else 0.0
        t_exp = 1.0 if r.get("tier") == "expensive" else 0.0
        inter_mid = (dums * t_mid).tolist()
        inter_exp = (dums * t_exp).tolist()
        row_x = [1.0] + dums.tolist() + [t_mid, t_exp] + inter_mid + inter_exp
        X_list.append(row_x)
        y_list.append(r["y_unsafe"])
        clusters.append(r["pressure_join_id"])
    if not X_list:
        return None
    return np.array(X_list, dtype=float), np.array(y_list, dtype=float), colnames, clusters


def matrix_tier_slope(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Per tier with enough rows: OLS y_unsafe ~ intercept + category_idx (0..4).
    Returns dict tier -> {slope, intercept, n}.
    """
    by_tier: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        t = r.get("tier")
        if t is None:
            continue
        by_tier.setdefault(t, []).append(r)
    out: dict[str, Any] = {}
    for t in TIER_ORDER:
        sub = by_tier.get(t) or []
        if len(sub) < 10:
            out[t] = {"n": len(sub), "slope": None, "intercept": None, "note": "n_lt_10"}
            continue
        xi = np.array([float(r["category_idx"]) for r in sub], dtype=float)
        yi = np.array([r["y_unsafe"] for r in sub], dtype=float)
        X = np.column_stack([np.ones(len(sub)), xi])
        beta, *_ = np.linalg.lstsq(X, yi, rcond=None)
        out[t] = {
            "n": len(sub),
            "intercept": float(beta[0]),
            "slope_category_index": float(beta[1]),
            "note": "OLS unsafe on ordinal category index (descriptive only)",
        }
    return out


def ols_fit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    if X.shape[0] < X.shape[1]:
        raise ValueError("Underdetermined OLS")
    beta, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
    return beta
