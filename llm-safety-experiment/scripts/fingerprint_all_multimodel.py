"""
Batch: compute model_fingerprint.json + fingerprint figure for every results_*.json under results/multimodel.

Writes:
  <tier>/figures/<results_stem>/model_fingerprint.json
  <tier>/figures/<results_stem>/fig_model_fingerprint_curves.png

Usage (from llm-safety-experiment):
  python scripts/fingerprint_all_multimodel.py
  python scripts/fingerprint_all_multimodel.py --root results/multimodel/cheap
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def discover(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("results_*.json"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        type=Path,
        default=ROOT / "results" / "multimodel",
        help="Directory tree to search for results_*.json",
    )
    args = ap.parse_args()

    files = discover(args.root)
    if not files:
        print(f"No results_*.json under {args.root}", file=sys.stderr)
        sys.exit(1)

    py = sys.executable
    compute = ROOT / "scripts" / "compute_model_fingerprints.py"
    plot = ROOT / "scripts" / "plot_model_fingerprints.py"

    for fp in files:
        stem = fp.stem
        out_dir = fp.parent / "figures" / stem
        out_json = out_dir / "model_fingerprint.json"
        out_png = out_dir / "fig_model_fingerprint_curves.png"
        out_dir.mkdir(parents=True, exist_ok=True)
        r1 = subprocess.run(
            [str(py), str(compute), "--results", str(fp), "--out", str(out_json)],
            cwd=str(ROOT),
            check=False,
        )
        if r1.returncode != 0:
            print(f"compute_model_fingerprints failed for {fp}", file=sys.stderr)
            sys.exit(r1.returncode)
        r2 = subprocess.run(
            [str(py), str(plot), "--fingerprint-json", str(out_json), "--out", str(out_png)],
            cwd=str(ROOT),
            check=False,
        )
        if r2.returncode != 0:
            print(f"plot_model_fingerprints failed for {out_json}", file=sys.stderr)
            sys.exit(r2.returncode)
        print(out_json, file=sys.stderr)
        print(out_png, file=sys.stderr)


if __name__ == "__main__":
    main()
