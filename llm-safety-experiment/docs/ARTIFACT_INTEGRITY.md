# Artifact integrity checklist

Use this before citing numbers or figures in a paper, fellowship summary, or portfolio.

**Human-readable summary of methods and results:** [`RESEARCH_MONOGRAPH.md`](RESEARCH_MONOGRAPH.md) (start here for outsiders; cite frozen JSON + this checklist for numbers).

## Multimodel (nine runs)

1. **Paths:** `results/multimodel/cheap|mid|expensive/results_<provider>_<slug>.json` (see [`RESULTS_LAYOUT.md`](../RESULTS_LAYOUT.md)).
2. **Scan:** `python scripts/audit_multimodel_artifacts.py`  
   - Optional CI gate: `python scripts/audit_multimodel_artifacts.py --strict`  
   - Expect **90 rows**, **0** `ERROR:` responses, **0** missing/bad labels for frozen releases.
3. **Matrices / figures:** `python scripts/reproduce_main_figures.py` (or `--skip-pilot` if only multimodel changed). Add **`--extra-visuals`** for parallel coordinates, Wilson forests, clustermap, tier slopes, stacked composition, summary table, category correlation, ranks, and `interactive_rates.html`. Add **`--phd-visuals`** for McNemar pairwise matrices, Jeffreys Beta credible-interval facets, tier×provider interaction plots, UNSAFE concordance histogram, Cohen’s *h* grid, prompts×runs incidence heatmap, logit profiles, and direct-vs-roleplay escalation scatter.  
   - Regenerates `figures/multimodel/signature_rate_matrix.json`, risk matrix, combined heatmaps, 9-panel figure, fingerprints, frontier, PCA, and optional extended charts.
4. **Gemini tier caveat:** Document that **mid and expensive Gemini share `gemini-2.5-pro`**; tier contrast for Gemini is **not** a model-SKU ladder (see `configs/tier_models.json` `_comment`).

## Pilot (single-model report)

1. After editing `results/pilot/results.json`:  
   `python scripts/compute_significance.py`  
   `python scripts/verify_artifact_chain.py`
2. Figures: `python scripts/generate_report_figures.py` (add `--skip-sankey` if Plotly/Kaleido hangs).

## Optional: per-file significance

`scripts/postprocess_multimodel_tiers.py` can run significance + verify + figures for each labeled multimodel JSON when you need per-model stats files.

## Failure-mode heatmap

If the failure-mode × category heatmap should be **primary** evidence, invest in explicit **failure_mode** coding on rows; otherwise the pipeline may use **label-fallback** (weaker; document which path you used).

## Provenance

Record commit hash, Python version, and `pip freeze` as in [`PROVENANCE.md`](../PROVENANCE.md).
