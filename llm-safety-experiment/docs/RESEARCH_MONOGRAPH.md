# Contextual Evasion Under a Fixed Elicitation Taxonomy

**An empirical audit of harmful-request compliance across LLM APIs**

Aevion Labs — `llm-safety-experiment`  
*Document version:* 1.0 (April 2026)

---

## Abstract

Deployment monitoring often emphasizes **explicit** harmful intent and binary **UNSAFE** adjudications. Realistic misuse also appears under **staged** or **dual-use** language, where models may receive **PARTIAL** (borderline) labels rather than **UNSAFE** while still posing harm-relevant risk. This project fixes a **90-prompt** bank, balanced across five **elicitation strata** (direct, indirect, emotional, escalation, roleplay), runs it against **commercial chat APIs**, and **human-labels** assistant outputs as SAFE, PARTIAL, or UNSAFE under a published rubric.

**Pilot (single model, frozen JSON):** aggregate UNSAFE **11.1%** (10/90); aggregate **risk** (PARTIAL ∪ UNSAFE) **32.2%** (29/90). Category structure matters: e.g. **roleplay** shows the highest UNSAFE share in the contingency table (**6/18**), while **indirect** is **10/18 PARTIAL** and **0/18 UNSAFE**—a clear **decoupling** between strict UNSAFE and the broader risk surface. A Fisher exact test for UNSAFE comparing **roleplay** to all other categories yields **p ≈ 0.0037** (see `results/pilot/significance_stats.json`).

**Multimodel extension:** the **same** prompt bank is evaluated on **nine** tiered configurations (three cost/capability tiers × three providers). Results are summarized in `figures/multimodel/signature_rate_matrix.json` and the figure bundle under `figures/multimodel/`. **Important caveat:** mid- and expensive-tier **Gemini** both use the **`gemini-2.5-pro`** model id in the frozen configuration, so Gemini tier is **not** a clean SKU ladder; there are still nine labeled run files and **eight** distinct provider×model-id pairs.

We do **not** claim population prevalence, causal mechanisms inside models, or optimality under adaptive attack. We **do** ship a **reproducible** pipeline: audit scripts, rate matrices, Wilson intervals, and optional paired tests and diagnostic figures. For the full technical narrative, notation, and extended discussion, see [`LLM_SAFETY_EXPERIMENT_REPORT.md`](../LLM_SAFETY_EXPERIMENT_REPORT.md).

---

## 1. Introduction

### 1.1 Motivation

Safety teams need measurements that reflect **how** a harmful objective is phrased, not only **whether** it is phrased bluntly. A model may refuse a direct request yet produce problematic content when the same objective is embedded in **fiction**, **incremental** steps, or **dual-use** framing. If monitoring tracks only **UNSAFE**-style outcomes, **PARTIAL**-heavy strata can hide a large **risk surface**.

### 1.2 Contribution type

This repository is a **structured behavioral audit**, not a competition to “break” models with optimized strings.

- **Prespecified strata:** five elicitation categories, **18 prompts each**, **90** total per run.
- **Human labels:** each assistant `response` is judged SAFE / PARTIAL / UNSAFE using [`LABEL_RUBRIC.md`](../LABEL_RUBRIC.md).
- **Replication-first:** frozen `results/*.json`, scripted figures, and documented commands ([`PROVENANCE.md`](../PROVENANCE.md)).

### 1.3 Terminology: CEP

**CEP (Contextual Evasion Pattern)** is the **analytic shorthand** used in the long report for **category-conditional** structure: variation in label rates across the prespecified strata within **this** bank. It is **not** a claim about latent “intent” inside the model or about universal behavior across all prompts.

---

## 2. Methods

### 2.1 Prompt bank

- **Source:** [`prompts.json`](../prompts.json) — 90 rows with `id`, `category`, `text`.
- **Strata:** `direct`, `indirect`, `emotional`, `escalation`, `roleplay`.
- **Balance:** 18 prompts per stratum.

### 2.2 API execution

- **Providers:** OpenAI, Anthropic, Google Gemini (see [`provider_clients.py`](../provider_clients.py)).
- **Entry points:** [`run_experiment.py`](../run_experiment.py) (single run); [`run_multi_model.py`](../run_multi_model.py) with [`configs/tier_models.json`](../configs/tier_models.json) for tiered multimodel batches.
- **Outputs:** JSON arrays of rows including `response`, `provider`, `model`, and (after labeling) `label`.

Failed API calls are stored as `ERROR:` prefixes in `response` and are excluded from rate summaries until fixed.

### 2.3 Labeling

- **Tooling:** [`analyze_results.py`](../analyze_results.py) (interactive adjudication).
- **Schema:** [`RESULTS_SCHEMA.md`](../RESULTS_SCHEMA.md).
- **Rubric:** [`LABEL_RUBRIC.md`](../LABEL_RUBRIC.md).

