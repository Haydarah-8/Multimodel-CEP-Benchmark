"""
Copy safe/partial/unsafe labels from a pilot results file into a multi-model
results JSON by matching prompt row ``id``.

This does **not** replace human labeling of each model's *responses* for a
published study; it seeds the same rubric labels by prompt id so offline scripts
(significance, figures, verify) can run. For full per-model annotation, use
``analyze_results.py --results <path>`` interactively instead.

Usage (from llm-safety-experiment):

  python scripts/seed_labels_from_pilot.py --target results_openai_gpt-4o.json
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
VALID = frozenset({"safe", "partial", "unsafe"})


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed labels from pilot results by row id.")
    ap.add_argument(
        "--pilot",
        type=Path,
        default=PILOT_RESULTS_JSON,
        help="Labeled pilot JSON (default: results/pilot/results.json)",
    )
    ap.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Multi-model results file to update in place",
    )
    ap.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing labels when pilot has a value (default: only fill null/missing)",
    )
    args = ap.parse_args()

    pilot_path = args.pilot.resolve()
    target_path = args.target.resolve()
    if not pilot_path.is_file():
        print(f"Missing pilot: {pilot_path}", file=sys.stderr)
        sys.exit(1)
    if not target_path.is_file():
        print(f"Missing target: {target_path}", file=sys.stderr)
        sys.exit(1)

    with pilot_path.open(encoding="utf-8") as f:
        pilot: list[dict] = json.load(f)
    id_to_label: dict[object, str] = {}
    for r in pilot:
        pid = r.get("id")
        lab = str(r.get("label") or "").strip().lower()
        if lab in VALID:
            id_to_label[pid] = lab

    with target_path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)

    filled = 0
    for r in rows:
        pid = r.get("id")
        if pid not in id_to_label:
            continue
        cur = str(r.get("label") or "").strip().lower()
        if cur in VALID and not args.overwrite:
            continue
        r["label"] = id_to_label[pid]
        filled += 1

    with target_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(
        f"Updated {target_path.name}: applied {filled} label(s) from "
        f"{pilot_path.name} (pilot map size={len(id_to_label)})."
    )


if __name__ == "__main__":
    main()
