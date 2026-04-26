# Lightweight causal proxies (regression)

This note describes **associational** regressions used as **hypothetical “causal language” proxies**—not claims of causal identification. There is no instrumental variable, no randomized assignment, and no fully specified causal graph. Use wording such as “association consistent with a shift in unsafe rate if category were held in a regression sense,” not “pressure causes unsafe outputs.”

## Why cluster bootstrap?

Pooled multimodel rows repeat the **same canonical prompt** across providers/models. Treating rows as i.i.d. would overstate precision. [`scripts/regression_causal_proxies.py`](scripts/regression_causal_proxies.py) resamples **`pressure_join_id`** (canonical `prompts.json` id: `parent_prompt_id` / `parent_id` / `id`) with replacement and aggregates rows within drawn clusters before refitting OLS.

## Models (linear probability / LPM)

| Block | Outcome | Regressors | Interpretation (associational) |
| ----- | ------- | ---------- | ------------------------------ |
| **pressure → unsafe** | `1[label=unsafe]` | intercept, `pressure_composite`, category dummies (`direct` omitted) | Marginal association of heuristic pressure with unsafe probability **conditional on category** in a linear approximation. |
| **category → refusal** | `1[label=safe]` | intercept, category dummies (`direct` omitted) | Differences in estimated P(safe) vs **direct** stratum—proxy for “refusal shift” on an ordinal ladder’s safe end. |
| **tier → sensitivity** | `1[label=unsafe]` | categories, tier dummies (`cheap` omitted), category×tier interactions | Extra unsafe probability vs direct at mid/expensive tiers for non-direct categories (when multiple tiers exist). |
| **per-tier slope** | same | OLS `unsafe ~ category_index` per tier | Descriptive “sensitivity slope” along ordered category index within each tier. |

LPM predictions can fall outside `[0,1]`; coefficients are still useful as **marginal effects in a linear approximation**. For optional **logistic** fits (standard errors, p-values), install `statsmodels` and use `pressure-unsafe --logistic`.

## Pressure join id

Heuristic pressure scores ([`PROMPT_PRESSURE_SCORING.md`](PROMPT_PRESSURE_SCORING.md)) are keyed by canonical prompt **`id`**. Mutation-wave result rows must use **`parent_prompt_id`** (or `parent_id`) so pressure joins correctly; see [`scripts/causal_proxy_data.py`](scripts/causal_proxy_data.py) `pressure_join_id`. [`scripts/correlate_pressure_with_safety.py`](scripts/correlate_pressure_with_safety.py) uses the same join.

## Commands

```bash
cd llm-safety-experiment

# All three blocks (requires prompt_pressure_scores.json)
python scripts/regression_causal_proxies.py all --root results/multimodel --pressure-json results/prompt_pressure_scores.json

# Individual modes
python scripts/regression_causal_proxies.py pressure-unsafe --root results/multimodel/cheap --pressure-json results/prompt_pressure_scores.json
python scripts/regression_causal_proxies.py refusal --root results/multimodel/cheap
python scripts/regression_causal_proxies.py tier --root results/multimodel

# Optional Logit (pip install statsmodels)
python scripts/regression_causal_proxies.py pressure-unsafe --logistic --root results/multimodel --pressure-json results/prompt_pressure_scores.json
```

Default output: [`results/causal_proxy_regressions.json`](results/causal_proxy_regressions.json). Flags: `--bootstrap N`, `--seed`, `--out`.

## Methods blurb (example)

> We report linear probability models as descriptive proxies: (i) unsafe on heuristic prompt-pressure features controlling for elicitation category, (ii) safe-label rates vs a direct baseline across categories, and (iii) tier-by-category interactions when multiple cost tiers are available. Standard errors are not assumed i.i.d.; we use a cluster bootstrap at the canonical prompt id to reflect repeated prompts across models. Estimates are associational and are not interpreted as causal effects of prompts on model internals.
