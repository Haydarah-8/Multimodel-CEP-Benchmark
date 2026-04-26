# Multi-model results (tiered layout)

See **[`RESULTS_LAYOUT.md`](RESULTS_LAYOUT.md)** for directory conventions.

## Labeling status (read this first)

**Human adjudication per model response** is required for defensible cross-model statistics. Scripts such as [`scripts/seed_labels_from_pilot.py`](scripts/seed_labels_from_pilot.py) copy pilot labels by prompt `id` only to unblock tooling—they are **not** gold labels for each provider’s text.

Use [`scripts/clear_labels.py`](scripts/clear_labels.py) then [`analyze_results.py`](analyze_results.py) per file when you are ready to label seriously.

## Tier × provider layout

| Tier | OpenAI | Anthropic | Gemini |
|------|--------|-----------|--------|
| cheap | `gpt-4o-mini` | `claude-3-haiku-20240307` | `gemini-2.5-flash` |
| mid | `gpt-4o` | `claude-3-sonnet-20240229` | `gemini-2.5-pro` |
| expensive | `gpt-4.1` | `claude-3-opus-20240229` | `gemini-2.5-pro` |

`gemini-1.5-flash` / `gemini-1.5-pro` ids return 404 on current `generateContent`. Mid and expensive share the same Gemini model id; tier differentiation is via OpenAI and Anthropic. See `_comment` in [`configs/tier_models.json`](configs/tier_models.json).

Authoritative model strings: [`configs/tier_models.json`](configs/tier_models.json). **Batch runner:** `python scripts/run_all_tiers.py` (use `--dry-run` first).

## Migrated artifacts (legacy runs)

Successful API outputs from earlier flat-root runs were placed under:

- `results/multimodel/cheap/results_gemini_gemini-2.5-flash.json` + paired `significance_stats_*.json`
- `results/multimodel/mid/results_openai_gpt-4o.json` + paired stats
- `results/multimodel/expensive/results_anthropic_claude-3-opus-20240229.json` + paired stats

Failed or deprecated runs remain in `results/archive/legacy_flat/`.

## Pilot (single-model)

Frozen pilot: `results/pilot/results.json` — primary report numbers refer to this corpus unless you publish a new wave.

## After labeling (stats, verify, figures)

For each `results_<provider>_<model>.json` that has **every** row labeled `safe` / `partial` / `unsafe`, run the batch helper (from `llm-safety-experiment/`):

```bash
python scripts/postprocess_multimodel_tiers.py
python scripts/postprocess_multimodel_tiers.py --also results/pilot/results.json
```

This writes `significance_stats_<stem>.json` next to the results file, checks consistency with `scripts/verify_artifact_chain.py`, and writes PNGs under `results/multimodel/<tier>/figures/<stem>/` beside that JSON (pilot: `results/pilot/figures/results/`). Use `--skip-figures` or `--skip-sankey` if needed (Kaleido Sankey can hang on some hosts; `MPLBACKEND=Agg` recommended for headless runs).

**Cross-model console summary** (after postprocess): `python scripts/summarize_multi_model.py` — saved copy: [`results/multimodel/SUMMARY_CONSOLE.txt`](results/multimodel/SUMMARY_CONSOLE.txt).

**Rubric:** [`LABEL_RUBRIC.md`](LABEL_RUBRIC.md). **Validity / robustness:** [`FAILURE_MODE_CODEBOOK.md`](FAILURE_MODE_CODEBOOK.md), [`ROBUSTNESS_HARM_OPERATIONALIZATIONS.md`](ROBUSTNESS_HARM_OPERATIONALIZATIONS.md), [`scripts/export_paired_error_table.py`](scripts/export_paired_error_table.py), [`scripts/compute_irr_kappa.py`](scripts/compute_irr_kappa.py).
