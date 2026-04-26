"""
Run LLM safety prompts against OpenAI, Anthropic, or Google Gemini; save structured rows.

Use --provider and --model. Default OpenAI + gpt-4o-mini writes results/pilot/results.json;
other providers default to results/multimodel/unsorted/results_<provider>_<model_slug>.json when --output is omitted.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from paths import PILOT_RESULTS_JSON, PROMPTS_FILE, UNSORTED_MULTIMODEL_DIR
from provider_clients import ProviderName, MAX_TOKENS as _MAX_TOKENS
from provider_clients import complete

# Default OpenAI model; override with OPENAI_MODEL
MODEL = "gpt-4o-mini"

RESULTS_FILE = PILOT_RESULTS_JSON
MAX_TOKENS = _MAX_TOKENS


def model_slug(model: str) -> str:
    """Filesystem-safe slug (alnum, dash, dot, underscore)."""
    s = re.sub(r"[^\w\-.]+", "_", model.strip(), flags=re.UNICODE)
    s = re.sub(r"_+", "_", s).strip("_")
    return (s[:96] if s else "model")


def results_slug(provider: str, model: str) -> str:
    """Collision-safe prefix for default filenames: openai + model slug."""
    p = provider.strip().lower()
    return f"{p}_{model_slug(model)}"


def load_prompts(path: Path) -> list[dict]:
    """Load experiment prompts from JSON."""
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("prompts.json must contain a JSON array")
    return data


def run_all(
    provider: ProviderName,
    model: str,
    prompts: list[dict],
    *,
    mutation_wave: str | None = None,
) -> list[dict]:
    """Execute each prompt; label left null for manual review.

    Wave files (from ``expand_prompt_wave``) may include ``parent_id`` and
    ``mutation``; those map to optional provenance fields on each result row.
    """
    results: list[dict] = []
    total = len(prompts)
    for i, row in enumerate(prompts, start=1):
        pid = row.get("id")
        category = row.get("category", "")
        text = row.get("text", "")
        preview = text[:60] + ("…" if len(text) > 60 else "")
        print(f"[{i}/{total}] id={pid} category={category} prompt={preview!r}")

        response = complete(provider, model, text)
        out: dict = {
            "id": pid,
            "category": category,
            "prompt": text,
            "response": response,
            "provider": provider,
            "model": model,
            "label": None,
        }
        if "parent_id" in row and row.get("parent_id") is not None:
            out["parent_prompt_id"] = row.get("parent_id")
        mut = row.get("mutation")
        if isinstance(mut, dict):
            if mut.get("kind") is not None:
                out["mutation_kind"] = mut.get("kind")
            if mut.get("variant") is not None:
                out["mutation_variant"] = mut.get("variant")
            if mut.get("schema_version") is not None:
                out["mutation_schema_version"] = mut.get("schema_version")
        if mutation_wave:
            out["mutation_wave"] = mutation_wave
        results.append(out)
    return results


def save_results(path: Path, results: list[dict]) -> None:
    """Write results with stable formatting."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        f.write("\n")


def require_api_key(provider: ProviderName) -> None:
    from provider_clients import gemini_api_key

    if provider == "openai":
        k = os.getenv("OPENAI_API_KEY")
        if not k or k == "your_api_key_here":
            print("Set OPENAI_API_KEY in .env (or environment).", file=sys.stderr)
            sys.exit(1)
    elif provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("Set ANTHROPIC_API_KEY in .env (or environment).", file=sys.stderr)
            sys.exit(1)
    elif provider == "gemini":
        if not gemini_api_key():
            print("Set GEMINI_API_KEY or GOOGLE_API_KEY in .env (or environment).", file=sys.stderr)
            sys.exit(1)


def _default_output_path(provider: ProviderName, model: str) -> Path:
    """OpenAI + default model → results/pilot/results.json; else results/multimodel/unsorted/."""
    default_model = os.getenv("OPENAI_MODEL", MODEL)
    if provider == "openai" and model == default_model:
        PILOT_RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
        return RESULTS_FILE
    UNSORTED_MULTIMODEL_DIR.mkdir(parents=True, exist_ok=True)
    return UNSORTED_MULTIMODEL_DIR / f"results_{results_slug(provider, model)}.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run prompts.json against OpenAI, Anthropic, or Gemini."
    )
    parser.add_argument(
        "--provider",
        choices=("openai", "anthropic", "gemini"),
        default="openai",
        help="API backend (default: openai).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id for the provider (default: OPENAI_MODEL for openai, else required for non-default).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output JSON path. If omitted: results/pilot/results.json for OpenAI default model; else unsorted multimodel path.",
    )
    parser.add_argument(
        "--prompts",
        type=Path,
        default=PROMPTS_FILE,
        help="Prompt bank JSON (default: prompts.json).",
    )
    parser.add_argument(
        "--mutation-wave",
        default=None,
        metavar="NAME",
        help="Stored on each result row as mutation_wave (e.g. cep_wave_2026_04). Use the same name as expand_prompt_wave --wave-name.",
    )
    args = parser.parse_args()

    load_dotenv()
    provider: ProviderName = args.provider

    if args.model is None:
        if provider == "openai":
            model = os.getenv("OPENAI_MODEL", MODEL)
        else:
            print(f"--model is required when --provider is {provider!r}.", file=sys.stderr)
            sys.exit(1)
    else:
        model = args.model

    require_api_key(provider)

    if args.output is not None:
        out_path = args.output.resolve()
    else:
        out_path = _default_output_path(provider, model)

    prompts = load_prompts(args.prompts.resolve())
    print(
        f"Loaded {len(prompts)} prompts. provider={provider!r} model={model!r}, max_tokens={MAX_TOKENS}"
    )
    results = run_all(provider, model, prompts, mutation_wave=args.mutation_wave)
    save_results(out_path, results)
    print(f"Wrote {len(results)} rows to {out_path}")


if __name__ == "__main__":
    main()
