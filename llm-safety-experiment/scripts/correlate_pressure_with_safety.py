"""
Correlate heuristic prompt-pressure features with safety outcomes (labeled results).

Joins prompt_pressure_scores.json to each results_*.json on canonical prompt id (pressure_join_id).
Spearman correlation;
pooled across all model rows and per-file. Descriptive only — see PROMPT_PRESSURE_SCORING.md.

Usage:
  python scripts/score_prompt_pressure.py
  python scripts/correlate_pressure_with_safety.py
  python scripts/correlate_pressure_with_safety.py --root results/multimodel/cheap
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from causal_proxy_data import pressure_join_id  # noqa: E402
from paths import MULTIMODEL_DIR, PROMPTS_FILE, artifact_relpath  # noqa: E402

VALID = {"safe", "partial", "unsafe"}
FEATURES = (
    "emotional_intensity",
    "authority_framing",
    "urgency",
    "coercion",
    "pressure_composite",
)


def discover_files(root: Path, include_archive: bool) -> list[Path]:
    if not root.is_dir():
        return []
    files = sorted(root.rglob("results_*.json"))
    if not include_archive:
        files = [p for p in files if "archive" not in p.parts]
    return files


def load_pressure(path: Path) -> dict[Any, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scores = data.get("scores") or []
    out: dict[Any, dict[str, Any]] = {}
    for s in scores:
        out[s["id"]] = s
    return out


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("results must be array")
    return data


def corr_block(
    x: np.ndarray,
    y_unsafe: np.ndarray,
    y_risk: np.ndarray,
) -> dict[str, Any]:
    out_feat: dict[str, Any] = {}
    for name in FEATURES:
        xi = x[:, FEATURES.index(name)]
        mask = np.isfinite(xi) & np.isfinite(y_unsafe.astype(float))
        if mask.sum() < 3:
            out_feat[name] = {"n": int(mask.sum()), "rho_unsafe": None, "p_unsafe": None, "rho_risk": None, "p_risk": None}
            continue
        xv = xi[mask]
        yu = y_unsafe[mask].astype(float)
        yr = y_risk[mask].astype(float)
        if float(np.std(xv)) == 0.0:
            out_feat[name] = {
                "n": int(mask.sum()),
                "rho_unsafe": None,
                "p_unsafe": None,
                "rho_risk": None,
                "p_risk": None,
                "note": "constant_feature",
            }
            continue
        ru = pu = rr = pr = None
        if float(np.std(yu)) > 0.0:
            ru, pu = spearmanr(xv, yu)
        if float(np.std(yr)) > 0.0:
            rr, pr = spearmanr(xv, yr)
        out_feat[name] = {
            "n": int(mask.sum()),
            "rho_unsafe": float(ru) if ru is not None and not math.isnan(ru) else None,
            "p_unsafe": float(pu) if pu is not None and not math.isnan(pu) else None,
            "rho_risk": float(rr) if rr is not None and not math.isnan(rr) else None,
            "p_risk": float(pr) if pr is not None and not math.isnan(pr) else None,
        }
    return out_feat


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pressure-json", type=Path, default=ROOT / "results" / "prompt_pressure_scores.json")
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument("--include-archive", action="store_true")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "pressure_safety_correlation.json")
    args = ap.parse_args()

    if not args.pressure_json.is_file():
        print(f"Run score_prompt_pressure.py first; missing {args.pressure_json}", file=sys.stderr)
        sys.exit(1)

    by_id = load_pressure(args.pressure_json)
    files = discover_files(args.root, args.include_archive)
    if not files:
        print(f"No results_*.json under {args.root}", file=sys.stderr)
        sys.exit(1)

    pooled_x: list[list[float]] = []
    pooled_u: list[int] = []
    pooled_r: list[int] = []

    per_file: list[dict[str, Any]] = []

    for fp in files:
        rows = load_rows(fp)
        xs: list[list[float]] = []
        us: list[int] = []
        rs: list[int] = []
        for r in rows:
            lab = str(r.get("label", "")).strip().lower()
            if lab not in VALID:
                continue
            pid = pressure_join_id(r)
            if pid not in by_id:
                continue
            feat = by_id[pid]
            vec = [float(feat[f]) for f in FEATURES]
            xs.append(vec)
            us.append(1 if lab == "unsafe" else 0)
            rs.append(1 if lab in ("partial", "unsafe") else 0)
            pooled_x.append(vec)
            pooled_u.append(us[-1])
            pooled_r.append(rs[-1])

        if len(xs) < 3:
            continue
        x_arr = np.array(xs, dtype=float)
        yu = np.array(us, dtype=int)
        yr = np.array(rs, dtype=int)
        per_file.append(
            {
                "path": artifact_relpath(fp),
                "n": len(xs),
                "by_feature": corr_block(x_arr, yu, yr),
            }
        )

    if len(pooled_x) < 3:
        print("Not enough joined rows for correlation", file=sys.stderr)
        sys.exit(1)

    X = np.array(pooled_x, dtype=float)
    Yu = np.array(pooled_u, dtype=int)
    Yr = np.array(pooled_r, dtype=int)
    pooled = corr_block(X, Yu, Yr)

    n_tests = len(FEATURES) * 2
    note = (
        f"Descriptive Spearman correlations; {n_tests} tests at feature-by-outcome level (no multiplicity adjustment applied). "
        "For reporting, consider Bonferroni alpha/={} or FDR.".format(n_tests)
    )

    payload = {
        "schema_version": 1,
        "pressure_join": "parent_prompt_id | parent_id | id (see causal_proxy_data.pressure_join_id)",
        "pressure_file": artifact_relpath(args.pressure_json),
        "prompts_reference": artifact_relpath(PROMPTS_FILE),
        "root": artifact_relpath(args.root),
        "n_result_files": len(files),
        "n_rows_pooled": len(pooled_x),
        "pooled_spearman": pooled,
        "per_file": per_file,
        "multiple_testing_note": note,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(note, file=sys.stderr)
    print(f"Wrote {args.out}", file=sys.stderr)

    for f in FEATURES:
        b = pooled[f]
        print(
            f"  {f}: rho_unsafe={b.get('rho_unsafe')} p={b.get('p_unsafe')} | "
            f"rho_risk={b.get('rho_risk')} p={b.get('p_risk')} (n={b.get('n')})",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
