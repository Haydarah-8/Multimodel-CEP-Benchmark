# LLM safety experiment

Small toolkit to run a fixed prompt set against **OpenAI**, **Anthropic**, or **Google Gemini**, store responses, manually label them (`safe` / `partial` / `unsafe`), and summarize unsafe rates by category with pandas.

**Use only for authorized safety research, red teaming with clear scope, or education.** Prompts are designed to probe model behavior; handle outputs responsibly.

## What next (implementation priority)

1. **Track A — Ship:** After changing `results/pilot/results.json`, run `python scripts/compute_significance.py` and `python scripts/verify_artifact_chain.py`; refresh figures with `python scripts/generate_report_figures.py`. Keep [`PROVENANCE.md`](PROVENANCE.md), [`LLM_SAFETY_EXPERIMENT_SHORT.md`](LLM_SAFETY_EXPERIMENT_SHORT.md), and appendix anchors in sync with the main report.
2. **Track B — Replication:** Follow the **Executable runbook (Phase 1)** in [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md) (multi-model commands, `export_irr_subset.py` for dual coding, paired-prompt protocol as a manual sheet).

## Requirements

- Python 3.10+ recommended

## Install

```bash
cd llm-safety-experiment
python -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

For strict replication of optional figure outputs, generate a lockfile after install: `pip freeze > requirements.lock.txt` (see [`PROVENANCE.md`](PROVENANCE.md)).

## API keys

Set keys in `.env` (or the environment) for whichever providers you use:

| Provider   | Environment variable(s) |
| ---------- | ----------------------- |
| OpenAI     | `OPENAI_API_KEY`        |
| Anthropic  | `ANTHROPIC_API_KEY`     |
| Gemini     | `GEMINI_API_KEY` or `GOOGLE_API_KEY` |

Optional for Gemini only: `GEMINI_MAX_OUTPUT_TOKENS` (integer, default **4096**, max **8192**) sets `max_output_tokens` in [`provider_clients.py`](provider_clients.py). OpenAI and Anthropic still use the shared 200-token cap unless you change the code.

The harness refuses to start if the key for the chosen `--provider` is missing. Replace any placeholder `your_api_key_here` for OpenAI runs.

## Results on disk

- **Pilot (single-model, frozen):** `results/pilot/results.json` — default output of `python run_experiment.py` with OpenAI + default model.
- **Multi-model, tiered:** `results/multimodel/cheap|mid|expensive/` — use `python run_multi_model.py --tier <tier> ...` or `python scripts/run_all_tiers.py` (see [`configs/tier_models.json`](configs/tier_models.json)).
- **Layout map:** [`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md). **Labeling:** multi-model statistics are only defensible when you assign `safe` / `partial` / `unsafe` from **each model’s response** (`analyze_results.py`). Copying labels from the pilot via `seed_labels_from_pilot.py` is a tooling shortcut, not gold adjudication.

## Run the experiment

```bash
python run_experiment.py
```

- Reads `prompts.json` (override with **`--prompts`**), calls the API once per prompt, writes **`results/pilot/results.json`** when using default **OpenAI** + default model (see below). Otherwise default output is **`results/multimodel/unsorted/results_<provider>_<model_slug>.json`** (collision-safe across APIs).
- **`--provider`** — `openai` (default), `anthropic`, or `gemini`. Non-OpenAI providers require **`--model`** (provider-specific id).
- Default OpenAI model is **`gpt-4o-mini`** (`MODEL` in `run_experiment.py`). Override with **`OPENAI_MODEL`** in `.env` or **`--model`**.
- **Custom output:** `python run_experiment.py --model gpt-4o --output path/to/results_custom.json`
- **Anthropic example:** `python run_experiment.py --provider anthropic --model claude-3-5-haiku-20241022`
- **Gemini example:** `python run_experiment.py --provider gemini --model gemini-2.0-flash`
- **Multi-run (same prompts, one JSON per API + model):**
  - **Tiered (recommended):** `python scripts/run_all_tiers.py --dry-run` then run without `--dry-run` after editing [`configs/tier_models.json`](configs/tier_models.json).
  - **One tier:** `python run_multi_model.py --tier cheap openai:gpt-4o-mini anthropic:claude-3-haiku-20240307 gemini:gemini-2.5-flash`
  - Bare ids are treated as OpenAI: `python run_multi_model.py gpt-4o-mini gpt-4o` → `results_openai_*.json` under `results/multimodel/unsorted/`
  - Or **`MULTI_MODELS=openai:gpt-4o-mini,gemini:gemini-2.5-flash`**
- See [`PROVENANCE.md`](PROVENANCE.md) and [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md) for `provider` on each row and filenames.
- Progress is printed as `[i/n] id=... category=...`.
- Failures are recorded in the `response` field as `ERROR: ...` so the run can finish all prompts.

**Hands-on multi-model replication (PowerShell, model IDs you control):** see [`LOCAL_MULTI_MODEL_RUNBOOK.md`](LOCAL_MULTI_MODEL_RUNBOOK.md). To clear existing labels before relabeling: `python scripts/clear_labels.py --target <results_file.json>`.

## Label and analyze results

```bash
python analyze_results.py
python analyze_results.py --results results/multimodel/mid/results_openai_gpt-4o.json
```

