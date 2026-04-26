"""
Tabulate label rates by mutation_kind × category for a labeled results file.

Run from llm-safety-experiment:

  python scripts/summarize_mutation_wave.py --results results/wave/results_openai_gpt-4o-mini.json

Rows without mutation_kind are counted under \"(none)\" for backward compatibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize mutation wave results by kind × category.")
    parser.add_argument("--results", type=Path, required=True, help="Labeled results JSON.")
    args = parser.parse_args()
    path = args.results.resolve()
    with path.open(encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        print("results must be a JSON array", file=sys.stderr)
        sys.exit(1)

    # cells[(kind, cat)] = {label: count, "total": n}
    cells: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for r in rows:
        if not isinstance(r, dict):
            continue
        kind = r.get("mutation_kind")
        k = str(kind) if kind is not None else "(none)"
        cat = str(r.get("category") or "")
        label = r.get("label")
        lab = str(label) if label is not None else "(null)"
        key = (k, cat)
        cells[key][lab] += 1
        cells[key]["_total"] += 1

    keys = sorted(cells.keys(), key=lambda x: (x[0], x[1]))
    print(f"File: {path.name}\n")
    print(f"{'mutation_kind':<22} {'category':<14} {'n':>5}  unsafe%  partial%  safe%")
    for k, c in keys:
        d = cells[(k, c)]
        total = d["_total"]
        nu = d.get("unsafe", 0)
        np_ = d.get("partial", 0)
        ns = d.get("safe", 0)
        pu = 100.0 * nu / total if total else 0.0
        pp = 100.0 * np_ / total if total else 0.0
        ps = 100.0 * ns / total if total else 0.0
        print(f"{k:<22} {c:<14} {total:5d}  {pu:6.1f}  {pp:6.1f}  {ps:6.1f}")


if __name__ == "__main__":
    main()
