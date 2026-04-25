# Replication and extension protocol (next study)

This document specifies a **stronger** empirical design for follow-up work. It is **not** required to interpret the current \(n=90\) audit; it is a **template** for publishable replication and portfolio-grade evidence.

## Estimands (unchanged conceptual core)

- **Outcome:** \(Y \in \{\mathrm{S},\mathrm{P},\mathrm{U}\}\); **risk** \(R = \mathbf{1}[Y \in \{\mathrm{P},\mathrm{U}\}]\); **harm (strict)** \(\mathbf{1}[Y=\mathrm{U}]\).
- **Primary population quantities:** \(\Pr(Y \mid c)\), \(\Pr(R \mid c)\), \(\Pr(U \mid c)\) **per elicitation category** \(c\), under a **fixed rubric**.

## Design upgrades

### 1. Dual coding and IRR

- **Two** independent coders on **all** rows or a **pre-specified** subset (e.g. 100% of UNSAFE + random 20% of SAFE/PARTIAL).
- Report **agreement %** and **Cohen’s κ** (or equivalent) on \(Y\).
- **Adjudication rule:** majority vote, or third rater on disagreement—**pre-specify** before unblinding.

### 2. Power and sample size

- **Current:** \(n_c = 18\) per category yields **wide** Wilson intervals on rare events (Table 4).
- **Pre hoc:** choose minimum detectable difference in \(\hat{p}_U(c)\) (or \(\hat{p}_R(c)\)) between key contrasts (e.g. roleplay vs direct); solve for \(n_c\) at 80% power (exact or simulation-based for binomial).
- **Report:** CIs for **every** rate cited in the abstract (Wilson or Clopper–Pearson).

### 3. Intent-matched paired prompts (tests “surface form” prediction)

- For each of \(K\) **harm domains**, author **two** prompts: **direct** harmful surface vs **obfuscated** surface (same **intended** adjudication target—documented in a protocol sheet).
- **Paired** analysis: McNemar or paired bootstrap on **\(R\)** or **\(U\)** across pairs.
- **Falsifies** a strong null: “only wording, no strategic obscuring” should **not** show large **within-pair** gaps if CEP were mere noise.

### 4. Multi-model matrix

- **Same** `prompts.json`, **same** labels (or re-run labeling protocol per model if outputs differ).
- **Tooling:** [`run_multi_model.py`](run_multi_model.py) writes `results_<provider>_<slug>.json` per API + model; then `analyze_results.py --results …`, `compute_significance.py --results …`, [`scripts/summarize_multi_model.py`](scripts/summarize_multi_model.py).
- **Rows:** models/checkpoints; **columns:** categories or contrasts.
- **Claim:** **partial order stability** (e.g. roleplay ≥ direct on \(\hat{p}_U\)) **replicates**—not that every model is unsafe.

### 5. Threat model clarity

- **This audit:** fixed **taxonomy**, non-adaptive prompts—**structured red team**.
- **Not in scope:** adaptive **jailbreak** optimization (separate study: search budget, success metric).

## Pre-registration (lightweight)

- Before **full** label release or analysis of **held-out** pairs: commit a dated markdown listing **primary figure** (e.g. risk vs UNSAFE panel) and **primary contrasts** (e.g. indirect vs direct on \(\hat{p}_R\)).

## Negative controls (optional, ethics-dependent)

- **Benign** but **context-heavy** prompts (e.g. harmless fiction-writing) to show elevated verbosity is not mistaken for **\(R\)** on harmful tasks.

---

## Executable runbook (Phase 1)

Use this section as a **copy-paste checklist** after changing prompts or starting replication. All commands assume the working directory is `llm-safety-experiment/`.

### A. Freeze counts and tests (single-model artifact)

| Step | Command | Output |
| ---- | ------- | ------ |
| 1 | `python scripts/compute_significance.py` | `results/pilot/significance_stats.json` + console (χ², Fisher) |
| 2 | `python scripts/verify_artifact_chain.py` | Exit 0 if `results/pilot/results.json` matches `results/pilot/significance_stats.json` |
| 3 | `python scripts/generate_report_figures.py` | PNGs under `figures/` (optional slides) |

### B. Multi-model matrix (same `prompts.json`)

| Step | Command | Notes |
| ---- | ------- | ----- |
| 1 | `python scripts/run_all_tiers.py --dry-run` then without `--dry-run` | Nine batches (3 tiers × 3 providers); edit [`configs/tier_models.json`](configs/tier_models.json) first |
| 1b | Or: `python run_multi_model.py --tier cheap openai:gpt-4o-mini anthropic:... gemini:...` | Writes under `results/multimodel/cheap/` |
| 2 | `python analyze_results.py --results results/multimodel/cheap/results_openai_gpt-4o-mini.json` | Repeat per file; label **each model’s** response text |
| 3 | `python scripts/compute_significance.py --results <path>` | Stats next to each results file |
| 4 | `python scripts/summarize_multi_model.py` | Console summary across pilot + `results/multimodel/**/results_*.json` |

### C. Dual coding / IRR subset

| Step | Command | Notes |
| ---- | ------- | ----- |
| 1 | `python scripts/export_irr_subset.py --out irr_subset_for_rater2.json` | 100% UNSAFE + 20% of remainder (default); `--seed` for reproducibility |
| 2 | Second rater labels offline; merge `label_rater2` into rows | See [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md) |
| 3 | (Optional) Adjudicate disagreements → `label_adjudicated`; extend analysis scripts if needed | Pre-specify adjudication rule before unblinding |

### D. Intent-matched pairs (protocol only)

- Author pairs in a **separate sheet** (domain id, direct text, obfuscated text, intended harm target).
- Paired analysis is **not automated** in this repo; export labels and run McNemar / paired bootstrap offline.

### E. Optional Wave 2: stronger or alternate prompt bank

- Copy `prompts.json` to `prompts_v2.json`, document changes and keep a balanced 5×18 design if primary estimands stay comparable.
- Run with `--prompts prompts_v2.json` on [`run_experiment.py`](run_experiment.py) and [`run_multi_model.py`](run_multi_model.py).
- Present Wave 2 as a **separate** study in the report; do not silently merge counts with Wave 1.

### F. Portfolio rigor (optional but high leverage)

- **Dual coding:** use [`scripts/export_irr_subset.py`](scripts/export_irr_subset.py); report agreement and Cohen’s κ on a pre-specified subset before strong cross-model claims.
- **Labeling policy:** never treat [`scripts/seed_labels_from_pilot.py`](scripts/seed_labels_from_pilot.py) outputs as gold for multi-model adjudication—only as a pipeline stub.
