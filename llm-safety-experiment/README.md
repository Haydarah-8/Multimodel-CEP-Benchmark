# Multimodel-CEP-Benchmark (package: `llm-safety-experiment`)

**Aevion Labs** — **multimodel** **elicitation-stratified** safety audit (CEP-oriented benchmark) for OpenAI, Anthropic, and Google Gemini.

**Replication-oriented empirical overview** (notation, inference posture, reproducibility checklist, BibTeX): [parent `README.md`](../README.md). This file is the **package quick reference** for day-to-day commands.

Run a **fixed** 90-prompt bank (five strata × 18 prompts), collect assistant outputs, **human-label** them `safe` / `partial` / `unsafe`, and analyze **UNSAFE** rates versus a broader **risk** surface (PARTIAL ∪ UNSAFE). The design targets **monitoring gaps**: harmful or dual-use content often appears under indirect or narrative framing even when blunt **UNSAFE** counts stay low.

**Use only for authorized safety research, scoped red teaming, or education.** Handle model outputs responsibly. Repository-wide notes: [`../SECURITY.md`](../SECURITY.md).

---

## Start here

| Resource | Purpose |
| -------- | ------- |
| **[`docs/RESEARCH_MONOGRAPH.md`](docs/RESEARCH_MONOGRAPH.md)** | **Primary narrative:** methods, pilot + multimodel results, figure index, limits, replication |
| [`docs/MULTIMODEL_MANUSCRIPT.md`](docs/MULTIMODEL_MANUSCRIPT.md) | **Multimodel-only** write-up (nine API runs; links to monograph for pilot) |
| [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md) | Full technical report (notation, extended discussion) |
| [`docs/README.md`](docs/README.md) | Documentation index |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Setup, audit, reproduce commands |
| [`LICENSE`](LICENSE) | MIT License (Aevion Labs) |

---

## Reproduce figures (no API calls)

From this directory, after `pip install -r requirements.txt`:

```bash
python scripts/reproduce_main_figures.py
```

**Options:**

- `--extra-visuals` — parallel coordinates, Wilson forests, clustermap, tier slopes, composition, summary table, category correlation, rank heatmap, Plotly HTML.
- `--phd-visuals` — McNemar pairwise matrices, Jeffreys Beta facets, tier×provider interactions, concordance histogram, Cohen’s *h*, incidence heatmap, logit profiles, direct vs roleplay scatter.
- `--strict-audit` — fail on `ERROR:` responses, bad labels, or row count ≠ 90 in multimodel files.
- `--skip-pilot` / `--skip-fingerprints` — faster when only multimodel artifacts changed.

Outputs land in [`figures/multimodel/`](figures/multimodel/) and pilot [`figures/`](figures/). See [`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md).

**Gemini caveat:** mid- and expensive-tier Gemini may share **`gemini-2.5-pro`** in [`configs/tier_models.json`](configs/tier_models.json) — nine labeled runs, **eight** unique provider×model-id pairs.

---

## Install

```bash
cd llm-safety-experiment
python -m venv .venv
```

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

Optional lockfile: committed [`requirements.lock.txt`](requirements.lock.txt) or regenerate via `pip freeze > requirements.lock.txt` ([`PROVENANCE.md`](PROVENANCE.md)).

**Requirements:** Python 3.10+ recommended.

---

## API keys

Set in `.env` or the environment (never commit secrets):

| Provider  | Variable(s) |
| --------- | ----------- |
| OpenAI    | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Gemini    | `GEMINI_API_KEY` or `GOOGLE_API_KEY` |

Optional: `GEMINI_MAX_OUTPUT_TOKENS` (Gemini only; see [`provider_clients.py`](provider_clients.py)). OpenAI and Anthropic use a shared **200** output-token cap unless you change the code.

---

## Results layout

- **Pilot:** [`results/pilot/results.json`](results/pilot/results.json)
- **Multimodel:** [`results/multimodel/`](results/multimodel/) — [`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md)

Label **each model’s** `response` text ([`analyze_results.py`](analyze_results.py)). Seeding labels from the pilot is a **shortcut**, not gold cross-model adjudication ([`MULTI_MODEL_RESULTS.md`](MULTI_MODEL_RESULTS.md)).

---

## Run API experiments

```bash
python run_experiment.py
```

Default OpenAI model: **`gpt-4o-mini`**. Multi-model / tier batches: [`run_multi_model.py`](run_multi_model.py), [`scripts/run_all_tiers.py`](scripts/run_all_tiers.py), [`LOCAL_MULTI_MODEL_RUNBOOK.md`](LOCAL_MULTI_MODEL_RUNBOOK.md).

```bash
python analyze_results.py --results results/pilot/results.json
```

After labeling the pilot, refresh stats: `python scripts/compute_significance.py` and `python scripts/verify_artifact_chain.py`.

---

## Key files

| Path | Role |
| ---- | ---- |
| [`prompts.json`](prompts.json) | Prompt bank |
| [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md) | Row schema |
| [`LABEL_RUBRIC.md`](LABEL_RUBRIC.md) | Label definitions |
| [`PROVENANCE.md`](PROVENANCE.md) | Artifact chain, script index |
| [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md) | Stronger future study design (IRR, pairs) |
| [`scripts/reproduce_main_figures.py`](scripts/reproduce_main_figures.py) | One-command figure rebuild |
| [`scripts/audit_multimodel_artifacts.py`](scripts/audit_multimodel_artifacts.py) | Integrity scan |

---

## Citation

See **§9** in [`docs/RESEARCH_MONOGRAPH.md`](docs/RESEARCH_MONOGRAPH.md). Cite the repo URL, commit hash, and model ids from [`PROVENANCE.md`](PROVENANCE.md).
