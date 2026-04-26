# Decision-boundary audit (Tier 2)

**Descriptive** cross-model discordance on the **same** prompt `id`, using human ordinal labels only. This is **not** an estimated classifier boundary: there are no token logits or continuous harm scores.

See [`scripts/decision_boundary_audit.py`](scripts/decision_boundary_audit.py).

**Mutation waves:** when results include `parent_prompt_id`, `mutation_kind`, and `mutation_variant`, the same ordinal machinery applies more naturally if you align cells with [`scripts/compute_boundary_stability.py`](scripts/compute_boundary_stability.py) `cross-model` (wave-aware `align_key`) and measure **within-model** dispersion across variants with `cross-variant`. Spec: [`BOUNDARY_STABILITY.md`](BOUNDARY_STABILITY.md).

## Ordinal coding

For aggregation only: `safe` → 0, `partial` → 1, `unsafe` → 2.

## Per-prompt summaries (complete rows)

For each `id` where **every** model column has a non-empty label:

- **range** = max(score) − min(score)
- **variance** = population variance of scores across models
- **majority_label** = modal label (ties broken lexicographically: `partial`, `safe`, `unsafe`)

**Boundary prompts**

- `range >= 1`: at least one ordinal step of disagreement
- `range == 2`: some model `safe` and another `unsafe` (polar disagreement)

## Pairwise “switches” (directed)

For ordered pair (model A, model B), count occurrences of each label pair \((\ell_A, \ell_B)\). This is the **comparator** analogue of “SAFE→PARTIAL” (not a within-model trajectory on the same prompt as difficulty increases).

## Consistency

- **majority_fraction**: fraction of models matching the majority label (mean over prompts)
- **Fleiss’ κ** (fixed \(k=3\) categories, one row per prompt with complete ratings): standard formula on category counts per item

## Marginal shift (single model)

Optional block: for each model stem, adjacent-category differences in \(\hat P(\texttt{partial})\) and \(\hat P(\texttt{unsafe})\) along `CAT_ORDER` (same as [`compute_significance.py`](scripts/compute_significance.py)). This describes **where** label mass moves between strata, not a per-prompt threshold.

## Methods blurb (example)

> We audited decision-boundary heterogeneity by aligning models on identical prompt ids and mapping labels to an ordinal safe–partial–unsafe scale for descriptive discordance (range, pairwise label transitions). We report Fleiss’ κ and majority agreement across models. We do not estimate a latent refusal threshold per model because continuous scores were unavailable.

## Commands

```bash
cd llm-safety-experiment
python scripts/decision_boundary_audit.py
python scripts/decision_boundary_audit.py --multimodel-root results/multimodel/cheap --out-json results/multimodel/cheap/boundary_audit.json
python scripts/decision_boundary_audit.py --paired-csv results/multimodel/paired_labels_wide.csv --out-csv-discord results/multimodel/high_discordance_ids.csv
```

**Outputs:** `--out-json` writes a **slim** summary (pairwise counts, marginal shifts, Fleiss κ; per-prompt rows omitted). The script also writes `<stem>_full.json` beside it with `per_prompt_complete` for auditing.