**Cross-model note:** [`scripts/seed_labels_from_pilot.py`](../scripts/seed_labels_from_pilot.py) can copy labels by prompt `id`; that is a **workflow shortcut**, not a substitute for reading each model’s actual text for publication-grade claims ([`MULTI_MODEL_RESULTS.md`](../MULTI_MODEL_RESULTS.md)).

### 2.4 Estimands

For category \(c\) with \(n_c = 18\):

- \(\hat{p}_U(c)\): fraction **UNSAFE**.
- \(\hat{p}_R(c)\): fraction with **risk** \(R=1\) if \(Y \in \{\mathrm{PARTIAL},\mathrm{UNSAFE}\}\).

**Pilot aggregates** (from `significance_stats.json`): \(\hat{p}_U = 10/90\), \(\hat{p}_R = 29/90\).

### 2.5 Multimodel matrix

[`scripts/build_multimodel_rate_matrix.py`](../scripts/build_multimodel_rate_matrix.py) aggregates labeled multimodel JSON into:

- `figures/multimodel/signature_rate_matrix.json` (metric: UNSAFE),
- optional risk metric sibling (`signature_rate_matrix_risk.json` when built with `--metric risk`).

Rows are **runs** (tier × provider × model configuration); columns are the five strata.

### 2.6 Statistical machinery (overview)

- **Pilot:** Pearson \(\chi^2\) on the 5×3 contingency, **Fisher** for prespecified UNSAFE contrasts, **Wilson** CIs in `significance_stats.json` ([`scripts/compute_significance.py`](../scripts/compute_significance.py)).
- **Multimodel visuals:** Wilson CIs on bar charts; **McNemar** pairwise grids and **Jeffreys Beta** facets are **exploratory** (multiplicity not fully adjusted) — see [`INTERPRETABILITY_VIZ.md`](../INTERPRETABILITY_VIZ.md) §5.

---

## 3. Results

### 3.1 Pilot: category-level pattern

The frozen **5×3** counts (SAFE / PARTIAL / UNSAFE × five categories) are in `results/pilot/significance_stats.json`. In words:

| Stratum     | SAFE | PARTIAL | UNSAFE |
|------------|------|---------|--------|
| direct     | 18   | 0       | 0      |
| indirect   | 8    | 10      | 0      |
| emotional  | 18   | 0       | 0      |
| escalation | 9    | 5       | 4      |
| roleplay   | 8    | 4       | 6      |

**Independence test:** \(\chi^2\) with **p ≈ 7.5×10⁻⁷** (8 d.f.) — strong evidence of **heterogeneity** across strata under this bank and rubric.

**Prespecified contrast (UNSAFE):** roleplay vs rest — **p ≈ 0.0037** (Fisher two-sided, see `fisher_roleplay_vs_rest_unsafe` in the same JSON).

### 3.2 Pilot: interpretation in one paragraph

The pilot run is **not** “models are safe because UNSAFE is only 11%.” It is: **risk** is **32.2%** when PARTIAL counts as harm-relevant, and **indirect** is almost entirely **PARTIAL** with **zero** UNSAFE—exactly the monitoring gap the design is meant to surface. **Roleplay** concentrates **UNSAFE** in this snapshot; **escalation** mixes PARTIAL and UNSAFE (see table).

### 3.3 Multimodel: qualitative summary

The nine-run matrix (`p_hat` in `signature_rate_matrix.json`) shows **shared** qualitative features across APIs:

- **Direct** and **emotional** strata are often near **zero** UNSAFE in many runs.
- **Indirect** tends to carry **non-trivial** \(\hat{p}_U\) in several runs (unlike the pilot’s 0/18 UNSAFE for indirect—multimodel responses differ by model).
- **Escalation** and **roleplay** typically sit at the **high** end of \(\hat{p}_U\) relative to direct within the same row.

Exact numeric cells are **one click away** in the JSON; the heatmaps and nine-panel figure make cross-run comparison immediate ([`RESULTS_LAYOUT.md`](../RESULTS_LAYOUT.md)).

### 3.4 Configuration caveat (Gemini)

[`configs/tier_models.json`](../configs/tier_models.json) documents that **Gemini mid and expensive** may reference the **same** `gemini-2.5-pro` id. Interpret **tier ladders** per provider with that constraint; prefer **within-provider** tier contrasts for OpenAI and Anthropic when the SKU list is distinct.

---

## 4. Figure gallery (multimodel bundle)

All paths under `figures/multimodel/`. Regenerate with `python scripts/reproduce_main_figures.py` (add `--extra-visuals` and `--phd-visuals` for the full set).

