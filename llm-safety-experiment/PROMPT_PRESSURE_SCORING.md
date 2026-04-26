# Prompt adversarial pressure (heuristic, Tier 3)

**Research-only:** deterministic features on **prompt** text (`prompts.json`). They are **not** validated constructs of “adversarial pressure”; use for exploratory correlation with human labels, not for optimizing harmful prompts.

## Dimensions (schema v1)

Each prompt receives scores in \([0,1]\) from lexicon and regex rules in [`scripts/score_prompt_pressure.py`](scripts/score_prompt_pressure.py):

| Feature | Intent | Method (v1) |
| ------- | ------ | ----------- |
| `emotional_intensity` | Affective / pleading tone | Keywords (e.g. *desperate*, *terrified*, *please*, *beg*); exclamation count capped. |
| `authority_framing` | Institutional / role legitimacy | Keywords (*doctor*, *officer*, *law*, *policy*, *official*, *regulation*, …). |
| `urgency` | Time pressure | Keywords (*asap*, *immediately*, *right now*, *urgent*, *hurry*, *deadline*). |
| `coercion` | Threat / obligation | Keywords (*or else*, *you must*, *i will report*, *consequences*, *forced to*). |

`pressure_composite` is the mean of the four scores (equal weight for auditability).

## Artifact

- `prompt_pressure_scores.json` — one object per prompt `id` plus `schema_version` and generation metadata.

## Phase 2 (extension)

LLM or human rubric scores can replace or augment these features; version the schema and keep prompts frozen for comparability.

## Correlation

Run [`scripts/correlate_pressure_with_safety.py`](scripts/correlate_pressure_with_safety.py) after labeling. Joins on canonical prompt id via `parent_prompt_id` / `parent_id` / `id` (same as [`scripts/causal_proxy_data.py`](scripts/causal_proxy_data.py)). Treat multiple correlations as **descriptive**; adjust for multiplicity if you report many tests (Bonferroni / FDR noted in script output).

For **linear probability models** (pressure → unsafe controlling for category, category → refusal, tier interactions) with **cluster bootstrap** at the prompt id, see [`CAUSAL_PROXIES.md`](CAUSAL_PROXIES.md) and [`scripts/regression_causal_proxies.py`](scripts/regression_causal_proxies.py).
