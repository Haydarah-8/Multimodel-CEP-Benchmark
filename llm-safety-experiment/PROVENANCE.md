# Provenance and reproducibility

Claims in [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md) and the portfolio-oriented summary [`docs/RESEARCH_MONOGRAPH.md`](docs/RESEARCH_MONOGRAPH.md) are conditional on the **artifact chain** below. Update this file when you change model, prompts, or labels.

## Canonical data

| Artifact | Role |
| -------- | ---- |
| [`prompts.json`](prompts.json) | Fixed prompt bank (90 rows: `id`, `category`, `text`) |
| `prompts_waves/*.json` | Derived prompt banks from [`scripts/expand_prompt_wave.py`](scripts/expand_prompt_wave.py); each row adds `parent_id`, `mutation`, and stable wave `id` (see [`PROMPT_MUTATIONS.md`](PROMPT_MUTATIONS.md)) |
| `prompts_waves/*.json.manifest.json` | Wave manifest: content hashes, counts, optional LLM paraphrase audit |
| [`results/pilot/results.json`](results/pilot/results.json) | Default single-model pilot: outputs + human `label` per row (formerly `results.json` at repo root) |
| `results/multimodel/<tier>/results_<provider>_<slug>.json` | Tiered multi-model runs (cheap / mid / expensive); see [`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md) and [`configs/tier_models.json`](configs/tier_models.json) |
| `results/archive/legacy_flat/` | Superseded flat-root JSON retained for audit |
| [`results/pilot/significance_stats.json`](results/pilot/significance_stats.json) | Default output of [`scripts/compute_significance.py`](scripts/compute_significance.py) for the pilot |
| `significance_stats_<stem>.json` | Next to each non-pilot `results_*.json` (stem-based default naming; see script `--out`) |

Row schema (including optional `model`, dual-coding fields): [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md).

## Model and API

| Field | Value |
| ----- | ----- |
| Default provider | `openai` ([`run_experiment.py`](run_experiment.py) `--provider`) |
| Default model | `gpt-4o-mini` (`MODEL` in [`run_experiment.py`](run_experiment.py)) |
| Override (OpenAI) | Set `OPENAI_MODEL` in `.env` or environment (see README) |
| OpenAI | Chat Completions via [`provider_clients.py`](provider_clients.py) → `chat.completions.create` |
| Anthropic | Messages API via [`provider_clients.py`](provider_clients.py); env **`ANTHROPIC_API_KEY`** |
| Gemini | `google-generativeai` via [`provider_clients.py`](provider_clients.py); env **`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`** |
| Generation | Single-turn user message; `max_tokens` / `max_output_tokens` capped at **200** for comparability |

**Multi-model / multi-provider (same prompts):**

| Command | Notes |
| ------- | ----- |
| `python run_multi_model.py gpt-4o-mini gpt-4o` | OpenAI-only, backward compatible → `results_openai_*.json` |
| `python run_multi_model.py openai:gpt-4o-mini anthropic:claude-3-5-haiku-20241022 gemini:gemini-2.0-flash` | One file per pair (`results_openai_*.json`, etc.) |
| `MULTI_MODELS=openai:gpt-4o-mini,gemini:gemini-2.0-flash python run_multi_model.py` | Same, via environment |
| `python scripts/expand_prompt_wave.py --wave-name <name> ...` then `python run_experiment.py --prompts prompts_waves/<name>.json --mutation-wave <name>` | Controlled surface mutations; provenance columns per [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md) |

Then label each file: `python analyze_results.py --results results_<provider>_<slug>.json`.

**Recommended:** When you freeze a run for publication or a job portfolio, record **date of API calls** and **exact model string** used (including override) in a git commit message or here.

**Pinned dependencies:** For a reproducible environment matching a public release, install with `pip install -r requirements.lock.txt` after cloning, then record the **git commit hash** (and Python version) alongside any cited numbers. Regenerate the lockfile with `pip freeze > requirements.lock.txt` when you intentionally upgrade tooling.

**Last consistency check (artifact chain):** After any change to `results/pilot/results.json`, run `python scripts/compute_significance.py` then `python scripts/verify_artifact_chain.py` so `results/pilot/significance_stats.json` and §3.6 of the report stay aligned.

## Analysis scripts

| Script | Command | Output |
| ------ | ------- | ------ |
| Significance | `python scripts/compute_significance.py` | `significance_stats.json` + console |
| Significance (multi-model file) | `python scripts/compute_significance.py --results results_openai_gpt-4o-mini.json` | `significance_stats_results_openai_gpt-4o-mini.json` (default naming) + console |
| Verify chain | `python scripts/verify_artifact_chain.py` | Exit 0 if `results.json` contingency matches `significance_stats.json` |
| Multimodel audit | `python scripts/audit_multimodel_artifacts.py` | Console: `ERROR:` rows, labels, row counts; `--strict` fails CI |
| Reproduce (pilot + multimodel) | `python scripts/reproduce_main_figures.py` | [`figures/multimodel/combined_*.png`](RESULTS_LAYOUT.md), pilot `figures/*.png`, fingerprints; optional `--skip-pilot` / `--skip-fingerprints` / **`--extra-visuals`** / **`--phd-visuals`** |
| Figures (optional) | `python scripts/generate_report_figures.py --results results.json` | `figures/*.png` (overwrites; use separate runs or copy `figures/` if comparing models) |
| Multi-model summary | `python scripts/summarize_multi_model.py` | Console: aggregate % UNSAFE / % risk per file |
| IRR subset export | `python scripts/export_irr_subset.py` (`--include-all-partial` optional) | `irr_subset_for_rater2.json` (dual-coding workload; see `REPLICATION_PROTOCOL.md`) |
| IRR κ (single file) | `python scripts/compute_irr_kappa.py --results <merged.json> --by-category` | Cohen’s κ overall + per category (console) |
| IRR multimodel report | `python scripts/irr_multimodel_report.py` | [`results/multimodel/irr_multimodel_report.json`](results/multimodel/irr_multimodel_report.json) (per model / tier / category; optional `--bootstrap`; see [`IRR_ENGINE.md`](IRR_ENGINE.md)) |
| IRR disagreement figures | `python scripts/plot_irr_disagreement_heatmaps.py --report-json results/multimodel/irr_multimodel_report.json` | `figures/multimodel/irr_disagreement_panels.png` |
| Model proxy labels (exploratory) | `python scripts/model_proxy_irr_label.py --results <path> --dry-run` or with API | `*.with_model_proxy.json`; analyze with `irr_multimodel_report.py --compare-field label_model_proxy` |
| Paired multimodel labels | `python scripts/export_paired_error_table.py` | Wide CSV under `results/multimodel/` (cross-model comparison) |
| Harm robustness | `python scripts/compare_harm_operationalizations.py` | Strict vs risk vs expanded scalars (`ROBUSTNESS_HARM_OPERATIONALIZATIONS.md`) |
| Tier paired (McNemar) | `python scripts/compare_tier_paired.py --a <cheap.json> --b <exp.json>` | Discordant counts, paired OR, exact p for UNSAFE and risk |
| Tier summary grid | `python scripts/summarize_tier_or.py` | All provider × tier contrasts under `results/multimodel/` (skips duplicate Gemini paths) |
| Mutation wave summary | `python scripts/summarize_mutation_wave.py --results <path>` | Console table: `mutation_kind` × `category` label rates |
| Boundary stability (cross-model) | `python scripts/compute_boundary_stability.py cross-model --multimodel-root <tier_dir>` | `boundary_stability_cross_model.json` (optional `--mutation-wave`; see [`BOUNDARY_STABILITY.md`](BOUNDARY_STABILITY.md)) |
| Boundary stability (cross-variant) | `python scripts/compute_boundary_stability.py cross-variant --results <labeled.json>` | `boundary_stability_cross_variant.json` (`--full` for per-parent rows) |
| Category stress indices | `python scripts/compute_category_stress_indices.py --results <path>` | `category_stress_indices.json` (RR vs direct, CPI, roleplay amplification) |
| Stress figure | `python scripts/plot_category_stress.py --indices-json <path>` | `fig_category_stress_RR_unsafe.png` |
| Model fingerprints (Tier 2) | `python scripts/compute_model_fingerprints.py --results <path>` | `model_fingerprint.json` (curves + ASS + ESI; see [`MODEL_FINGERPRINTS.md`](MODEL_FINGERPRINTS.md)) |
| Fingerprint figure | `python scripts/plot_model_fingerprints.py --fingerprint-json <path>` | `fig_model_fingerprint_curves.png` |
| Fingerprint batch | `python scripts/fingerprint_all_multimodel.py` | Under each `results_*.json` dir: `figures/<stem>/model_fingerprint.json` + PNG |
| Decision-boundary audit | `python scripts/decision_boundary_audit.py` | `boundary_audit.json` + `boundary_audit_full.json` (see [`DECISION_BOUNDARY_AUDIT.md`](DECISION_BOUNDARY_AUDIT.md)) |
| Multimodel signature matrix (Tier 3) | `python scripts/build_multimodel_rate_matrix.py` | [`figures/multimodel/signature_rate_matrix.json`](figures/multimodel/signature_rate_matrix.json) + optional `normalization_layer.json` via `--out-normalization` |
| Signature heatmap (Tier 3) | `python scripts/plot_multimodel_signature_heatmap.py --matrix-json figures/multimodel/signature_rate_matrix.json` | Default or `combined_signature_unsafe_heatmap.png` / `combined_signature_excess_vs_direct.png` via `--out` (see [`CROSS_MODEL_NORMALIZATION.md`](CROSS_MODEL_NORMALIZATION.md)) |
| Nine-panel (3×3 tier × provider) | `python scripts/plot_multimodel_nine_panel.py` | `figures/multimodel/combined_9panel_unsafe_by_category.png` (Wilson CIs; `--no-ci` optional) |
| Radar grid (polar 3×3) | `python scripts/plot_multimodel_radar_grid.py --matrix-json …` | `figures/multimodel/combined_radar_grid_unsafe.png` |
| Within-category ranks | `python scripts/plot_multimodel_within_category_ranks.py --matrix-json …` | `combined_within_category_ranks_unsafe.png` |
| McNemar pairwise | `python scripts/plot_multimodel_mcnemar_pairwise.py --root results/multimodel` | `phd_mcnemar_pairwise_unsafe.png` / `_risk.png` |
| Beta posterior facets | `python scripts/plot_multimodel_beta_posterior_facets.py --matrix-json …` | `phd_beta_posterior_unsafe_facets.png` |
| Tier×provider interaction | `python scripts/plot_multimodel_interaction_tier_provider.py --matrix-json …` | `phd_tier_provider_interaction_unsafe.png` |
| UNSAFE concordance histogram | `python scripts/plot_multimodel_unsafe_concordance.py --root results/multimodel` | `phd_unsafe_concordance_histogram.png` |
| Cohen’s *h* pairwise (overall) | `python scripts/plot_multimodel_cohens_h_pairwise.py --root results/multimodel` | `phd_cohens_h_pairwise_overall.png` |
| UNSAFE incidence heatmap | `python scripts/plot_multimodel_unsafe_incidence_heatmap.py --root results/multimodel` | `phd_unsafe_incidence_prompts_by_run.png` |
| Logit category profiles | `python scripts/plot_multimodel_logit_category_profile.py --matrix-json …` | `phd_logit_category_profiles_unsafe.png` |
| Direct vs roleplay escalation | `python scripts/plot_multimodel_direct_vs_roleplay_escalation.py --matrix-json …` | `phd_direct_vs_roleplay_escalation.png` |
| Parallel coordinates | `python scripts/plot_multimodel_parallel_coordinates.py --matrix-json …` | `figures/multimodel/combined_parallel_coordinates.png` ([`INTERPRETABILITY_VIZ.md`](INTERPRETABILITY_VIZ.md) §4) |
| Forest plot (Wilson CI) | `python scripts/plot_multimodel_forest_wilson.py --matrix-json …` | `combined_forest_wilson_unsafe.png` / `_risk.png` |
| Clustermap | `python scripts/plot_multimodel_clustermap.py --matrix-json …` | `combined_clustermap_rates.png` |
| Tier slope (overall rates) | `python scripts/plot_tier_slope_chart.py --matrix-json …` | `combined_tier_slope_overall_rates.png` |
| Label composition | `python scripts/plot_multimodel_label_composition.py --root results/multimodel` | `combined_label_composition_stacked.png` |
| Summary table | `python scripts/export_multimodel_summary_table.py --matrix-json …` | `summary_table_models_categories.csv` + `.png` |
| Category correlation | `python scripts/plot_category_correlation_across_models.py --matrix-json …` | `combined_category_correlation_across_models.png` |
| Interactive heatmap (Plotly) | `python scripts/plot_multimodel_interactive_matrix.py --matrix-unsafe … --matrix-risk …` | `figures/multimodel/interactive_rates.html` |
| Fingerprint PCA (Tier 3) | `python scripts/plot_fingerprint_pca.py --root results/multimodel` | `figures/multimodel/fingerprint_pca.png` + optional `fingerprint_pca_meta.json` ([`INTERPRETABILITY_VIZ.md`](INTERPRETABILITY_VIZ.md)) |
| Failure-mode / label category heatmap | `python scripts/plot_failure_mode_category_heatmap.py --results <labeled.json>` | `figures/failure_mode_category_heatmap.png` (default path overridable) |
| Safety frontier (risk vs refusal) | `python scripts/plot_safety_frontier.py --root results/multimodel` | `figures/multimodel/safety_frontier.png` |
| Prompt pressure scores (Tier 3) | `python scripts/score_prompt_pressure.py` | [`results/prompt_pressure_scores.json`](results/prompt_pressure_scores.json) ([`PROMPT_PRESSURE_SCORING.md`](PROMPT_PRESSURE_SCORING.md)) |
| Pressure vs safety correlation | `python scripts/correlate_pressure_with_safety.py` | [`results/pressure_safety_correlation.json`](results/pressure_safety_correlation.json) |
| Associational regression proxies | `python scripts/regression_causal_proxies.py all --root results/multimodel --pressure-json results/prompt_pressure_scores.json` | [`results/causal_proxy_regressions.json`](results/causal_proxy_regressions.json) ([`CAUSAL_PROXIES.md`](CAUSAL_PROXIES.md)) |

**Effect sizes in `significance_stats*.json`:** Cramér’s V, per-category Wilson CIs for \(\hat p_U\) and \(\hat p_R\), Woolf 95% CIs for Fisher odds ratios ([`scripts/stats_utils.py`](scripts/stats_utils.py)).

## Python environment

- **Python:** 3.10+ recommended (see README).
- **Dependencies:** [`requirements.txt`](requirements.txt). For a **bit-for-bit** freeze after `pip install -r requirements.txt`, run:

  ```bash
  pip freeze > requirements.lock.txt
  ```

  Commit `requirements.lock.txt` when you need strict replication of numeric outputs from optional plotting stacks.

## Human labels

- Labels are **manual** (`analyze_results.py` or equivalent workflow).
- **Single-rater** in the reported run; inter-rater reliability (IRR) **not** reported—see report §6.
- **Labeling rubric (worked examples):** [`LABEL_RUBRIC.md`](LABEL_RUBRIC.md).

## Multi-model tier freeze (auxiliary corpus)

Primary narrative statistics in [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md) refer to the **pilot** artifact [`results/pilot/results.json`](results/pilot/results.json). Cross-model claims must cite the **tier tree** separately (see report §6.1).

| Field | Value |
| ----- | ----- |
| **Labeling frozen (UTC)** | 2026-04-12 |
| **Prompt bank** | Same [`prompts.json`](prompts.json) as pilot (90 rows). |
| **Layout** | [`results/multimodel/<tier>/results_<provider>_<slug>.json`](results/multimodel/) — nine labeled files (cheap / mid / expensive × three providers). |
| **Authoritative model ids** | [`configs/tier_models.json`](configs/tier_models.json) |

**Exact model strings (tiers):**

| Tier | OpenAI | Anthropic | Gemini |
| ---- | ------ | --------- | ------ |
| cheap | `gpt-4o-mini` | `claude-3-haiku-20240307` | `gemini-2.5-flash` |
| mid | `gpt-4o` | `claude-3-sonnet-20240229` | `gemini-2.5-pro` |
| expensive | `gpt-4.1` | `claude-3-opus-20240229` | `gemini-2.5-pro` |

**Gemini tier caveat:** **mid** and **expensive** both use **`gemini-2.5-pro`** (same model id; API constraints). Tier differentiation for Gemini is **not** a capability ladder—contrast across tiers is driven mainly by OpenAI and Anthropic model choices. See `_comment` in `tier_models.json`.

**Downstream artifacts (regenerated 2026-04-12):**

- Next to each results file: `significance_stats_<stem>.json` from [`scripts/compute_significance.py`](scripts/compute_significance.py), verified with [`scripts/verify_artifact_chain.py`](scripts/verify_artifact_chain.py).
- Figures: `results/multimodel/<tier>/figures/<stem>/fig*.png` (and pilot: `results/pilot/figures/results/`) from [`scripts/generate_report_figures.py`](scripts/generate_report_figures.py).
- **Batch command:** `python scripts/postprocess_multimodel_tiers.py --also results/pilot/results.json` (from `llm-safety-experiment/`). On Windows or headless hosts, use `MPLBACKEND=Agg` and **`--skip-sankey`** if Kaleido/Plotly export hangs; Sankey PNGs are optional for the numeric chain.
- **Console summary** (aggregate UNSAFE % / risk % per file): [`results/multimodel/SUMMARY_CONSOLE.txt`](results/multimodel/SUMMARY_CONSOLE.txt) from `python scripts/summarize_multi_model.py`.

**Git (repository snapshot):** Repository root `llm-safety-analysis/`. **Reproducibility bundle (all artifacts + docs + lockfile):** `87f75541116c6fde52b63caa605a84d4d30434eb`. Later commits may adjust documentation only; use `git log` / `git show 87f75541116c6fde52b63caa605a84d4d30434eb` to recover the frozen tree.
