"""
After human labeling: run compute_significance, verify_artifact_chain, and generate_report_figures
for each fully labeled results_*.json under results/multimodel (optional: extra paths e.g. pilot).

Fully labeled = every row has label in {safe, partial, unsafe}.

Usage (from llm-safety-experiment):
  python scripts/postprocess_multimodel_tiers.py
  python scripts/postprocess_multimodel_tiers.py --also results/pilot/results.json
  python scripts/postprocess_multimodel_tiers.py --skip-figures
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALID_LABELS = frozenset({"safe", "partial", "unsafe"})


def is_fully_labeled(rows: list[dict]) -> bool:
    if not rows:
        return False
    for r in rows:
        lab = str(r.get("label") or "").strip().lower()
        if lab not in VALID_LABELS:
            return False
    return True


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return data


def discover_results(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("results_*.json"))


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Run significance / verify / figures for labeled multimodel (and optional) results JSON."
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=ROOT / "results" / "multimodel",
        help="Directory tree to scan for results_*.json (default: results/multimodel)",
    )
    ap.add_argument(
        "--also",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help="Additional results JSON (repeatable), e.g. results/pilot/results.json",
    )
    ap.add_argument("--skip-figures", action="store_true", help="Skip generate_report_figures.py")
    ap.add_argument(
        "--skip-sankey",
        action="store_true",
        help="Forward --skip-sankey to generate_report_figures.py",
    )
    args = ap.parse_args()

    seen: set[Path] = set()
    ordered: list[Path] = []
    for extra in args.also:
        rp = extra.resolve()
        if rp.is_file() and rp not in seen:
            seen.add(rp)
            ordered.append(rp)
    for p in discover_results(args.root.resolve()):
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            ordered.append(rp)

    if not ordered:
        print("No results_*.json found and no --also paths; nothing to do.", file=sys.stderr)
        sys.exit(0)

    compute = ROOT / "scripts" / "compute_significance.py"
    verify = ROOT / "scripts" / "verify_artifact_chain.py"
    figures = ROOT / "scripts" / "generate_report_figures.py"

    for results_path in ordered:
        try:
            rows = load_rows(results_path)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"Skip {results_path}: {e}", file=sys.stderr)
            continue
        if not is_fully_labeled(rows):
            n_ok = sum(1 for r in rows if str(r.get("label") or "").strip().lower() in VALID_LABELS)
            print(f"Skip (not fully labeled): {results_path} ({n_ok}/{len(rows)} labeled)")
            continue

        stats_path = results_path.parent / (
            "significance_stats.json"
            if results_path.name == "results.json"
            else f"significance_stats_{results_path.stem}.json"
        )
        fig_dir = results_path.parent / "figures" / results_path.stem

        print(f"\n=== {results_path.relative_to(ROOT)} ===")
        r = subprocess.run(
            [sys.executable, str(compute), "--results", str(results_path), "--out", str(stats_path)],
            cwd=ROOT,
        )
        if r.returncode != 0:
            sys.exit(r.returncode)
        r = subprocess.run(
            [sys.executable, str(verify), "--results", str(results_path), "--stats", str(stats_path)],
            cwd=ROOT,
        )
        if r.returncode != 0:
            sys.exit(r.returncode)
        if not args.skip_figures:
            fig_dir.mkdir(parents=True, exist_ok=True)
            cmd = [
                sys.executable,
                str(figures),
                "--results",
                str(results_path),
                "--figures-dir",
                str(fig_dir),
            ]
            if args.skip_sankey:
                cmd.append("--skip-sankey")
            r = subprocess.run(cmd, cwd=ROOT)
            if r.returncode != 0:
                sys.exit(r.returncode)

    print("\nDone.")


if __name__ == "__main__":
    main()