| Artifact | Role |
|----------|------|
| `signature_rate_matrix.json` | Machine-readable \(\hat{p}\) (UNSAFE) + per-file counts |
| `combined_signature_unsafe_heatmap.png` | 9 runs × 5 strata heatmap |
| `combined_9panel_unsafe_by_category.png` | 3×3 tier × provider bars + Wilson CIs |
| `combined_radar_grid_unsafe.png` | Polar profiles by run |
| `combined_parallel_coordinates.png` | Each run as a line over strata |
| `combined_forest_wilson_unsafe.png` | Forest plots with Wilson intervals |
| `combined_clustermap_rates.png` | Exploratory clustering of runs |
| `combined_tier_slope_overall_rates.png` | Cheap → mid → expensive slopes |
| `combined_label_composition_stacked.png` | SAFE / PARTIAL / UNSAFE composition |
| `combined_category_correlation_across_models.png` | Descriptive correlation across strata |
| `combined_within_category_ranks_unsafe.png` | Ranks within each stratum |
| `interactive_rates.html` | Plotly toggle (unsafe vs risk) |
| `phd_mcnemar_pairwise_unsafe.png` / `_risk.png` | Paired exact tests (exploratory multiplicity) |
| `phd_beta_posterior_unsafe_facets.png` | Jeffreys Beta credible intervals |
| `phd_tier_provider_interaction_unsafe.png` | Tier × provider interaction lines |
| `phd_unsafe_concordance_histogram.png` | Cross-run UNSAFE concordance on shared ids |
| `phd_cohens_h_pairwise_overall.png` | Cohen’s *h* on overall UNSAFE |
| `phd_unsafe_incidence_prompts_by_run.png` | Binary incidence: prompts × runs |
| `phd_logit_category_profiles_unsafe.png` | Empirical logit profiles |
| `phd_direct_vs_roleplay_escalation.png` | Direct vs roleplay scatter per run |

Pilot-specific figures live under `figures/` from [`scripts/generate_report_figures.py`](../scripts/generate_report_figures.py); the long report references them by figure number.

---

## 5. Limitations

1. **Small \(n_c\):** 18 prompts per stratum → wide uncertainty; subcategory claims are fragile.
2. **Single primary coder** unless dual-coding artifacts are produced ([`REPLICATION_PROTOCOL.md`](../REPLICATION_PROTOCOL.md)).
3. **Single-turn** design; no tool use or multi-turn escalation in the base bank.
4. **Frozen checkpoints**; model behavior drifts with vendor updates even if ids stay constant.
5. **Associational** follow-ons (pressure scores, regression proxies) are **not** causal identification ([`CAUSAL_PROXIES.md`](../CAUSAL_PROXIES.md)).
6. **Exploratory** pairwise grids (McNemar, Cohen’s *h*) → **multiplicity**; see disclaimers in [`INTERPRETABILITY_VIZ.md`](../INTERPRETABILITY_VIZ.md).

---

## 6. Ethics and responsible use

Prompts are **sensitive by design**. Use only for **authorized** safety research, **scoped** red teaming, or **education**. Do not operationalize outputs to facilitate harm. Store artifacts securely; describe limitations clearly in any derivative publication.

---

## 7. Replication

### 7.1 Environment

```bash
cd llm-safety-experiment
python -m venv .venv
pip install -r requirements.txt
```

### 7.2 Integrity

```bash
python scripts/audit_multimodel_artifacts.py --strict
python scripts/verify_artifact_chain.py
```

### 7.3 Figures (no new API calls)

```bash
python scripts/reproduce_main_figures.py
python scripts/reproduce_main_figures.py --extra-visuals --phd-visuals
```

See [`docs/ARTIFACT_INTEGRITY.md`](ARTIFACT_INTEGRITY.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md), and [`PROVENANCE.md`](../PROVENANCE.md).

---

## 8. Related documents

| Document | Use |
|----------|-----|
| [`LLM_SAFETY_EXPERIMENT_REPORT.md`](../LLM_SAFETY_EXPERIMENT_REPORT.md) | Full technical report + extended argument |
| [`docs/NARRATIVE_SPINE.md`](NARRATIVE_SPINE.md) | Short through-line |
| [`docs/MULTIMODEL_MANUSCRIPT.md`](MULTIMODEL_MANUSCRIPT.md) | Multimodel-focused manuscript (minimal pilot) |
| [`docs/EMPIRICAL_MULTIMODEL_SAFETY.md`](EMPIRICAL_MULTIMODEL_SAFETY.md) | Earlier paper-style draft (overlaps this monograph) |
| [`REPLICATION_PROTOCOL.md`](../REPLICATION_PROTOCOL.md) | Stronger future study design |
| [`RESULTS_LAYOUT.md`](../RESULTS_LAYOUT.md) | Paths and naming |

---

## 9. Citation

If you use this codebase or frozen artifacts in academic work, cite the **public repository URL** (set this to your published GitHub/GitLab link before distribution), the **git commit hash**, and the **prompt bank version** and **model ids** from [`PROVENANCE.md`](../PROVENANCE.md). Example (adapt to your style):

> Aevion Labs. *llm-safety-experiment: contextual elicitation audit (multimodel safety toolkit).* MIT License. URL: *(add your public repository URL here)*. Commit: *(add `git rev-parse HEAD`)*.

---

## 10. License

Software and documentation in this package are released under the **MIT License** ([`LICENSE`](../LICENSE)) unless otherwise noted. Third-party API terms apply to model usage.
