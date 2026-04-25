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
