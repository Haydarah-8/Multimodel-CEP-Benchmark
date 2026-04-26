"""
Build a wide table: one row per prompt id with category and per-model primary labels.

Reads every results_*.json under results/multimodel/ (and optionally pilot).
No API calls — for cross-model "why differ" inspection and manual failure_mode coding.

Usage (from llm-safety-experiment):
  python scripts/export_paired_error_table.py
  python scripts/export_paired_error_table.py --out results/multimodel/paired_labels_wide.csv
  python scripts/export_paired_error_table.py --also-pilot --markdown results/multimodel/paired_labels_wide.md
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import PILOT_RESULTS_JSON  # noqa: E402


def discover_multimodel_results() -> list[Path]:
    base = ROOT / "results" / "multimodel"
    if not base.is_dir():
        return []
    return sorted(base.rglob("results_*.json"))


def stem_from_path(p: Path) -> str:
    return p.stem


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description="Wide paired label table across multimodel JSON files")
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "multimodel" / "paired_labels_wide.csv",
        help="Output CSV path",
    )
    ap.add_argument(
        "--also-pilot",
        action="store_true",
        help=f"Include pilot as column pilot_results from {PILOT_RESULTS_JSON.name}",
    )
    ap.add_argument(
        "--markdown",
        type=Path,
        default=None,
        help="Optional second output: GitHub-flavored markdown table",
    )
    args = ap.parse_args()

    files = discover_multimodel_results()
    if args.also_pilot and PILOT_RESULTS_JSON.is_file():
        files = [PILOT_RESULTS_JSON] + files

    if not files:
        print("No results_*.json found under results/multimodel/", file=sys.stderr)
        sys.exit(1)

    # id -> category (first seen), id -> { stem -> label }
    category_by_id: dict[str | int, str] = {}
    labels_by_id: dict[str | int, dict[str, str]] = defaultdict(dict)

    for fp in files:
        stem = "pilot_results" if fp.resolve() == PILOT_RESULTS_JSON.resolve() else stem_from_path(fp)
        rows = load_rows(fp)
        for r in rows:
            rid = r.get("id")
            cat = str(r.get("category") or "")
            lab = (r.get("label") or "").strip().lower()
            if rid not in category_by_id and cat:
                category_by_id[rid] = cat
            if lab:
                labels_by_id[rid][stem] = lab

    all_stems: list[str] = sorted({s for d in labels_by_id.values() for s in d})
    def sort_key(x: object) -> tuple[str, str]:
        cat = str(category_by_id.get(x, ""))
        return (cat, str(x))

    ids_sorted = sorted(labels_by_id.keys(), key=sort_key)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["id", "category"] + all_stems
    with args.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rid in ids_sorted:
            row = {"id": rid, "category": category_by_id.get(rid, "")}
            for s in all_stems:
                row[s] = labels_by_id[rid].get(s, "")
            w.writerow(row)

    print(f"Wrote {args.out} ({len(ids_sorted)} rows, {len(all_stems)} model columns).")

    if args.markdown:
        lines = [
            "| " + " | ".join(fieldnames) + " |",
            "| " + " | ".join("---" for _ in fieldnames) + " |",
        ]
        for rid in ids_sorted:
            cells = [str(rid), category_by_id.get(rid, "")]
            for s in all_stems:
                cells.append(labels_by_id[rid].get(s, ""))
            lines.append("| " + " | ".join(cells) + " |")
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {args.markdown}")


if __name__ == "__main__":
    main()
