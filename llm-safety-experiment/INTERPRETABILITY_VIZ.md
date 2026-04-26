# Interpretability visualizations (Tier 3)

Three figures help readers compare **models** and **elicitation categories** at a glance. They are **descriptive**; do not treat PCA axes, dendrogram merges, or convex hulls as causal or normative claims.

Prerequisites: labeled `results_*.json` and, for PCA/frontier, per-model [`model_fingerprint.json`](MODEL_FINGERPRINTS.md) (run [`scripts/fingerprint_all_multimodel.py`](scripts/fingerprint_all_multimodel.py)).

## 1. PCA embedding of fingerprints

**Script:** [`scripts/plot_fingerprint_pca.py`](scripts/plot_fingerprint_pca.py)

**What it shows:** Each model is a point in 2D principal-component space of a fixed **18-dimensional** feature vector: for each elicitation category (in `CAT_ORDER`), the fingerprint curve values refusal (`P(safe)`), compliance (`P(unsafe)`), and risk (`P(partial∪unsafe)`), plus ASS (imputed 0 if null) and the two ESI gaps.

**Limits:** PCA is rotation-invariant; interpret relative distances only in a exploratory sense. Needs **≥3** fingerprint files with full curves.

**Commands:**

```bash
cd llm-safety-experiment
python scripts/plot_fingerprint_pca.py --root results/multimodel --out figures/multimodel/fingerprint_pca.png --meta-out figures/multimodel/fingerprint_pca_meta.json --annotate
```

## 2. Category clustering (failure modes or labels)

**Script:** [`scripts/plot_failure_mode_category_heatmap.py`](scripts/plot_failure_mode_category_heatmap.py)

**What it shows:** Rows = elicitation categories (with data). Columns = either **`failure_mode`** distribution (if enough rows are coded: ≥10 non-empty and ≥5% of rows) or **fallback** `safe` / `partial` / `unsafe` shares. Cell = within-category proportion. **Jensen–Shannon** distances + **average linkage** reorder rows; heatmap uses the leaf order.

**Limits:** Sparse `failure_mode` coding triggers label fallback automatically (noted in stderr).

**Commands:**

```bash
python scripts/plot_failure_mode_category_heatmap.py --results results/pilot/results.json --out-png figures/fm_category_pilot.png --out-json figures/fm_category_pilot.json
python scripts/plot_failure_mode_category_heatmap.py --results results/multimodel/cheap/results_openai_gpt-4o-mini.json --out-png figures/fm_category_cheap_openai.png
```

## 3. Safety frontier (risk vs refusal)

**Script:** [`scripts/plot_safety_frontier.py`](scripts/plot_safety_frontier.py)

**What it shows:** One point per model: **weighted** aggregate \(\hat P(\mathrm{safe})\) and \(\hat R=\hat P(\mathrm{partial}\cup\mathrm{unsafe})\) using per-category counts in the fingerprint as weights. Color encodes **provider** or **tier** (tier inferred from path: `cheap` / `mid` / `expensive`). Optional **`--hull`** draws a **Qhull joggled** convex hull (almost collinear points are handled); optional **`--line`** connects points sorted by refusal (descending)—a visual “tour,” not an efficiency frontier.

**Limits:** The subtitle and figure footnote state this is **not** a Pareto or causal frontier.

**Commands:**

```bash
python scripts/plot_safety_frontier.py --root results/multimodel --out figures/multimodel/safety_frontier.png --color-by tier --hull --line
```

## 4. Extended multimodel charts (optional)

Regenerate everything including these with:

```bash
python scripts/reproduce_main_figures.py --extra-visuals
```

| Output | Script | What it shows |
|--------|--------|----------------|
| `combined_parallel_coordinates.png` | [`scripts/plot_multimodel_parallel_coordinates.py`](scripts/plot_multimodel_parallel_coordinates.py) | Each run as a polyline over the five category axes (\(\hat p\) from the matrix). |
| `combined_parallel_coordinates_by_tier.png` | same (`--color-by tier`) | Same, colored by **tier** instead of provider. |
| `combined_forest_wilson_unsafe.png` / `combined_forest_wilson_risk.png` | [`scripts/plot_multimodel_forest_wilson.py`](scripts/plot_multimodel_forest_wilson.py) | Wilson 95% CIs per run × category (faceted by category). |
| `combined_clustermap_rates.png` | [`scripts/plot_multimodel_clustermap.py`](scripts/plot_multimodel_clustermap.py) | Average-linkage dendrogram + reordered heatmap (exploratory ordering). |
| `combined_tier_slope_overall_rates.png` | [`scripts/plot_tier_slope_chart.py`](scripts/plot_tier_slope_chart.py) | Cheap→mid→expensive **overall** % unsafe and % risk per provider. |
| `combined_label_composition_stacked.png` | [`scripts/plot_multimodel_label_composition.py`](scripts/plot_multimodel_label_composition.py) | 100% stacked SAFE/PARTIAL/UNSAFE per run. |
| `summary_table_models_categories.csv` + `.png` | [`scripts/export_multimodel_summary_table.py`](scripts/export_multimodel_summary_table.py) | Table of % unsafe by model × category (+ row mean). |
| `combined_category_correlation_across_models.png` | [`scripts/plot_category_correlation_across_models.py`](scripts/plot_category_correlation_across_models.py) | 5×5 Pearson **r** between category columns (noisy at n=9 runs). |
| `combined_within_category_ranks_unsafe.png` | [`scripts/plot_multimodel_within_category_ranks.py`](scripts/plot_multimodel_within_category_ranks.py) | Rank each run **within** a category column (9 = highest $\\hat p$). |
| `interactive_rates.html` | [`scripts/plot_multimodel_interactive_matrix.py`](scripts/plot_multimodel_interactive_matrix.py) | Plotly heatmap; buttons toggle **unsafe** vs **risk** (offline HTML). |