- Walks through rows where `label` is missing and asks for `safe`, `partial`, or `unsafe`.
- Default `--results` is **`results/pilot/results.json`** when omitted.
- Type **`q`** to stop early; progress already saved after each label is kept.
- After labeling (or when you quit), prints per-category **unsafe percentage** (among labeled rows only), for example:

  ```
  Category: roleplay
  Unsafe: 35%
  ```

- Also prints overall labeled count and overall unsafe percentage.

## Files

| File                 | Role                                                |
| -------------------- | --------------------------------------------------- |
| `prompts.json`       | Input prompts (`id`, `category`, `text`)            |
| `results/pilot/results.json` | Pilot outputs plus `label` for manual review |
| `results/multimodel/**` | Tiered multi-model JSON + optional `significance_stats_*.json` |
| [`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md) | Where each artifact lives |
| `run_experiment.py`  | Calls chosen API; `--provider`, `--model`, `--output` (see above) |
| `provider_clients.py` | Shared OpenAI / Anthropic / Gemini completion helpers |
| `run_multi_model.py` | Same prompts, multiple `provider:model` specs → `results_<provider>_<slug>.json` each (`--tier` / `--output-dir`) |
| `scripts/run_all_tiers.py` | Runs cheap + mid + expensive batches from `configs/tier_models.json` |
| `configs/tier_models.json` | Pre-specified model ids per tier × provider |
| `analyze_results.py` | Interactive labels + pandas summary (optional `--results`) |
| [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md) | Row schema + optional dual-coding fields |
| `.env`               | API keys: OpenAI / Anthropic / Gemini as needed (and optional `OPENAI_MODEL`) |
| `requirements.txt`   | Python dependencies                                 |
| `LLM_SAFETY_EXPERIMENT_REPORT.md` | Full write-up: **lean** inline visuals (opening CEP graph, Figures 9 & 30, tables); remaining figures in appendix |
| `LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md` | **Appendix A:** legacy/alternate encodings, conceptual Figs 28–34; **Appendix B:** method and extended figures moved from main text |
| `LLM_SAFETY_EXPERIMENT_SHORT.md` | Short brief (~6–8 page equivalent) linking to full report + appendix |
| [`PROVENANCE.md`](PROVENANCE.md) | Model, scripts, and artifact chain for reproducibility |
| [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md) | Next-study design: dual coding, paired prompts, multi-model matrix, power/CIs |
| [`APPLICATIONS.md`](APPLICATIONS.md) | One-page project card + ~60s interview narrative (hiring / portfolio) |
| [`FELLOWSHIP_APPLICATION_BRIEF.md`](FELLOWSHIP_APPLICATION_BRIEF.md) | **Fellowship / research-statement** brief: workstreams, 4-month plan, SE→research bridge, checklist |
| `FIGURE_GENERATION_PROMPT.md` | Copy-paste brief for external AI / designers (extra figures, slides) |
| `figures/`           | Optional PNG exports from `generate_report_figures.py` (`fig1_*`, `figure2_*`, `fig_category_*`, `fig_cep_*`, `fig_failure_*`, `fig_entropy_*`, Sankey PNG) |
| `scripts/generate_report_figures.py` | Optional: builds PNGs from `results.json` (unsafe-rate, Wilson CI, stacked chart, heatmap, CEP line chart, Sankey, radar fingerprint, entropy) |
| `scripts/compute_significance.py` | χ² + Fisher tests → `significance_stats.json` (§3.6) |
| `scripts/verify_artifact_chain.py` | Asserts pilot `results.json` counts match `significance_stats.json` (defaults: `results/pilot/`) |
| `scripts/export_irr_subset.py` | Dual-coding workload JSON for IRR (see `REPLICATION_PROTOCOL.md`) |

## Report figures

The paper-style report keeps a **small main-text figure set** (signature CEP flowchart, Figure 9, Figure 30) plus tables; **Appendix B** in `LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md` holds the full set of pipeline, method, and section figures that were moved out of the main file for readability. **Appendix A** holds alternate encodings of the primary statistics and supplementary conceptual diagrams. Dark-theme Mermaid is used throughout; optional PNG links where noted. No build step is required to view Mermaid in a capable renderer.

To export **matplotlib** PNGs for slides or PDF paste-in (optional; the report’s canonical figures are Mermaid), after updating `results/pilot/results.json`:

```bash
python scripts/generate_report_figures.py
python scripts/generate_report_figures.py --skip-sankey
python scripts/generate_report_figures.py --results results/multimodel/mid/results_openai_gpt-4o.json --figures-dir figures/multi_model/openai_gpt-4o
python scripts/summarize_multi_model.py
```

Use `--skip-sankey` if Plotly/Kaleido hangs on your machine; full Sankey PNG is optional.

Also writes `figures/fig_failure_pattern_fingerprint.png` (radar-style polar plot of SAFE/PARTIAL/UNSAFE % by category) and `figures/fig_entropy_safety.png` (Shannon entropy of the label distribution per category). Matplotlib figures need `matplotlib`; the Sankey PNG needs `plotly` and `kaleido` (all listed in `requirements.txt`). See the long list in the script docstring for the full set of outputs.

## Switching models

1. **Environment (preferred):** add to `.env`:

   ```
   OPENAI_MODEL=gpt-4o
   ```

2. **Code:** change the `MODEL` constant in `run_experiment.py`.
