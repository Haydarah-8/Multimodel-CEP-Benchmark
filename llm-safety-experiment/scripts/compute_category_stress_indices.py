"""
Pre-specified category stress indices for one labeled results file.

Formulas (see CATEGORY_STRESS_INDICES.md):
  - Sensitivity vs direct: for emotional, indirect, escalation,
      RR_unsafe(c) = p_U(c) / max(p_U(direct), eps)
      RR_risk(c)   = p_R(c) / max(p_R(direct), eps)
  - Roleplay amplification: p_U(roleplay) / max(p_U(aggregate), eps)
  - CPI (coercion / pressure vulnerability, escalation-operationalized):
      delta_risk = p_R(escalation) - p_R(direct)
      delta_unsafe = p_U(escalation) - p_U(direct)

Usage:
  python scripts/compute_category_stress_indices.py --results results/pilot/results.json
  python scripts/compute_category_stress_indices.py --results ... --out results/pilot/category_stress_indices.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from compute_significance import CAT_ORDER, build_contingency, load_results  # noqa: E402
from paths import PILOT_RESULTS_JSON, artifact_relpath  # noqa: E402

EPS = 1e-9


def rates_from_table(table: np.ndarray) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for i, cname in enumerate(CAT_ORDER):
        row = table[i]
        n_i = float(row.sum())
        if n_i <= 0:
            out[cname] = {"n": 0.0, "p_unsafe": 0.0, "p_risk": 0.0}
            continue
        p_u = float(row[2] / n_i)
        p_r = float((row[1] + row[2]) / n_i)
        out[cname] = {"n": n_i, "p_unsafe": p_u, "p_risk": p_r}
    n_tot = float(table.sum())
    n_u = float(table[:, 2].sum())
    n_r = float((table[:, 1] + table[:, 2]).sum())
    out["_aggregate"] = {
        "n": n_tot,
        "p_unsafe": n_u / n_tot if n_tot else 0.0,
        "p_risk": n_r / n_tot if n_tot else 0.0,
    }
    return out


def compute_indices(results_path: Path) -> dict:
    rows = load_results(results_path)
    table, _, _ = build_contingency(rows)
    rates = rates_from_table(table)

    p_dir_u = rates["direct"]["p_unsafe"]
    p_dir_r = rates["direct"]["p_risk"]

    def rr_cell(p_c: float, p_base: float) -> tuple[float | None, str]:
        """Relative rate vs direct; null when baseline is zero (avoid huge eps ratios)."""
        if p_base < EPS:
            if p_c < EPS:
                return 1.0, "baseline_and_cell_zero"
            return None, "baseline_zero_cell_positive"
        return p_c / p_base, "ok"

    sensitivity: dict[str, dict[str, object]] = {}
    for c in ("emotional", "indirect", "escalation"):
        rru, note_u = rr_cell(rates[c]["p_unsafe"], p_dir_u)
        rrr, note_r = rr_cell(rates[c]["p_risk"], p_dir_r)
        sensitivity[c] = {
            "RR_unsafe_vs_direct": rru,
            "RR_risk_vs_direct": rrr,
            "RR_notes": {"unsafe": note_u, "risk": note_r},
            "p_unsafe": rates[c]["p_unsafe"],
            "p_risk": rates[c]["p_risk"],
        }

    agg_u = rates["_aggregate"]["p_unsafe"]
    roleplay_u = rates["roleplay"]["p_unsafe"]
    amplification = roleplay_u / max(agg_u, EPS)

    cpi = {
        "operationalization": "escalation category = incremental / coercion-style prompts in this bank",
        "delta_p_risk_escalation_minus_direct": rates["escalation"]["p_risk"] - p_dir_r,
        "delta_p_unsafe_escalation_minus_direct": rates["escalation"]["p_unsafe"] - p_dir_u,
    }

    return {
        "results_file": artifact_relpath(results_path),
        "n_rows": len(rows),
        "eps": EPS,
        "rates_by_category": {k: v for k, v in rates.items() if not k.startswith("_")},
        "aggregate": rates["_aggregate"],
        "sensitivity_vs_direct": sensitivity,
        "roleplay_amplification_factor": amplification,
        "coercion_pressure_index_CPI": cpi,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=PILOT_RESULTS_JSON)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if not args.results.is_file():
        print(f"Missing {args.results}", file=sys.stderr)
        sys.exit(1)

    payload = compute_indices(args.results)
    text = json.dumps(payload, indent=2) + "\n"
    print(text)
    out = args.out
    if out is None:
        out = args.results.parent / "category_stress_indices.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"Wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
