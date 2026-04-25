"""
Run all tier × provider batches from configs/tier_models.json (3 subprocesses × 3 providers × 90 prompts).

Usage (from llm-safety-experiment):

  python scripts/run_all_tiers.py
  python scripts/run_all_tiers.py --dry-run
  python scripts/run_all_tiers.py --max-prompts 2   # smoke test

Requires API keys in .env. Expensive tier uses frontier models; confirm ids in tier_models.json.
After a run, search outputs for ``ERROR:`` in ``response`` fields; re-run failed provider:model
pairs only via ``python run_multi_model.py --output-dir results/multimodel/<tier> ...``.
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

from paths import PROMPTS_FILE, TIER_MODELS_CONFIG, TIER_DIRS  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Run multi-model batches for cheap/mid/expensive tiers.")
    ap.add_argument("--dry-run", action="store_true", help="Print commands only")
    ap.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        metavar="N",
        help="Forward to run_multi_model.py: only first N prompts (smoke test).",
    )
    ap.add_argument(
        "--config",
        type=Path,
        default=TIER_MODELS_CONFIG,
        help="JSON mapping tier -> provider -> model id",
    )
    args = ap.parse_args()

    raw = json.loads(args.config.read_text(encoding="utf-8"))
    tiers = {k: v for k, v in raw.items() if not str(k).startswith("_")}
    run_multi = ROOT / "run_multi_model.py"

    for tier_name, providers in tiers.items():
        out_dir = TIER_DIRS.get(tier_name)
        if out_dir is None:
            continue
        specs: list[str] = []
        for prov, model in sorted(providers.items()):
            if str(prov).startswith("_"):
                continue
            if prov not in ("openai", "anthropic", "gemini"):
                continue
            specs.append(f"{prov}:{model}")
        if not specs:
            continue
        cmd = [
            sys.executable,
            str(run_multi),
            "--prompts",
            str(PROMPTS_FILE),
            "--output-dir",
            str(out_dir),
        ]
        if args.max_prompts is not None:
            cmd.extend(["--max-prompts", str(args.max_prompts)])
        cmd.extend(specs)
        print(" ".join(cmd))
        if args.dry_run:
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            sys.exit(r.returncode)

    if not args.dry_run:
        print("\nDone. Next: human-label each results file, then compute_significance / verify / figures.")


if __name__ == "__main__":
    main()
