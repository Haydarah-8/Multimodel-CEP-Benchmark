# Results directory layout

All empirical JSON artifacts live under `results/` so the package root stays clean.

| Path | Purpose |
|------|---------|
| `results/pilot/results.json` | **Frozen single-model pilot** (default OpenAI `gpt-4o-mini` run). Human labels adjudicate this corpus for the main report. |
| `results/pilot/significance_stats.json` | Default significance output for the pilot (next to `results.json`). |
| `results/multimodel/cheap/` | Tier: cost-efficient models (see `configs/tier_models.json`). |
| `results/multimodel/mid/` | Tier: mid-range capability/cost. |
| `results/multimodel/expensive/` | Tier: frontier / highest capability (edit model ids to match your API access). |
| `results/multimodel/unsorted/` | Default output for ad hoc `run_multi_model.py` runs without `--tier` / `--output-dir`. |
| `results/archive/legacy_flat/` | Older flat-root JSON and failed API runs kept for audit (not primary analysis). |

**Naming:** Each run file is `results_<provider>_<model_slug>.json` (see `run_experiment.results_slug`).

**Batch all tiers:** `python scripts/run_all_tiers.py` (see `--dry-run` first). **810** API calls total if every tier is full.

**Labeling:** Multi-model files must be labeled per **response text** (`analyze_results.py`). Copying labels from the pilot by prompt id is a pipeline shortcut only and is **not** gold-standard cross-model adjudication.

**Combined multimodel figures** (regenerate with `python scripts/reproduce_main_figures.py`; add **`--extra-visuals`** for extended charts):

| Path | Description |
|------|-------------|
| `figures/multimodel/signature_rate_matrix.json` | Built matrix \(\hat p\) unsafe; `signature_rate_matrix_risk.json` for risk |
| `figures/multimodel/combined_signature_unsafe_heatmap.png` | 9 runs × 5 categories |
| `figures/multimodel/combined_signature_excess_vs_direct.png` | Excess unsafe vs direct |
| `figures/multimodel/combined_signature_risk_heatmap.png` | \(\hat P(\mathrm{risk})\) |
| `figures/multimodel/combined_9panel_unsafe_by_category.png` | 3×3 tier × provider bars (muted palette, Wilson 95% CIs); `--no-ci` on script to omit |
| `figures/multimodel/combined_radar_grid_unsafe.png` | 3×3 polar “radar” profiles over categories |
| `figures/multimodel/combined_safety_frontier.png` | Refusal vs risk (needs `fingerprint_all_multimodel`) |
| `figures/multimodel/combined_fingerprint_pca.png` | PCA of fingerprints |
| `figures/multimodel/combined_parallel_coordinates.png` | Parallel coords (color = provider); `*_by_tier.png` = tier color |
| `figures/multimodel/combined_forest_wilson_unsafe.png` | Forest plot, Wilson CIs, unsafe |
| `figures/multimodel/combined_forest_wilson_risk.png` | Forest plot, risk metric |
| `figures/multimodel/combined_clustermap_rates.png` | Dendrogram + clustered heatmap |
| `figures/multimodel/combined_tier_slope_overall_rates.png` | Tier ladder: overall unsafe & risk |
| `figures/multimodel/combined_label_composition_stacked.png` | Stacked label shares per run |
| `figures/multimodel/summary_table_models_categories.csv` | Table export (also `.png`) |
| `figures/multimodel/combined_category_correlation_across_models.png` | Category × category **r** across runs |
| `figures/multimodel/interactive_rates.html` | Plotly toggle unsafe / risk |
| `figures/multimodel/combined_within_category_ranks_unsafe.png` | Within-column rank of $\\hat p(\\mathrm{unsafe})$ (1–9) |
| `figures/multimodel/phd_mcnemar_pairwise_unsafe.png` | Paired McNemar **p**-matrix (UNSAFE); `--phd-visuals` |
| `figures/multimodel/phd_mcnemar_pairwise_risk.png` | Same for **risk** (P∪U) |
| `figures/multimodel/phd_beta_posterior_unsafe_facets.png` | Jeffreys Beta 95% credible intervals, faceted by category |
| `figures/multimodel/phd_tier_provider_interaction_unsafe.png` | Tier×provider interaction lines per category |
| `figures/multimodel/phd_unsafe_concordance_histogram.png` | How many runs flagged each prompt UNSAFE (*k*=0…9) |
| `figures/multimodel/phd_cohens_h_pairwise_overall.png` | Cohen’s *h* grid on overall UNSAFE rate |
| `figures/multimodel/phd_unsafe_incidence_prompts_by_run.png` | Binary prompts×runs incidence (sorted rows) |
| `figures/multimodel/phd_logit_category_profiles_unsafe.png` | Empirical logit profiles across categories |
| `figures/multimodel/phd_direct_vs_roleplay_escalation.png` | Direct vs roleplay \(\hat p\) per run |

Per-run artifacts: `<tier>/figures/<results_stem>/model_fingerprint.json` and curve PNG (from `scripts/fingerprint_all_multimodel.py`).
