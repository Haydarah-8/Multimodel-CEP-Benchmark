"""
Summarize paired McNemar comparisons across price tiers per provider (OpenAI, Anthropic, Gemini).

Runs compare_tier_paired logic for cheap vs mid, mid vs expensive, cheap vs expensive.
Skips identical file paths (e.g. Gemini mid and expensive both gemini-2.5-pro) with a clear note.

Usage (from llm-safety-experiment):
  python scripts/summarize_tier_or.py
  python scripts/summarize_tier_or.py --out results/multimodel/tier_mcnemar_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from compare_tier_paired import compare_pair  # noqa: E402
from paths import artifact_relpath  # noqa: E402

MULTIMODEL = ROOT / "results" / "multimodel"

# Paths relative to results/multimodel/
PROVIDER_TIER_FILES: dict[str, dict[str, str]] = {
    "openai": {
        "cheap": "cheap/results_openai_gpt-4o-mini.json",
        "mid": "mid/results_openai_gpt-4o.json",
        "expensive": "expensive/results_openai_gpt-4.1.json",
    },
    "anthropic": {
        "cheap": "cheap/results_anthropic_claude-3-haiku-20240307.json",
        "mid": "mid/results_anthropic_claude-3-sonnet-20240229.json",
        "expensive": "expensive/results_anthropic_claude-3-opus-20240229.json",
    },
    "gemini": {
        "cheap": "cheap/results_gemini_gemini-2.5-flash.json",
        "mid": "mid/results_gemini_gemini-2.5-pro.json",
        "expensive": "expensive/results_gemini_gemini-2.5-pro.json",
    },
}

CONTRASTS = [
    ("cheap", "mid", "cheap_vs_mid"),
    ("mid", "expensive", "mid_vs_expensive"),
    ("cheap", "expensive", "cheap_vs_expensive"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    summary: dict = {"contrasts": [], "skipped": []}

    for provider, tiers in PROVIDER_TIER_FILES.items():
        for low, high, tag in CONTRASTS:
            rel_a = tiers[low]
            rel_b = tiers[high]
            path_a = MULTIMODEL / rel_a
            path_b = MULTIMODEL / rel_b
            if path_a.resolve() == path_b.resolve():
                summary["skipped"].append(
                    {
                        "provider": provider,
                        "contrast": tag,
                        "reason": "same file path (e.g. Gemini mid and expensive model id)",
                        "path": artifact_relpath(path_a),
                    }
                )
                continue
            if not path_a.is_file() or not path_b.is_file():
                summary["skipped"].append(
                    {
                        "provider": provider,
                        "contrast": tag,
                        "reason": "missing file",
                        "path_a": artifact_relpath(path_a),
                        "path_b": artifact_relpath(path_b),
                    }
                )
                continue
            try:
                block = compare_pair(path_a, path_b)
            except ValueError as e:
                summary["skipped"].append(
                    {"provider": provider, "contrast": tag, "reason": str(e)}
                )
                continue
            summary["contrasts"].append({"provider": provider, "contrast": tag, **block})

    text = json.dumps(summary, indent=2) + "\n"
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
