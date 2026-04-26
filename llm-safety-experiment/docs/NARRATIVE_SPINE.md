# Narrative spine (10-minute read)

For a **single structured overview** (abstract through replication), use [`RESEARCH_MONOGRAPH.md`](RESEARCH_MONOGRAPH.md).

This is the through-line reviewers use to connect artifacts: **what we measured** and **why it matters** for empirical AI safety evaluation.

## 1. Taxonomy (elicitation design)

We fix a **five-stratum prompt bank** (direct, indirect, emotional, escalation, roleplay) with **18 prompts per stratum** (90 total per model run). Stratum is the **experimental factor**; labels (SAFE / PARTIAL / UNSAFE) are human adjudications of assistant text under a published rubric. **CEP (Contextual Evasion Pattern)** names the empirical regularity that risk is **not uniform** across strata—especially concentrated where intent is staged or narratively embedded.

## 2. Multimodel matrix (robustness across APIs)

We replicate the **same** prompt set across **nine tiered API runs**: three cost/capability tiers × three providers (OpenAI, Anthropic, Google Gemini). **Important caveat:** Gemini’s public lineup did not expose a distinct “mid” model at the time of configuration; **mid- and expensive-tier Gemini both use `gemini-2.5-pro`** ([`configs/tier_models.json`](../configs/tier_models.json)). There are still **nine labeled JSON artifacts** (separate runs); **eight unique provider×model-id configurations**.

Primary multimodel displays: **model × category** rate matrices and heatmaps (`figures/multimodel/combined_signature_*.png`), plus a **3×3 panel** view (`combined_9panel_unsafe_by_category.png`).

## 3. Robustness beyond the base prompts (mutations / boundary)

**Prompt mutations** and **boundary stability** scripts probe whether category-level structure survives paraphrase-style stress and adjacent prompt families (see [`PROMPT_MUTATIONS.md`](../PROMPT_MUTATIONS.md), [`BOUNDARY_STABILITY.md`](../BOUNDARY_STABILITY.md)). These are **stress tests**, not causal identification of internal mechanisms.

## 4. Proxies (pressure / regression)

**Causal proxies** here are **associational summaries** linking auxiliary constructs (e.g., response-pressure features) to safety outcomes—useful for monitoring hypotheses, **not** causal claims about model internals (see [`CAUSAL_PROXIES.md`](../CAUSAL_PROXIES.md)).

## 5. Interpretability figures

Per-model **fingerprints**, **PCA** of fingerprint features, and **safety frontiers** (refusal vs risk) visualize cross-model geometry in the same label space (see [`INTERPRETABILITY_VIZ.md`](../INTERPRETABILITY_VIZ.md), [`MODEL_FINGERPRINTS.md`](../MODEL_FINGERPRINTS.md)).

## 6. Artifact chain

Pilot: `results/pilot/results.json` ↔ `significance_stats.json` via `scripts/verify_artifact_chain.py`. Multimodel: integrity scan via `scripts/audit_multimodel_artifacts.py`. One-command refresh: `python scripts/reproduce_main_figures.py` (see [`ARTIFACT_INTEGRITY.md`](ARTIFACT_INTEGRITY.md)).
