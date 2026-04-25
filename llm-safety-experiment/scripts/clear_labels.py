"""
Set every row's \"label\" to null in a results JSON so analyze_results.py will
prompt again. Use before interactive relabeling.

Usage (from llm-safety-experiment):

  python scripts/clear_labels.py --target results_openai_gpt-4o.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Clear all labels in a results JSON file.")
    ap.add_argument(
        "--target",
        type=Path,
        required=True,
        help="Results JSON to update in place",
    )
    args = ap.parse_args()
    path = args.target.resolve()
    if not path.is_file():
        print(f"Missing: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    n = 0
    for r in rows:
        if r.get("label") is not None:
            n += 1
        r["label"] = None
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Cleared labels on {len(rows)} rows ({n} were non-null): {path.name}")


if __name__ == "__main__":
    main()
