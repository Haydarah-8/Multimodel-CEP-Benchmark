# Boundary stability under perturbation

This document defines two **descriptive** metrics for how **stable ordinal safety labels** are when you either change the **model** (holding the evaluated surface fixed) or change the **prompt surface** (holding the seed intent and model fixed). They use the same coding as the decision-boundary audit: `safe` → 0, `partial` → 1, `unsafe` → 2.

This is **not** adaptive attack optimization: variants come from a **closed, pre-registered** mutation registry ([`PROMPT_MUTATIONS.md`](PROMPT_MUTATIONS.md)). There are no logits or continuous harm scores.

## Intent cluster (operational)

In v1, an **intent cluster** is the lineage of a row in the canonical bank: **`parent_prompt_id`** when present (mutation waves), otherwise the result row **`id`** (canonical `prompts.json` runs). We do **not** use embedding clusters here.

## Metric 1: Cross-model boundary dispersion

**Question:** For the same evaluation cell, how much do labels disagree across models?

**Alignment key (`align_key`):**

- If `parent_prompt_id`, `mutation_kind`, and `mutation_variant` are all present:  
  `(parent_prompt_id, mutation_kind, mutation_variant)` — same **surface framing** across providers/models.
- Otherwise: `(id,)` — same as the original decision-boundary audit on canonical banks.

**Per–align_key summaries** (only rows where **every** model stem has a label): population **variance** and **range** of ordinal scores, **majority label**, **Fleiss’ κ**, pairwise directed label counts, marginal shifts — see [`DECISION_BOUNDARY_AUDIT.md`](DECISION_BOUNDARY_AUDIT.md) for interpretation.

**Script:** [`scripts/compute_boundary_stability.py`](scripts/compute_boundary_stability.py) `cross-model`

## Metric 2: Cross-variant boundary dispersion

**Question:** For the same **parent intent** and **same model**, how much do labels change across **mutation variants**?

**Grouping:** `(parent_prompt_id or id, provider, model)`  
**Variants:** distinct `(mutation_kind, mutation_variant)`; if mutation metadata is missing, each row’s `id` is its own variant (usually one row per group for canonical files).

**Eligibility:** Groups need at least **two** labeled variants. Summary output includes mean/median variance, fraction with `range >= 1`, and fraction with polar disagreement (`range == 2`).

**Script:** `cross-variant` (one or more labeled results JSON paths; optional `--mutation-wave` filter).

## Commands

```bash
cd llm-safety-experiment

# Canonical or wave: cross-model (wave-aware align_key when provenance columns exist)
python scripts/compute_boundary_stability.py cross-model --multimodel-root results/multimodel/cheap
python scripts/compute_boundary_stability.py cross-model --multimodel-root results/multimodel/cheap --mutation-wave my_wave

# Labeled wave file(s): dispersion across variants within each parent × model
python scripts/compute_boundary_stability.py cross-variant --results path/to/labeled.json --mutation-wave my_wave --full
```

Default JSON outputs: `results/multimodel/boundary_stability_cross_model.json` and `boundary_stability_cross_variant.json`. Use `--full` for cross-model to also write `*_full.json` with `per_prompt_complete`.

## Methods blurb (example)

> We operationalized boundary stability under controlled surface perturbations using ordinal human labels (safe / partial / unsafe). Cross-model dispersion was computed on aligned evaluation cells: for mutation waves, cells were defined by the seed id plus mutation kind and variant; for the canonical bank, by prompt id. Cross-variant dispersion, for each seed id and model, summarized the spread of labels across pre-registered surface mutations. We report descriptive variance, range, and agreement summaries; we do not optimize prompts toward higher harm.

## Relation to existing audit

[`scripts/decision_boundary_audit.py`](scripts/decision_boundary_audit.py) remains the **id-keyed** cross-model audit for legacy parity. [`compute_boundary_stability.py`](scripts/compute_boundary_stability.py) generalizes alignment for **wave** results and adds **cross-variant** stability.
