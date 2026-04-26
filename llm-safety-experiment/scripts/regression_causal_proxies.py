"""
Lightweight associational regressions (LPM) as causal proxies — not causal identification.

Modes:
  pressure-unsafe   y_unsafe ~ pressure_composite + category dummies
  refusal           y_safe ~ category dummies
  tier              y_unsafe ~ category + tier + interactions; per-tier category-index slopes

See CAUSAL_PROXIES.md. Cluster bootstrap by canonical prompt id (pressure_join_id).

Usage (from llm-safety-experiment):
  python scripts/regression_causal_proxies.py all --root results/multimodel --pressure-json results/prompt_pressure_scores.json
  python scripts/regression_causal_proxies.py pressure-unsafe --root results/multimodel/cheap ...
"""

from __future__ import annotations

import argparse
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

from causal_proxy_data import (  # noqa: E402
    TIER_ORDER,
    discover_result_files,
    load_pressure_scores,
    matrix_pressure_unsafe,
    matrix_refusal,
    matrix_tier_interaction,
    matrix_tier_slope,
    ols_fit,
    pooled_labeled_rows,
)
from paths import MULTIMODEL_DIR, PROMPTS_FILE, artifact_relpath  # noqa: E402

SCHEMA_VERSION = 1


def cluster_bootstrap_ols(
    X: np.ndarray,
    y: np.ndarray,
    cluster_keys: list[Any],
    n_boot: int,
    seed: int,
) -> tuple[np.ndarray, dict[str, list[float]] | None]:
    """Resample clusters with replacement; percentile 95% CI for coefficients."""
    n, k = X.shape
    if n < k or n < 2:
        raise ValueError("Insufficient rows for OLS")
    unique = list(dict.fromkeys(cluster_keys))
    if len(unique) < 2:
        beta = ols_fit(X, y)
        return beta, None
    key_to_rows: dict[Any, list[int]] = {}
    for i, key in enumerate(cluster_keys):
        key_to_rows.setdefault(key, []).append(i)
    rng = np.random.default_rng(seed)
    betas: list[np.ndarray] = []
    n_c = len(unique)
    for _ in range(n_boot):
        picked = rng.choice(n_c, size=n_c, replace=True)
        idxs: list[int] = []
        for j in picked:
            idxs.extend(key_to_rows[unique[j]])
        if len(idxs) < k:
            continue
        Xb = X[idxs]
        yb = y[idxs]
        try:
            betas.append(ols_fit(Xb, yb))
        except ValueError:
            continue
    beta_hat = ols_fit(X, y)
    if len(betas) < 10:
        return beta_hat, None
    B = np.stack(betas, axis=0)
    lo = np.percentile(B, 2.5, axis=0).tolist()
    hi = np.percentile(B, 97.5, axis=0).tolist()
    return beta_hat, {"low": lo, "high": hi}


def coef_table(colnames: list[str], beta: np.ndarray, ci: dict[str, list[float]] | None) -> list[dict[str, Any]]:
    out = []
    for j, name in enumerate(colnames):
        row: dict[str, Any] = {"name": name, "coef": float(beta[j])}
        if ci is not None and j < len(ci["low"]):
            row["ci95_low"] = ci["low"][j]
            row["ci95_high"] = ci["high"][j]
        out.append(row)
    return out


def try_logit_summary(X: np.ndarray, y: np.ndarray, colnames: list[str]) -> dict[str, Any] | None:
    try:
        import statsmodels.api as sm  # type: ignore[import-untyped]
    except ImportError:
        return None
    if X.shape[0] < X.shape[1] + 5:
        return {"note": "too_few_rows_for_logit", "import_ok": True}
    try:
        model = sm.Logit(y.astype(float), X.astype(float))
        res = model.fit(disp=False, maxiter=100)
    except Exception as e:  # noqa: BLE001
        return {"note": f"logit_failed: {e!s}", "import_ok": True}
    out: dict[str, Any] = {
        "import_ok": True,
        "log_likelihood": float(res.llf),
        "aic": float(res.aic),
        "params": {colnames[i]: float(res.params[i]) for i in range(len(colnames))},
        "pvalues": {colnames[i]: float(res.pvalues[i]) for i in range(len(colnames))},
    }
    return out


def load_pool(
    root: Path,
    pressure_path: Path,
    include_archive: bool,
    require_pressure: bool,
) -> tuple[list[dict[str, Any]], dict[Any, dict[str, Any]]]:
    by_p: dict[Any, dict[str, Any]] = {}
    if pressure_path.is_file():
        by_p = load_pressure_scores(pressure_path)
    elif require_pressure:
        raise FileNotFoundError(pressure_path)
    files = discover_result_files(root, include_archive)
    rows = pooled_labeled_rows(files, by_p, require_pressure=require_pressure)
    return rows, by_p


def cmd_pressure_unsafe(args: argparse.Namespace) -> dict[str, Any]:
    try:
        rows, _ = load_pool(args.root, args.pressure_json, args.include_archive, require_pressure=True)
    except FileNotFoundError as e:
        return {"error": "missing_pressure_json", "path": str(e)}
    X, y, colnames, clusters = matrix_pressure_unsafe(rows)
    if X.shape[0] < X.shape[1]:
        return {"error": "not_enough_rows", "n_rows": int(X.shape[0])}
    beta, ci = cluster_bootstrap_ols(X, y, clusters, args.bootstrap, args.seed)
    block: dict[str, Any] = {
        "n_rows": int(X.shape[0]),
        "n_clusters": len(set(clusters)),
        "model": "LPM unsafe ~ 1 + pressure_composite + category dummies (direct ref)",
        "coefficients": coef_table(colnames, beta, ci),
    }
    if getattr(args, "logistic", False):
        block["logit_optional"] = try_logit_summary(X, y, colnames)
        if block["logit_optional"] is None:
            block["logit_optional"] = {"import_ok": False, "note": "pip install statsmodels for Logit"}
    return block


