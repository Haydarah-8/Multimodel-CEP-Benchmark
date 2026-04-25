"""
Export a pre-specified subset of rows for dual coding / IRR (replication protocol §1).

Default rule (configurable):
  - Include 100% of rows where label is `unsafe`
  - Include a random fraction of all other rows (default 0.20) with fixed seed

Outputs JSON list of row dicts (same schema as results.json). Second rater fills
`label_rater2` in a copy or in a spreadsheet keyed by `id`; merge per RESULTS_SCHEMA.md.

Usage:
  python scripts/export_irr_subset.py
  python scripts/export_irr_subset.py --results results.json --out irr_subset_ids.json --fraction 0.2 --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import PILOT_RESULTS_JSON  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=PILOT_RESULTS_JSON)
    ap.add_argument("--out", type=Path, default=ROOT / "irr_subset_for_rater2.json")
    ap.add_argument(
        "--fraction",
        type=float,
        default=0.2,
        help="Fraction of non-UNSAFE rows to include (0–1)",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if not args.results.is_file():
        print(f"Missing {args.results}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.fraction <= 1:
        print("--fraction must be in [0, 1]", file=sys.stderr)
        sys.exit(1)

    with args.results.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)

    unsafe_rows = [r for r in rows if (r.get("label") or "").strip().lower() == "unsafe"]
    other_rows = [r for r in rows if (r.get("label") or "").strip().lower() != "unsafe"]

    rng = random.Random(args.seed)
    k = int(round(args.fraction * len(other_rows)))
    sampled = rng.sample(other_rows, k=min(k, len(other_rows)))

    subset = unsafe_rows + sampled
    subset.sort(key=lambda r: (str(r.get("category", "")), int(r.get("id", 0) or 0)))

    payload = {
        "protocol": "100% UNSAFE rows + random fraction of remainder",
        "fraction_of_non_unsafe": args.fraction,
        "seed": args.seed,
        "n_total": len(rows),
        "n_unsafe_included": len(unsafe_rows),
        "n_other_sampled": len(sampled),
        "n_subset": len(subset),
        "rows": subset,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    print(f"Wrote {args.out} ({len(subset)} rows). Second rater: add label_rater2 per RESULTS_SCHEMA.md.")


if __name__ == "__main__":
    main()