**Default multimodel bundle** (without `--extra-visuals`) also writes **`combined_radar_grid_unsafe.png`** and an upgraded **`combined_9panel_unsafe_by_category.png`** (muted bars + Wilson CIs). See [`scripts/plot_multimodel_nine_panel.py`](scripts/plot_multimodel_nine_panel.py) (`--no-ci` to drop error bars).

**Limits:** All use **n=18** per category cell where applicable; **nine runs / eight unique Gemini SKUs**; category correlation is **descriptive** only.

## 5. Publication / “PhD-level” diagnostics (`--phd-visuals`)

Run:

```bash
python scripts/reproduce_main_figures.py --phd-visuals
```

(Combine with `--extra-visuals` as needed; requires labeled `results_*.json` under `results/multimodel/`.)

| Output | Script | What it shows |
|--------|--------|----------------|
| `phd_mcnemar_pairwise_unsafe.png` / `phd_mcnemar_pairwise_risk.png` | [`scripts/plot_multimodel_mcnemar_pairwise.py`](scripts/plot_multimodel_mcnemar_pairwise.py) | **Paired McNemar** exact tests on shared prompt `id`s; asymmetric 9×9 **p**-matrix with significance stars. |
| `phd_beta_posterior_unsafe_facets.png` | [`scripts/plot_multimodel_beta_posterior_facets.py`](scripts/plot_multimodel_beta_posterior_facets.py) | **Jeffreys Beta–Binomial** 95% **credible** intervals + posterior mean per run × category (faceted by stratum). |
| `phd_tier_provider_interaction_unsafe.png` | [`scripts/plot_multimodel_interaction_tier_provider.py`](scripts/plot_multimodel_interaction_tier_provider.py) | **Interaction plot:** cheap→mid→expensive lines per provider within each category (Okabe–Ito–style colors). |
| `phd_unsafe_concordance_histogram.png` | [`scripts/plot_multimodel_unsafe_concordance.py`](scripts/plot_multimodel_unsafe_concordance.py) | **Cross-run concordance:** histogram of *k* = how many of the nine runs flagged each shared prompt as UNSAFE (0–9). |
| `phd_cohens_h_pairwise_overall.png` | [`scripts/plot_multimodel_cohens_h_pairwise.py`](scripts/plot_multimodel_cohens_h_pairwise.py) | **Cohen’s *h*** on **overall** UNSAFE rate (arcsin √*p*); symmetric pairwise grid; diagonal masked. |
| `phd_unsafe_incidence_prompts_by_run.png` | [`scripts/plot_multimodel_unsafe_incidence_heatmap.py`](scripts/plot_multimodel_unsafe_incidence_heatmap.py) | **Incidence:** binary prompts×runs heatmap (rows sorted by row sum); highlights disagreement drivers. |
| `phd_logit_category_profiles_unsafe.png` | [`scripts/plot_multimodel_logit_category_profile.py`](scripts/plot_multimodel_logit_category_profile.py) | **Logit profiles:** empirical logit per category per run (continuity \((k+0.5)/(n+1)\), *n*=18). |
| `phd_direct_vs_roleplay_escalation.png` | [`scripts/plot_multimodel_direct_vs_roleplay_escalation.py`](scripts/plot_multimodel_direct_vs_roleplay_escalation.py) | **Escalation scatter:** \(\hat P(\mathrm{unsafe}\mid\mathrm{direct})\) vs roleplay per run; above *y*=*x* → higher under roleplay. |

Shared style helpers: [`scripts/academic_plot_style.py`](scripts/academic_plot_style.py).

**Limits:** McNemar and Cohen’s *h* grids imply **many** pairwise contrasts—interpret as **exploratory** unless you pre-register a multiplicity adjustment; Beta intervals are **per-cell** not simultaneous.

## Related

- Fingerprints: [`MODEL_FINGERPRINTS.md`](MODEL_FINGERPRINTS.md), [`scripts/plot_model_fingerprints.py`](scripts/plot_model_fingerprints.py)
- Failure-mode codes: [`FAILURE_MODE_CODEBOOK.md`](FAILURE_MODE_CODEBOOK.md)
- Signature heatmaps (model × category rates): [`scripts/plot_multimodel_signature_heatmap.py`](scripts/plot_multimodel_signature_heatmap.py)
- Nine-panel bars: [`scripts/plot_multimodel_nine_panel.py`](scripts/plot_multimodel_nine_panel.py)
- Radar grid (polar 3×3): [`scripts/plot_multimodel_radar_grid.py`](scripts/plot_multimodel_radar_grid.py)