def cmd_refusal(args: argparse.Namespace) -> dict[str, Any]:
    rows, _ = load_pool(args.root, args.pressure_json, args.include_archive, require_pressure=False)
    X, y, colnames, clusters = matrix_refusal(rows)
    if X.shape[0] < X.shape[1]:
        return {"error": "not_enough_rows", "n_rows": int(X.shape[0])}
    beta, ci = cluster_bootstrap_ols(X, y, clusters, args.bootstrap, args.seed)
    return {
        "n_rows": int(X.shape[0]),
        "n_clusters": len(set(clusters)),
        "model": "LPM safe ~ 1 + category dummies (direct ref); proxy for refusal shift vs direct",
        "coefficients": coef_table(colnames, beta, ci),
    }


def cmd_tier(args: argparse.Namespace) -> dict[str, Any]:
    rows, _ = load_pool(args.root, args.pressure_json, args.include_archive, require_pressure=False)
    tiered = [r for r in rows if r.get("tier") in TIER_ORDER]
    has_mid = any(r.get("tier") == "mid" for r in tiered)
    has_exp = any(r.get("tier") == "expensive" for r in tiered)
    block: dict[str, Any] = {
        "n_rows_tiered": len(tiered),
        "per_tier_slope_unsafe_on_category_index": matrix_tier_slope(tiered),
    }
    if not has_mid and not has_exp:
        block["tier_interaction"] = {
            "note": "Only one tier present under --root; interaction model needs cheap+mid and/or expensive.",
        }
        return block
    inter = matrix_tier_interaction(tiered)
    if inter is None:
        block["tier_interaction"] = {"error": "not_enough_tiered_rows"}
        return block
    X, y, colnames, clusters = inter
    if X.shape[0] < X.shape[1]:
        block["tier_interaction"] = {"error": "rank_deficient", "n_rows": int(X.shape[0])}
        return block
    beta, ci = cluster_bootstrap_ols(X, y, clusters, args.bootstrap, args.seed)
    block["tier_interaction"] = {
        "n_rows": int(X.shape[0]),
        "n_clusters": len(set(clusters)),
        "model": "LPM unsafe ~ cats + tier_mid/exp + cat×tier (direct ref cat, cheap ref tier)",
        "coefficients": coef_table(colnames, beta, ci),
    }
    return block


def cmd_all(args: argparse.Namespace) -> dict[str, Any]:
    if not args.pressure_json.is_file():
        return {"error": f"missing_pressure_json: {args.pressure_json}"}
    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "prompts_reference": artifact_relpath(PROMPTS_FILE),
        "pressure_file": artifact_relpath(args.pressure_json),
        "root": artifact_relpath(args.root),
        "bootstrap_reps": args.bootstrap,
        "cluster_key": "pressure_join_id (canonical prompt id)",
        "disclaimer": "Associational / hypothetical proxies only — not causal identification.",
        "pressure_unsafe": cmd_pressure_unsafe(args),
        "refusal": cmd_refusal(args),
        "tier": cmd_tier(args),
    }
    return out


def add_common(ap: argparse.ArgumentParser) -> None:
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--pressure-json",
        type=Path,
        default=ROOT / "results" / "prompt_pressure_scores.json",
    )
    ap.add_argument("--include-archive", action="store_true")
    ap.add_argument("--bootstrap", type=int, default=1000, help="Cluster bootstrap replications")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "causal_proxy_regressions.json",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="LPM causal proxies (cluster bootstrap)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c_all = sub.add_parser("all", help="Run pressure-unsafe, refusal, and tier blocks")
    add_common(c_all)
    c_all.set_defaults(func=cmd_all)

    c_p = sub.add_parser("pressure-unsafe", help="Unsafe ~ pressure + category")
    add_common(c_p)
    c_p.add_argument("--logistic", action="store_true", help="Try statsmodels Logit if installed")
    c_p.set_defaults(func=lambda a: {**{"mode": "pressure_unsafe"}, **cmd_pressure_unsafe(a)})

    c_r = sub.add_parser("refusal", help="Safe ~ category dummies")
    add_common(c_r)
    c_r.set_defaults(func=lambda a: {**{"mode": "refusal"}, **cmd_refusal(a)})

    c_t = sub.add_parser("tier", help="Tier interactions + per-tier category-index slopes")
    add_common(c_t)
    c_t.set_defaults(func=lambda a: {**{"mode": "tier"}, **cmd_tier(a)})

    args = ap.parse_args()
    if args.cmd != "all":
        if args.cmd == "pressure-unsafe" and not args.pressure_json.is_file():
            print(f"Missing {args.pressure_json}; run score_prompt_pressure.py first.", file=sys.stderr)
            sys.exit(1)
        payload = args.func(args)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "mode": args.cmd,
            "prompts_reference": artifact_relpath(PROMPTS_FILE),
            "pressure_file": artifact_relpath(args.pressure_json) if args.pressure_json.is_file() else None,
            "root": artifact_relpath(args.root),
            "bootstrap_reps": args.bootstrap,
            "cluster_key": "pressure_join_id",
            "disclaimer": "Associational proxies only — not causal identification.",
            **payload,
        }
    else:
        if not args.pressure_json.is_file():
            print(f"Missing {args.pressure_json}; run score_prompt_pressure.py first.", file=sys.stderr)
            sys.exit(1)
        payload = cmd_all(args)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
