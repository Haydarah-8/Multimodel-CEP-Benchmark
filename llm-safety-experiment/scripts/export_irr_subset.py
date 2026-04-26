"""
Export a pre-specified subset of rows for dual coding / IRR (replication protocol §1).

Default rule (configurable):
  - Include 100% of rows where label is `unsafe`
  - Optionally include 100% of rows where label is `partial` (--include-all-partial; recommended for κ on the highest-variance band)
  - Include a random fraction of remaining rows (default 0.20 of that pool) with fixed seed

Outputs JSON list of row dicts (same schema as results.json). Second rater fills
`label_rater2` in a copy or in a spreadsheet keyed by `id`; merge per RESULTS_SCHEMA.md.

Usage:
  python scripts/export_irr_subset.py
  python scripts/export_irr_subset.py --results results.json --out irr_subset_ids.json --fraction 0.2 --seed 42
  python scripts/export_irr_subset.py --include-all-partial
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
        help="With --include-all-partial: fraction of SAFE rows to sample. Otherwise: fraction of all non-UNSAFE rows (0–1).",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--include-all-partial",
        action="store_true",
        help="Include every PARTIAL row; random fraction applies only to SAFE-only remainder",
    )
    args = ap.parse_args()

    if not args.results.is_file():
        print(f"Missing {args.results}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.fraction <= 1:
        print("--fraction must be in [0, 1]", file=sys.stderr)
        sys.exit(1)

    with args.results.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)

    def norm_label(r: dict) -> str:
        return (r.get("label") or "").strip().lower()

    unsafe_rows = [r for r in rows if norm_label(r) == "unsafe"]
    partial_rows = [r for r in rows if norm_label(r) == "partial"]
    safe_rows = [r for r in rows if norm_label(r) == "safe"]

    rng = random.Random(args.seed)
    if args.include_all_partial:
        pool_for_fraction = safe_rows
        protocol = "100% UNSAFE + 100% PARTIAL + random fraction of SAFE-only remainder"
    else:
        pool_for_fraction = [r for r in rows if norm_label(r) != "unsafe"]
        protocol = "100% UNSAFE rows + random fraction of remainder"

    k = int(round(args.fraction * len(pool_for_fraction)))
    sampled = rng.sample(pool_for_fraction, k=min(k, len(pool_for_fraction)))

    if args.include_all_partial:
        subset = unsafe_rows + partial_rows + sampled
    else:
        subset = unsafe_rows + sampled

    # Deduplicate by prompt id (stable)
    seen: set[object] = set()
    deduped: list[dict] = []
    for r in subset:
        rid = r.get("id")
        if rid in seen:
            continue
        seen.add(rid)
        deduped.append(r)
    deduped.sort(key=lambda r: (str(r.get("category", "")), int(r.get("id", 0) or 0)))

    payload = {
        "protocol": protocol,
        "include_all_partial": args.include_all_partial,
        "fraction_applied_pool": args.fraction,
        "seed": args.seed,
        "n_total": len(rows),
        "n_unsafe_included": len(unsafe_rows),
        "n_partial_included": len(partial_rows) if args.include_all_partial else 0,
        "n_from_fraction_sample": len(sampled),
        "n_subset": len(deduped),
        "rows": deduped,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    print(
        f"Wrote {args.out} ({len(deduped)} rows). Second rater: add label_rater2 per RESULTS_SCHEMA.md. "
        "Then: python scripts/compute_irr_kappa.py --results <merged.json>"
    )


if __name__ == "__main__":
    main()
