# Prompt mutations (controlled adaptive evaluation)

This layer turns the **canonical** prompt bank ([`prompts.json`](prompts.json)) into **derived waves**: expanded prompt rows with explicit lineage, plus a **manifest** (hashes, counts, optional LLM paraphrase audit). It supports **surface-form variation under audit**, not open-ended attack optimization.

## Ethics and scope

- The fixed bank remains the **seed**; harmful or sensitive intents already exist in the corpus. Mutations **reframe** wording or pressure (role, emotion, directness, closed “policy test” framings) so you can study **robustness of model behavior** to controlled surface changes.
- This is **not** gradient descent, success feedback, or automated search toward higher harm. Do not use manifests or scripts to iteratively “improve” jailbreak success rates.
- **Phase B** (`llm_paraphrase`) calls an external model to rephrase prompts. It is **gated** (`--i-understand-llm-mutation` or `LLM_MUTATION_ACK=1`) and logs parse failures in the manifest. Treat outputs as **audit artifacts**; human review and institutional policies (e.g. IRB) still apply.

## Artifacts

| Artifact | Role |
| -------- | ---- |
| [`configs/mutation_registry.json`](configs/mutation_registry.json) | Closed list of allowed variants (role shift, emotional escalation, framing patterns, directness ladder suffixes, frozen LLM paraphrase instruction). |
| [`configs/indirect_direct_ladder_map.json`](configs/indirect_direct_ladder_map.json) | Pre-reviewed mapping from indirect `parent_id` → ladder template ids (optional subset). |
| `prompts_waves/<name>.json` | Array of wave rows: `id`, `parent_id`, `category`, `text`, `mutation` (`kind`, `variant`, `rung`, `schema_version`, …). |
| `prompts_waves/<name>.json.manifest.json` | Counts by kind, per-row `content_sha256`, file hashes, optional `llm_paraphrase` audit block. |

## Commands

**Expand a wave (Phase A, rule-based only):**

```bash
cd llm-safety-experiment
python scripts/expand_prompt_wave.py --wave-name cep_2026_04 \
  --kinds baseline,role_shift,emotional_escalation,framing_pattern,directness_ladder \
  --out prompts_waves/cep_2026_04.json \
  --manifest-out prompts_waves/cep_2026_04.manifest.json
```

**Run experiments on the wave:**

```bash
python run_experiment.py --prompts prompts_waves/cep_2026_04.json --mutation-wave cep_2026_04
python run_multi_model.py --prompts prompts_waves/cep_2026_04.json --mutation-wave cep_2026_04 openai:gpt-4o-mini
```

**Optional Phase B — LLM paraphrase** (adds rows; requires API keys and acknowledgment):

```bash
python scripts/expand_prompt_wave.py --wave-name cep_2026_04_llm --max-prompts 20 \
  --kinds baseline \
  --llm-paraphrase --i-understand-llm-mutation \
  --paraphrase-provider openai --paraphrase-model gpt-4o-mini --max-llm-parents 20
```

**Summarize labeled wave results:**

```bash
python scripts/summarize_mutation_wave.py --results path/to/labeled.json
```

**Boundary stability (ordinal label dispersion):** after labeling, use [`scripts/compute_boundary_stability.py`](scripts/compute_boundary_stability.py) — `cross-model` for variance across models on the same `(parent, kind, variant)` cell, and `cross-variant` for variance across mutation variants for the same parent and model. Definitions: [`BOUNDARY_STABILITY.md`](BOUNDARY_STABILITY.md).

## Pre-registration checklist

1. List **which** `kinds` and registry **variant ids** you will use (cite `mutation_registry.json` version or commit hash).
2. State whether **directness_ladder** uses the default map or a **custom** `indirect_direct_ladder_map.json` (peer-reviewed subset only).
3. If using **LLM paraphrase**, record `instruction_sha256`, provider, model, and `max-llm-parents` from the manifest.
4. Record **`--mutation-wave`** string in provenance so result rows link to the wave name.

## Linkage to the main report

Controlled surface mutations complement the **fixed taxonomy** and categorical analysis in [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md): same seed intents, additional **provenance columns** on each result row (see [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md)).
