# Inter-rater reliability engine (multimodel)

Defensible **human** inter-rater agreement uses paired `label` (primary) and `label_rater2` on the **same** `response`. Model-generated `label_model_proxy` is **exploratory only** and must not be reported as human IRR.

## Workflow

1. **Workload:** [`scripts/export_irr_subset.py`](scripts/export_irr_subset.py) → subset JSON for rater 2 (pre-specified UNSAFE + stratified SAFE/PARTIAL).
2. **Merge:** Second rater fills `label_rater2` per [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md); merge into the canonical `results_*.json` (same `id` rows).
3. **Single-file κ:** [`scripts/compute_irr_kappa.py`](scripts/compute_irr_kappa.py) — overall and `--by-category` (console).
4. **Multimodel report:** [`scripts/irr_multimodel_report.py`](scripts/irr_multimodel_report.py) → [`results/multimodel/irr_multimodel_report.json`](results/multimodel/irr_multimodel_report.json) — per **file (model)**, per **tier** (pooled), per **category**, confusion matrices, optional **bootstrap** κ CIs (`--bootstrap 1000`).
5. **Plots:** [`scripts/plot_irr_disagreement_heatmaps.py`](scripts/plot_irr_disagreement_heatmaps.py) — disagreement \((1-p_o)\) heatmaps (model × category, tier × category) and global **P(compare | primary)** 3×3 (unless `--no-conditional`).

## Bootstrap (“simulation”)

Resampling **paired** rows with replacement approximates sampling uncertainty for κ (descriptive). Not a generative model of multiple human annotators.

## Model proxy (optional)

[`scripts/model_proxy_irr_label.py`](scripts/model_proxy_irr_label.py) writes a **copy** of a results file with `label_model_proxy`. Then:

```bash
python scripts/irr_multimodel_report.py --root results/multimodel/cheap --compare-field label_model_proxy
```

The report’s `note_compare` field will state **proxy rater (not human IRR)**.

## Pooling caveats

**Per-tier** and **global** blocks concatenate paired rows across files in that scope. This assumes the **same rubric** and comparable adjudication targets; it is not a hierarchical rater model.

## Minimum stratum size

Per-category κ in the JSON is omitted (null with a note) when \(n < 5\) paired rows in that stratum (`MIN_PAIRS_CATEGORY_KAPPA` in [`scripts/irr_utils.py`](scripts/irr_utils.py)).
