"""
Expand canonical prompts.json (or another seed bank) into a derived wave + manifest.

Run from llm-safety-experiment:

  python scripts/expand_prompt_wave.py --wave-name cep_2026_04 \\
    --kinds baseline,role_shift,emotional_escalation,framing_pattern,directness_ladder \\
    --out prompts_waves/cep_2026_04.json --manifest-out prompts_waves/cep_2026_04.manifest.json

Phase B (LLM paraphrase) requires explicit acknowledgment and API keys:

  python scripts/expand_prompt_wave.py ... --llm-paraphrase \\
    --i-understand-llm-mutation --paraphrase-provider openai --paraphrase-model gpt-4o-mini \\
    --max-llm-parents 10
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from paths import PROMPTS_FILE
from prompt_mutations.llm_paraphrase import append_llm_paraphrase_rows
from run_experiment import require_api_key
from prompt_mutations.wave import (
    MUTATION_SCHEMA_VERSION,
    build_manifest,
    expand_wave,
    load_ladder_map,
    load_registry,
)
from provider_clients import ProviderName


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _merge_dedupe_text(base: list[dict], extra: list[dict]) -> list[dict]:
    seen = {_sha256_text(str(r.get("text") or "")) for r in base}
    out = list(base)
    for r in extra:
        h = _sha256_text(str(r.get("text") or ""))
        if h in seen:
            continue
        seen.add(h)
        out.append(r)
    return out


def _load_seed(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("seed prompts file must be a JSON array")
    return data


def main() -> None:
    default_registry = ROOT / "configs" / "mutation_registry.json"
    default_ladder = ROOT / "configs" / "indirect_direct_ladder_map.json"
    default_out_dir = ROOT / "prompts_waves"

    parser = argparse.ArgumentParser(
        description="Build a versioned prompt wave from prompts.json + mutation registry."
    )
    parser.add_argument("--seed", type=Path, default=PROMPTS_FILE, help="Seed prompt bank JSON.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=default_registry,
        help="mutation_registry.json",
    )
    parser.add_argument(
        "--ladder-map",
        type=Path,
        default=default_ladder,
        help="indirect_direct_ladder_map.json (for directness_ladder).",
    )
    parser.add_argument(
        "--wave-name",
        required=True,
        metavar="NAME",
        help="Logical wave id (e.g. cep_wave_2026_04); stored alongside artifacts.",
    )
    parser.add_argument(
        "--kinds",
        default="baseline,role_shift,emotional_escalation,framing_pattern,directness_ladder",
        help="Comma-separated kinds to include.",
    )
    parser.add_argument(
        "--max-variants",
        type=int,
        default=3,
        metavar="N",
        help="Cap variants per kind per seed row (role_shift, emotional, framing).",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Omit baseline copies even if baseline is listed in --kinds.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output wave JSON path (default: prompts_waves/<wave-name>.json).",
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=None,
        help="Manifest path (default: same stem as --out + .manifest.json).",
    )
    parser.add_argument(
        "--max-prompts",
        type=int,
        default=None,
        metavar="N",
        help="Only expand the first N seed rows (smoke test).",
    )
    # Phase B
    parser.add_argument(
        "--llm-paraphrase",
        action="store_true",
        help="Append llm_paraphrase rows (one per seed row up to --max-llm-parents).",
    )
    parser.add_argument(
        "--i-understand-llm-mutation",
        action="store_true",
        help="Required (or set LLM_MUTATION_ACK=1) when --llm-paraphrase is set.",
    )
    parser.add_argument(
        "--paraphrase-provider",
        choices=("openai", "anthropic", "gemini"),
        default="openai",
        help="Provider for paraphrase mutator.",
    )
    parser.add_argument(
        "--paraphrase-model",
        default=None,
        help="Model id for paraphrase (default: OPENAI_MODEL or gpt-4o-mini for openai).",
    )
    parser.add_argument(
        "--max-llm-parents",
        type=int,
        default=0,
        metavar="N",
        help="Max seed rows to paraphrase (0 = all seeds in current slice).",
    )
    parser.add_argument(
        "--paraphrase-variant",
        default="registry_v1",
        help="mutation.variant id for llm_paraphrase rows.",
    )
    args = parser.parse_args()

    load_dotenv()

    seed_path = args.seed.resolve()
    registry_path = args.registry.resolve()
    ladder_path = args.ladder_map.resolve()

    kinds_raw = [k.strip() for k in str(args.kinds).split(",") if k.strip()]
    kind_set = set(kinds_raw)
    valid = {
        "baseline",
        "role_shift",
        "emotional_escalation",
        "framing_pattern",
        "directness_ladder",
    }
    unknown = kind_set - valid
    if unknown:
        print(f"Unknown kinds: {sorted(unknown)} (allowed: {sorted(valid)})", file=sys.stderr)
        sys.exit(1)

    include_baseline = "baseline" in kind_set and not args.no_baseline
    kinds_for_expand = set(kind_set)
    if args.no_baseline:
        kinds_for_expand.discard("baseline")

    registry = load_registry(registry_path)
    ladder_map = load_ladder_map(ladder_path) if ladder_path.is_file() else {}

    seed_rows = _load_seed(seed_path)
    if args.max_prompts is not None:
        if args.max_prompts < 1:
            print("--max-prompts must be >= 1.", file=sys.stderr)
            sys.exit(1)
        seed_rows = seed_rows[: args.max_prompts]

    expanded = expand_wave(
        seed_rows,
        registry,
        kinds_for_expand,
        ladder_map,
        max_variants_per_kind=args.max_variants,
        include_baseline=include_baseline,
    )

    extra_manifest: dict = {
        "mutation_schema_version": MUTATION_SCHEMA_VERSION,
        "seed_sha256": _sha256_file(seed_path),
        "registry_sha256": _sha256_file(registry_path),
    }
    if ladder_path.is_file():
        extra_manifest["ladder_map_sha256"] = _sha256_file(ladder_path)

    llm_audit: list[dict] = []
    if args.llm_paraphrase:
        ack = args.i_understand_llm_mutation or os.getenv("LLM_MUTATION_ACK", "").strip() == "1"
        block = registry.get("llm_paraphrase") or {}
        if block.get("requires_acknowledgment") and not ack:
            print(
                "LLM paraphrase requires --i-understand-llm-mutation or LLM_MUTATION_ACK=1.",
                file=sys.stderr,
            )
            sys.exit(1)
        prov: ProviderName = args.paraphrase_provider  # type: ignore[assignment]
        if args.paraphrase_model is None:
            if prov == "openai":
                model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            else:
                print("--paraphrase-model is required for non-openai paraphrase provider.", file=sys.stderr)
                sys.exit(1)
        else:
            model = args.paraphrase_model

        require_api_key(prov)

        max_parents = args.max_llm_parents or len(seed_rows)
        para_rows, llm_audit = append_llm_paraphrase_rows(
            seed_rows,
            registry,
            provider=prov,
            model=model,
            max_parents=max_parents,
            variant_id=str(args.paraphrase_variant),
        )
        expanded = _merge_dedupe_text(expanded, para_rows)
        instr = str(block.get("instruction") or "")
        extra_manifest["llm_paraphrase"] = {
            "provider": prov,
            "model": model,
            "max_parents": max_parents,
            "variant": str(args.paraphrase_variant),
            "instruction_sha256": hashlib.sha256(instr.encode("utf-8")).hexdigest(),
            "audit": llm_audit,
        }

    out_path = args.out
    if out_path is None:
        default_out_dir.mkdir(parents=True, exist_ok=True)
        out_path = default_out_dir / f"{args.wave_name}.json"
    else:
        out_path = out_path.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_path = args.manifest_out
    if manifest_path is None:
        manifest_path = out_path.with_suffix(out_path.suffix + ".manifest.json")

    manifest = build_manifest(
        args.wave_name,
        seed_path,
        registry_path,
        ladder_path if ladder_path.is_file() else None,
        expanded,
        kinds_raw,
        extra=extra_manifest,
    )

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(expanded, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {len(expanded)} rows -> {out_path.relative_to(ROOT)}")
    print(f"Manifest -> {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
