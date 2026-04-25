# Local commands: multi-model run + labeling (you run these)

Step-by-step runbook for replicating the multi-model batch on your machine. See also [`README.md`](README.md).

## 0. One-time setup (PowerShell)

```powershell
cd c:\Users\Owner\OneDrive\Desktop\llm-safety-analysis\llm-safety-experiment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ensure `.env` in this folder defines real keys (not placeholders):

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY` **or** `GOOGLE_API_KEY`

Keep the venv **activated** for every command below.

---

## 1. Run the 90-prompt batch (three models per tier)

**Important:** Model IDs change over time. If you see `ERROR:` rows with `404` or `not_found_error`, open each provider’s current model list and **substitute working ids** in [`configs/tier_models.json`](configs/tier_models.json) before re-running.

**All three tiers (nine API runs, 810 calls total):**

```powershell
cd c:\Users\Owner\OneDrive\Desktop\llm-safety-analysis\llm-safety-experiment
python scripts/run_all_tiers.py --dry-run
python scripts/run_all_tiers.py
```

**One tier at a time** (writes under `results/multimodel/<cheap|mid|expensive>/`):

```powershell
python run_multi_model.py --tier cheap openai:gpt-4o-mini anthropic:claude-3-haiku-20240307 gemini:gemini-2.5-flash
```

**Ad hoc** (default output folder `results/multimodel/unsorted/`):

```powershell
python run_multi_model.py openai:gpt-4o anthropic:claude-3-sonnet-20240229 gemini:gemini-2.5-flash
```

**Expected outputs** — `results_<provider>_<model-slug>.json` in the chosen folder (see `results_slug` in `run_experiment.py`).

**Re-run only one model** after fixing a bad id:

```powershell
python run_multi_model.py --tier mid anthropic:claude-3-sonnet-20240229
```

---

## 2. If prompts “didn’t run” or you see errors

The harness often **continues** on API failure: failures are stored in `response` as text starting with `ERROR:`.

| Symptom | What to check |
|--------|----------------|
| Script exits with “Set … API_KEY” | Missing or placeholder key in `.env`. |
| JSON has many `ERROR:` rows | Wrong **model id**, billing/quota, or network; read the exact error text in the file. |
| `ModuleNotFoundError` | Activate `.venv` and run from `llm-safety-experiment`. |
| Anthropic `not_found_error` / 404 model | Use a model id from [Anthropic’s model docs](https://docs.anthropic.com/en/docs/about-claude/models). |
| Gemini “no longer available to new users” | Pick a current id from [Gemini API models](https://ai.google.dev/gemini-api/docs/models). |

**Quick check:** search a results file for `"ERROR:"`.

---

## 3. Label each results file (interactive)

One file at a time (paths under `results/multimodel/...`):

```powershell
python analyze_results.py --results results/multimodel/mid/results_openai_gpt-4o.json
python analyze_results.py --results results/multimodel/expensive/results_anthropic_claude-3-opus-20240229.json
python analyze_results.py --results results/multimodel/cheap/results_gemini_gemini-2.5-flash.json
```

- Enter `safe`, `partial`, or `unsafe` per row.
- `q` quits early; progress is saved after each label.

**Relabeling:** If rows already have labels (e.g. seeded from `scripts/seed_labels_from_pilot.py` for stats), clear them first:

```powershell
python scripts/clear_labels.py --target results/multimodel/expensive/results_anthropic_claude-3-opus-20240229.json
```

Then run `analyze_results.py` again so every row is judged from **that file’s** `response` text.

**Do not** meaningfully label rows whose `response` is still an API `ERROR:` until you fix the run and regenerate completions.

---

## 4. After labeling (optional)

Per labeled file:

```powershell
python scripts/compute_significance.py --results <path-to-results.json>
python scripts/verify_artifact_chain.py --results <path-to-results.json> --stats significance_stats_<stem>.json
```

The default stats filename is `significance_stats_<results_basename_without_json>.json` (see `scripts/compute_significance.py`).

Aggregate:

```powershell
python scripts/summarize_multi_model.py
```

Figures into a **separate** folder (avoids overwriting default `figures/`):

```powershell
python scripts/generate_report_figures.py --results <path> --figures-dir figures/multi_model/<short-name> --skip-sankey
```

---

## 5. Pilot file

The frozen single-model pilot is **`results/pilot/results.json`**. Do not overwrite it unless you intend a new pilot wave. Multi-model runs live under `results/multimodel/` (see [`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md)).
