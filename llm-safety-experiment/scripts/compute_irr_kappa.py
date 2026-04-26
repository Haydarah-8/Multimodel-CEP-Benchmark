"""
Cohen's κ on primary label vs label_rater2, overall and stratified by elicitation category.

Requires merged rows where both `label` and `label_rater2` are in {safe, partial, unsafe}.
Rows with null/empty rater2 are skipped (reported in console).

Usage (from llm-safety-experiment):
  python scripts/compute_irr_kappa.py --results results/pilot/results.json
  python scripts/compute_irr_kappa.py --results results/pilot/results.json --by-category
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from irr_utils import cohen_kappa, normalize_label  # noqa: E402
from paths import PILOT_RESULTS_JSON  # noqa: E402


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "rows" in data:
        inner = data["rows"]
        if isinstance(inner, list):
            return inner
    if isinstance(data, list):
        return data
    raise ValueError(f"{path}: expected JSON array or object with 'rows' list")


def main() -> None:
    ap = argparse.ArgumentParser(description="Cohen kappa for label vs label_rater2")
    ap.add_argument("--results", type=Path, default=PILOT_RESULTS_JSON)
    ap.add_argument(
        "--by-category",
        action="store_true",
        help="Print κ per elicitation category (stratified)",
    )
    args = ap.parse_args()

    if not args.results.is_file():
        print(f"Missing {args.results}", file=sys.stderr)
        sys.exit(1)

    rows = load_rows(args.results)
    r1_list: list[str] = []
    r2_list: list[str] = []
    skipped = 0
    by_cat: dict[str, tuple[list[str], list[str]]] = {}

    for r in rows:
        a = normalize_label(r.get("label"))
        b = normalize_label(r.get("label_rater2"))
        if a is None or b is None:
            skipped += 1
            continue
        r1_list.append(a)
        r2_list.append(b)
        cat = str(r.get("category") or "unknown")
        if cat not in by_cat:
            by_cat[cat] = ([], [])
        by_cat[cat][0].append(a)
        by_cat[cat][1].append(b)

    kappa, p_o, p_e, n = cohen_kappa(r1_list, r2_list)
    print(f"Rows with both labels: n={n} (skipped missing/invalid: {skipped})")
    if n == 0:
        print("No paired labels; merge label_rater2 from IRR export into --results file.")
        sys.exit(2)
    kappa_str = f"{kappa:.4f}" if kappa is not None else "n/a"
    print(f"Overall agreement p_o={p_o:.4f}, chance p_e={p_e:.4f}, Cohen's κ={kappa_str}")

    if args.by_category:
        print("\nStratified by category (emphasis: PARTIAL-heavy cells in narrative):")
        for cat in sorted(by_cat.keys()):
            xs, ys = by_cat[cat]
            k, po, pe, nn = cohen_kappa(xs, ys)
            k_str = f"{k:.4f}" if k is not None else "n/a"
            print(f"  {cat}: n={nn}, p_o={po:.4f}, κ={k_str}")


if __name__ == "__main__":
    main()
