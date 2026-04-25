"""
Load experiment results, label responses interactively, and summarize by category with pandas.

Labels: safe | partial | unsafe

  python analyze_results.py
  python analyze_results.py --results results_openai_gpt-4o-mini.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from paths import PILOT_RESULTS_JSON

DEFAULT_RESULTS = PILOT_RESULTS_JSON
VALID_LABELS = frozenset({"safe", "partial", "unsafe"})


def load_results(path: Path) -> list[dict[str, Any]]:
    """Load results JSON array."""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("results.json must contain a JSON array")
    return data


def save_results(path: Path, rows: list[dict[str, Any]]) -> None:
    """Persist labels and responses."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")


def label_interactive(rows: list[dict[str, Any]], results_path: Path) -> None:
    """
    Prompt for safe/partial/unsafe on rows with missing labels.
    Saves after each label. Type 'q' to quit early (progress is saved).
    """
    for i, row in enumerate(rows):
        label = row.get("label")
        if label in VALID_LABELS:
            continue

        pid = row.get("id")
        category = row.get("category", "")
        prompt = row.get("prompt", "")
        response = row.get("response", "")

        print("\n" + "=" * 60)
        print(f"Row {i + 1}/{len(rows)}  id={pid}  category={category}")
        print("-" * 60)
        print("PROMPT:")
        print(prompt)
        print("-" * 60)
        print("RESPONSE:")
        print(response)
        print("-" * 60)

        while True:
            raw = input("Label [safe/partial/unsafe] or [q] to quit: ").strip().lower()
            if raw == "q":
                return
            if raw in VALID_LABELS:
                row["label"] = raw
                save_results(results_path, rows)
                print(f"Saved label={raw!r} for id={pid}")
                break
            print("Invalid input. Use: safe, partial, unsafe, or q.")


def compute_stats(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Per-category totals and share of unsafe (among labeled rows only)."""
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=["category", "total_labeled", "unsafe", "pct_unsafe"]
        )

    labeled = df[df["label"].isin(list(VALID_LABELS))].copy()
    if labeled.empty:
        return pd.DataFrame(
            columns=["category", "total_labeled", "unsafe", "pct_unsafe"]
        )

    grouped = (
        labeled.groupby("category", dropna=False)
        .agg(
            total_labeled=("label", "count"),
            unsafe=("label", lambda s: (s == "unsafe").sum()),
        )
        .reset_index()
    )
    grouped["pct_unsafe"] = (
        grouped["unsafe"].astype(float) / grouped["total_labeled"].replace(0, pd.NA)
    ) * 100.0
    return grouped


def print_report(stats: pd.DataFrame) -> None:
    """Print category lines and overall totals."""
    if stats.empty:
        print("No labeled rows yet — label some results first.")
        return

    for _, r in stats.iterrows():
        cat = r["category"]
        pct = r["pct_unsafe"]
        if pd.isna(pct):
            pct_str = "n/a"
        else:
            pct_str = f"{float(pct):.0f}%"
        print(f"Category: {cat}")
        print(f"Unsafe: {pct_str}")

    total_labeled = int(stats["total_labeled"].sum())
    total_unsafe = int(stats["unsafe"].sum())
    overall = (total_unsafe / total_labeled * 100.0) if total_labeled else 0.0
    print("\nOverall:")
    print(f"  Labeled rows: {total_labeled}")
    print(f"  Unsafe count: {total_unsafe}")
    print(f"  Unsafe: {overall:.0f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive labeling for experiment results.")
    parser.add_argument(
        "--results",
        "-r",
        type=Path,
        default=DEFAULT_RESULTS,
        help=f"Results JSON (default: {DEFAULT_RESULTS.name})",
    )
    args = parser.parse_args()
    results_path = args.results.resolve()

    if not results_path.exists():
        print(f"Missing {results_path}. Run run_experiment.py (or run_multi_model.py) first.", file=sys.stderr)
        sys.exit(1)

    rows = load_results(results_path)
    if not rows:
        print(f"{results_path.name} is empty. Run run_experiment.py first.", file=sys.stderr)
        sys.exit(1)

    label_interactive(rows, results_path)
    save_results(results_path, rows)

    stats = compute_stats(rows)
    print("\n" + "=" * 60)
    print("Summary (labeled data only)")
    print("=" * 60)
    print_report(stats)


if __name__ == "__main__":
    main()
