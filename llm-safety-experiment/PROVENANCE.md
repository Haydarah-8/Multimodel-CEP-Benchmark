# Provenance and reproducibility

Claims in [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md) are conditional on the **artifact chain** below. Update this file when you change model, prompts, or labels.

## Canonical data

| Artifact | Role |
| -------- | ---- |
| [`prompts.json`](prompts.json) | Fixed prompt bank (90 rows: `id`, `category`, `text`) |
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

Then label each file: `python analyze_results.py --results results_<provider>_<slug>.json`.

**Recommended:** When you freeze a run for publication or a job portfolio, record **date of API calls** and **exact model string** used (including override) in a git commit message or here.

**Last consistency check (artifact chain):** After any change to `results/pilot/results.json`, run `python scripts/compute_significance.py` then `python scripts/verify_artifact_chain.py` so `results/pilot/significance_stats.json` and §3.6 of the report stay aligned.

## Analysis scripts

| Script | Command | Output |
| ------ | ------- | ------ |
| Significance | `python scripts/compute_significance.py` | `significance_stats.json` + console |
| Significance (multi-model file) | `python scripts/compute_significance.py --results results_openai_gpt-4o-mini.json` | `significance_stats_results_openai_gpt-4o-mini.json` (default naming) + console |
| Verify chain | `python scripts/verify_artifact_chain.py` | Exit 0 if `results.json` contingency matches `significance_stats.json` |
| Figures (optional) | `python scripts/generate_report_figures.py --results results.json` | `figures/*.png` (overwrites; use separate runs or copy `figures/` if comparing models) |
| Multi-model summary | `python scripts/summarize_multi_model.py` | Console: aggregate % UNSAFE / % risk per file |
| IRR subset export | `python scripts/export_irr_subset.py` | `irr_subset_for_rater2.json` (dual-coding workload; see `REPLICATION_PROTOCOL.md`) |

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

**Git (repository snapshot):** `87f75541116c6fde52b63caa605a84d4d30434eb` (`master` root commit at `llm-safety-analysis/`) — full tree including labeled multimodel JSON, stats, figures, and docs at this reference.
