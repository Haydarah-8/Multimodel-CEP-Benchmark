"""
Verify results.json label counts match significance_stats.json contingency table.

Run from llm-safety-experiment:
  python scripts/verify_artifact_chain.py
  python scripts/verify_artifact_chain.py --results results.json --stats significance_stats.json

Exit 0 if consistent; exit 1 with diff if not.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import PILOT_RESULTS_JSON  # noqa: E402


def contingency_from_results(path: Path) -> list[list[int]]:
    from collections import defaultdict

    CAT_ORDER = ["direct", "indirect", "emotional", "escalation", "roleplay"]
    LABEL_ORDER = ["safe", "partial", "unsafe"]
    counts: dict[str, dict[str, int]] = {
        c: {lab: 0 for lab in LABEL_ORDER} for c in CAT_ORDER
    }
    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    for r in rows:
        cat = (r.get("category") or "").strip().lower()
        lab = (r.get("label") or "").strip().lower()
        if cat in counts and lab in counts[cat]:
            counts[cat][lab] += 1
    return [[counts[c][lab] for lab in LABEL_ORDER] for c in CAT_ORDER]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=PILOT_RESULTS_JSON)
    ap.add_argument(
        "--stats",
        type=Path,
        default=PILOT_RESULTS_JSON.parent / "significance_stats.json",
    )
    args = ap.parse_args()

    if not args.results.is_file():
        print(f"Missing {args.results}", file=sys.stderr)
        sys.exit(1)
    if not args.stats.is_file():
        print(f"Missing {args.stats} (run scripts/compute_significance.py first)", file=sys.stderr)
        sys.exit(1)

    got = contingency_from_results(args.results)
    with args.stats.open(encoding="utf-8") as f:
        stats = json.load(f)
    expected = stats["contingency_5x3"]["counts"]

    if got != expected:
        print("Mismatch: results.json contingency vs significance_stats.json", file=sys.stderr)
        print("  from results:", got, file=sys.stderr)
        print("  from stats:  ", expected, file=sys.stderr)
        sys.exit(1)

    n = sum(sum(row) for row in got)
    print(f"OK: {args.results.name} matches {args.stats.name} (5x3 table, n={n}).")


if __name__ == "__main__":
    main()
