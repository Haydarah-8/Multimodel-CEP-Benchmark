# Results JSON schema (`results/pilot/results.json` / `results_<provider>_<model_slug>.json` under `results/multimodel/...`)

Each row is one prompt completion.

## Required fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | any | Prompt id from `prompts.json` |
| `category` | string | Elicitation category (`direct`, `indirect`, …) |
| `prompt` | string | User message text |
| `response` | string | Assistant output or `ERROR: ...` |
| `label` | string or null | `safe` / `partial` / `unsafe` (filled by `analyze_results.py`) |

## Optional fields (written by tooling)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `provider` | string | API backend: `openai`, `anthropic`, or `gemini` (`run_experiment.py --provider`, `run_multi_model.py`). Legacy files may omit this (treat as OpenAI-only). |
| `model` | string | Model id for that provider (`run_experiment.py`, `run_multi_model.py`) |

## Optional fields (dual coding — manual or custom tooling)

For inter-rater reliability, you may add:

| Field | Type | Description |
| ----- | ---- | ----------- |
| `label_rater2` | string or null | Second rater’s label |
| `label_adjudicated` | string or null | Consensus / tie-break label |

**Workload export:** `python scripts/export_irr_subset.py` writes `irr_subset_for_rater2.json` (default: all UNSAFE rows + random 20% of others; `--seed`, `--fraction`). Use that list for second-rater labeling, then merge `label_rater2` into the main `results` file per [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md).

**Analysis:** `scripts/compute_significance.py` and `scripts/generate_report_figures.py` use **`label`** only. For adjudicated analysis, copy consensus into `label` or extend the scripts to prefer `label_adjudicated` when present.
