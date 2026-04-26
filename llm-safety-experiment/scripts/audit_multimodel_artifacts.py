"""
Scan labeled multimodel results JSON for integrity: ERROR responses, missing labels, row count.

Usage (from llm-safety-experiment):
  python scripts/audit_multimodel_artifacts.py
  python scripts/audit_multimodel_artifacts.py --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paths import MULTIMODEL_DIR  # noqa: E402

VALID = frozenset({"safe", "partial", "unsafe"})
EXPECTED_N = 90


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def audit_file(path: Path) -> dict[str, Any]:
    rows = load_rows(path)
    n = len(rows)
    err = 0
    unlabeled = 0
    bad_label = 0
    for r in rows:
        resp = str(r.get("response") or "")
        if resp.lstrip().upper().startswith("ERROR:"):
            err += 1
        lab = str(r.get("label") or "").strip().lower()
        if not lab:
            unlabeled += 1
        elif lab not in VALID:
            bad_label += 1
    return {
        "path": path,
        "n_rows": n,
        "error_responses": err,
        "unlabeled": unlabeled,
        "bad_label": bad_label,
        "ok_rows": n - unlabeled - bad_label,
    }


def discover(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("results_*.json"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit multimodel results JSON for ERROR / labels")
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any ERROR response, missing label, bad label, or n != 90",
    )
    args = ap.parse_args()

    files = discover(args.root)
    if not files:
        print(f"No results_*.json under {args.root}", file=sys.stderr)
        sys.exit(1)

    problems = 0
    print(f"{'file':<55} {'n':>4} {'ERR':>4} {'unlab':>5} {'bad':>4}")
    for fp in files:
        try:
            rel = fp.relative_to(ROOT)
        except ValueError:
            rel = fp
        a = audit_file(fp)
        print(
            f"{str(rel):<55} {a['n_rows']:>4} {a['error_responses']:>4} "
            f"{a['unlabeled']:>5} {a['bad_label']:>4}"
        )
        if a["n_rows"] != EXPECTED_N:
            problems += 1
            print(f"  !! expected {EXPECTED_N} rows", file=sys.stderr)
        if a["error_responses"] or a["unlabeled"] or a["bad_label"]:
            problems += 1

    print(
        "\nNote: configs/tier_models.json uses gemini-2.5-pro for both mid and expensive tiers.",
        file=sys.stderr,
    )
    print(
        "Nine JSON files = nine API runs; eight unique provider x model-id configurations.\n",
        file=sys.stderr,
    )

    if args.strict and problems:
        sys.exit(1)
    if problems and not args.strict:
        print(
            f"Found {problems} issue line(s); re-run with --strict to fail CI.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
