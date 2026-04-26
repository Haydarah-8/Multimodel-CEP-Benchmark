"""
Run the same prompt bank against multiple API + model pairs; one results JSON per pair.

Specs: `openai:gpt-4o-mini`, `anthropic:claude-3-haiku-20240307`, `gemini:gemini-2.5-flash`.
Bare model id (no colon) means OpenAI: `gpt-4o-mini` -> `openai:gpt-4o-mini`.

Usage (from llm-safety-experiment):
  python run_multi_model.py openai:gpt-4o-mini anthropic:claude-3-haiku-20240307
  python run_multi_model.py --tier cheap openai:gpt-4o-mini anthropic:... gemini:...
  python run_multi_model.py --output-dir results/multimodel/mid gpt-4o
  python run_multi_model.py   # uses MULTI_MODELS env (comma-separated)

Each output: results_<provider>_<model_slug>.json under --output-dir (default: results/multimodel/unsorted).

Secrets: OPENAI_API_KEY for openai; ANTHROPIC_API_KEY for anthropic;
GEMINI_API_KEY or GOOGLE_API_KEY for gemini.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from paths import PROMPTS_FILE, TIER_DIRS, UNSORTED_MULTIMODEL_DIR
from provider_clients import ProviderName
from run_experiment import (
    load_prompts,
    require_api_key,
    results_slug,
    run_all,
    save_results,
)

ROOT = Path(__file__).resolve().parent


def parse_spec(token: str) -> tuple[ProviderName, str]:
    """Parse `provider:model` or bare `model` (implies openai)."""
    s = token.strip()
    if not s:
        raise ValueError("empty spec")
    if ":" in s:
        p, m = s.split(":", 1)
        prov = p.strip().lower()
        model = m.strip()
        if prov not in ("openai", "anthropic", "gemini"):
            raise ValueError(f"Unknown provider in {token!r} (use openai, anthropic, or gemini)")
        if not model:
            raise ValueError(f"Missing model after ':' in {token!r}")
        return prov, model  # type: ignore[return-value]
    return "openai", s


def parse_specs(argv: list[str]) -> list[tuple[ProviderName, str]]:
    if argv:
        raw = [x for x in argv if str(x).strip()]
    else:
        env = os.getenv("MULTI_MODELS", "").strip()
        if not env:
            print(
                "Pass provider:model specs as arguments, e.g.:\n"
                "  python run_multi_model.py openai:gpt-4o-mini anthropic:claude-3-haiku-20240307\n"
                "  python run_multi_model.py --tier cheap openai:gpt-4o-mini anthropic:... gemini:...\n"
                "Or set MULTI_MODELS=openai:gpt-4o-mini,gemini:gemini-2.5-flash",
                file=sys.stderr,
            )
            sys.exit(1)
        raw = [m.strip() for m in env.split(",") if m.strip()]
    out: list[tuple[ProviderName, str]] = []
    for t in raw:
        try:
            out.append(parse_spec(t))
        except ValueError as e:
            print(f"Bad spec {t!r}: {e}", file=sys.stderr)
            sys.exit(1)
    return out


def resolve_output_base(tier: str | None, output_dir: Path | None) -> Path:
    if tier and output_dir is not None:
        print("Use only one of --tier or --output-dir.", file=sys.stderr)
        sys.exit(1)
    if tier:
        return TIER_DIRS[tier]
    if output_dir is not None:
        return output_dir.resolve()
    return UNSORTED_MULTIMODEL_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-provider runs; one JSON per provider:model.")
    parser.add_argument(
        "--prompts",
        type=Path,
        default=PROMPTS_FILE,
        help="Prompt bank JSON (default: prompts.json)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Directory for results_<provider>_<slug>.json (default: results/multimodel/unsorted)",
    )
    parser.add_argument(
        "--tier",
        choices=("cheap", "mid", "expensive"),
        default=None,
        help="Shortcut for --output-dir results/multimodel/<tier>",
    )
    parser.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        metavar="N",
        help="Only run the first N prompts from the bank (smoke test / cost cap).",
    )
    parser.add_argument(
        "--mutation-wave",
        default=None,
        metavar="NAME",
        help="Stored on each result row as mutation_wave (wave runs).",
    )
    parser.add_argument(
        "specs",
        nargs="*",
        help="provider:model pairs (or bare model id = openai)",
    )
    args = parser.parse_args()

    load_dotenv()
    out_base = resolve_output_base(args.tier, args.output_dir)
    specs = parse_specs(args.specs)
    for provider in {p for p, _ in specs}:
        require_api_key(provider)

    prompts_path = args.prompts.resolve()
    prompts = load_prompts(prompts_path)
    if args.max_prompts is not None:
        if args.max_prompts < 1:
            print("--max-prompts must be >= 1.", file=sys.stderr)
            sys.exit(1)
        prompts = prompts[: args.max_prompts]
    print(f"Loaded {len(prompts)} prompts from {prompts_path.name}; {len(specs)} run(s).\n")

    out_base.mkdir(parents=True, exist_ok=True)

    for provider, model in specs:
        slug = results_slug(provider, model)
        out_path = out_base / f"results_{slug}.json"
        try:
            rel = out_path.relative_to(ROOT)
        except ValueError:
            rel = out_path
        print(f"=== {provider!r} / {model!r} -> {rel} ===")
        results = run_all(provider, model, prompts, mutation_wave=args.mutation_wave)
        save_results(out_path, results)
        print(f"Wrote {len(results)} rows.\n")

    print("Next: label each file (analyze_results.py --results <path>), then significance / figures.")


if __name__ == "__main__":
    main()
