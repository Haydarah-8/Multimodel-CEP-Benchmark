"""
Hypothesis tests for category × label association (results.json).

- Pearson chi-square independence on 5×3 contingency table
- Fisher exact (two-sided) on 2×2: UNSAFE vs not, focal category vs rest

Run from llm-safety-experiment:
  python scripts/compute_significance.py
  python scripts/compute_significance.py --results results_openai_gpt-4o-mini.json

Writes significance_stats.json (or --out). Uses column \"label\" on each row.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import chi2_contingency, fisher_exact

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import PILOT_RESULTS_JSON  # noqa: E402

DEFAULT_RESULTS = PILOT_RESULTS_JSON


def default_significance_out(results_path: Path) -> Path:
    """Place stats next to results; pilot results.json -> significance_stats.json in same folder."""
    if results_path.name == "results.json":
        return results_path.parent / "significance_stats.json"
    return results_path.parent / f"significance_stats_{results_path.stem}.json"

CAT_ORDER = ["direct", "indirect", "emotional", "escalation", "roleplay"]
LABEL_ORDER = ["safe", "partial", "unsafe"]


def load_results(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("results.json must contain a JSON array")
    return data


def build_contingency(rows: list[dict[str, Any]]) -> tuple[np.ndarray, list[str], list[str]]:
    """5×3 table: rows = category, cols = safe, partial, unsafe."""
    counts: dict[tuple[str, str], int] = {}
    for r in rows:
        cat = str(r.get("category", "")).lower()
        lab = str(r.get("label", "")).lower()
        if cat not in CAT_ORDER or lab not in LABEL_ORDER:
            continue
        counts[(cat, lab)] = counts.get((cat, lab), 0) + 1

    table = np.zeros((len(CAT_ORDER), len(LABEL_ORDER)), dtype=int)
    for i, c in enumerate(CAT_ORDER):
        for j, l in enumerate(LABEL_ORDER):
            table[i, j] = counts.get((c, l), 0)
    return table, CAT_ORDER, LABEL_ORDER


def fisher_unsafe_vs_rest(
    table: np.ndarray, focal_idx: int
) -> tuple[float, float, np.ndarray]:
    """
    Focal category vs all others: UNSAFE vs (SAFE + PARTIAL).
    Returns (odds_ratio, p_value, table_2x2).
    """
    unsafe_col = 2
    not_unsafe = slice(0, 2)
    a = int(table[focal_idx, unsafe_col])
    b = int(table[focal_idx, not_unsafe].sum())  # SAFE + PARTIAL
    rest = np.delete(table, focal_idx, axis=0)
    c = int(rest[:, unsafe_col].sum())
    d = int(rest[:, not_unsafe].sum())
    sub = np.array([[a, b], [c, d]], dtype=int)
    oddsratio, p = fisher_exact(sub, alternative="two-sided")
    return float(oddsratio), float(p), sub


def main() -> None:
    parser = argparse.ArgumentParser(description="Chi-square + Fisher tests on labeled results.")
    parser.add_argument(
        "--results",
        "-r",
        type=Path,
        default=DEFAULT_RESULTS,
        help=f"Labeled results JSON (default: {DEFAULT_RESULTS.name})",
    )
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        default=None,
        help="Output JSON path (default: significance_stats.json or significance_stats_<stem>.json)",
    )
    args = parser.parse_args()

    results_path = args.results.resolve()
    if not results_path.exists():
        print(f"Missing {results_path}", file=sys.stderr)
        sys.exit(1)

    out_path = args.out.resolve() if args.out is not None else default_significance_out(results_path)

    rows = load_results(results_path)
    table, cats, labels = build_contingency(rows)

    chi2, p_chi, dof, expected = chi2_contingency(table)

    rp_idx = cats.index("roleplay")
    esc_idx = cats.index("escalation")
    or_rp, p_rp, tab_rp = fisher_unsafe_vs_rest(table, rp_idx)
    or_esc, p_esc, tab_esc = fisher_unsafe_vs_rest(table, esc_idx)

    n_total = int(table.sum())
    n_unsafe = int(table[:, 2].sum())
    agg_unsafe_rate = n_unsafe / n_total if n_total else 0.0
    rp_unsafe = int(table[rp_idx, 2])
    rp_n = int(table[rp_idx].sum())
    rp_rate = rp_unsafe / rp_n if rp_n else 0.0
    rel_freq = rp_rate / agg_unsafe_rate if agg_unsafe_rate > 0 else float("nan")

    summary = {
        "results_file": str(results_path),
        "n_rows": len(rows),
        "contingency_5x3": {
            "categories": cats,
            "labels": labels,
            "counts": table.tolist(),
        },
        "chi2_independence": {
            "statistic": float(chi2),
            "df": int(dof),
            "p_value": float(p_chi),
            "expected": expected.tolist(),
        },
        "fisher_roleplay_vs_rest_unsafe": {
            "odds_ratio": or_rp,
            "p_value_two_sided": p_rp,
            "table_2x2": tab_rp.tolist(),
            "labels_rows": ["roleplay", "rest"],
            "labels_cols": ["UNSAFE", "not_UNSAFE"],
        },
        "fisher_escalation_vs_rest_unsafe": {
            "odds_ratio": or_esc,
            "p_value_two_sided": p_esc,
            "table_2x2": tab_esc.tolist(),
            "labels_rows": ["escalation", "rest"],
            "labels_cols": ["UNSAFE", "not_UNSAFE"],
        },
        "roleplay_vs_aggregate_baseline": {
            "roleplay_unsafe_rate": rp_rate,
            "aggregate_unsafe_rate": agg_unsafe_rate,
            "relative_frequency_times": float(rel_freq),
        },
    }

    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Results: {results_path}")
    print("Contingency (rows=categories, cols=safe,partial,unsafe):")
    print(table)
    print()
    print(f"Pearson chi-square independence: chi2={chi2:.4f}, df={dof}, p={p_chi:.6g}")
    print("(Small expected counts in some cells; interpret p as supporting evidence.)")
    print()
    print("Fisher exact (two-sided), UNSAFE vs not — roleplay vs rest:")
    print(tab_rp)
    print(f"  OR={or_rp:.4f}, p={p_rp:.6g}")
    print()
    print("Fisher exact (two-sided), UNSAFE vs not — escalation vs rest:")
    print(tab_esc)
    print(f"  OR={or_esc:.4f}, p={p_esc:.6g}")
    print()
    print(
        f"Roleplay UNSAFE rate {rp_rate:.1%} vs aggregate {agg_unsafe_rate:.1%} "
        f"(~{rel_freq:.2f}× relative frequency)."
    )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
