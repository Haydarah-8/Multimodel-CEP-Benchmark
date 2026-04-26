# Category stress indices (pre-specified)

Scripts: [`scripts/compute_category_stress_indices.py`](scripts/compute_category_stress_indices.py), optional figure [`scripts/plot_category_stress.py`](scripts/plot_category_stress.py).

## Inputs

One fully labeled [`results/pilot/results.json`](results/pilot/results.json) or `results/multimodel/.../results_*.json` (90 rows, five categories × 18 prompts).

## Definitions

Let \(\hat p_U(c)\) = UNSAFE rate in category \(c\), \(\hat p_R(c)\) = (PARTIAL ∪ UNSAFE) rate. Let **direct** be the baseline stratum. Use \(\varepsilon = 10^{-9}\) in denominators to avoid division by zero.

### Sensitivity vs direct

For \(c \in \{\texttt{emotional}, \texttt{indirect}, \texttt{escalation}\}\):

- \(\mathrm{RR}^{\mathrm{unsafe}}_c = \hat p_U(c) / \max(\hat p_U(\texttt{direct}), \varepsilon)\)
- \(\mathrm{RR}^{\mathrm{risk}}_c = \hat p_R(c) / \max(\hat p_R(\texttt{direct}), \varepsilon)\)

When \(\hat p_U(\texttt{direct})=0\), **`RR_unsafe_vs_direct` is JSON `null`** (baseline-zero rule) so outputs are not dominated by \(\varepsilon\) in the denominator; see `RR_notes` in the JSON. Same for risk when \(\hat p_R(\texttt{direct})=0\).

### Roleplay amplification factor

\[
A_{\mathrm{roleplay}} = \frac{\hat p_U(\texttt{roleplay})}{\max(\hat p_U(\texttt{aggregate}),\varepsilon)}
\]

where \(\hat p_U(\texttt{aggregate})\) is the overall UNSAFE rate (same object as `roleplay_vs_aggregate_baseline` in [`significance_stats.json`](results/pilot/significance_stats.json)).

### Coercion / pressure vulnerability index (CPI)

**Operationalization:** “Coercion” in this prompt bank is indexed by the **escalation** elicitation category (incremental / staged framing), not a separate metadata label.

- \(\mathrm{CPI}_{\mathrm{risk}} = \hat p_R(\texttt{escalation}) - \hat p_R(\texttt{direct})\)
- \(\mathrm{CPI}_{\mathrm{unsafe}} = \hat p_U(\texttt{escalation}) - \hat p_U(\texttt{direct})\)

## Commands

```bash
cd llm-safety-experiment
python scripts/compute_category_stress_indices.py --results results/pilot/results.json
python scripts/plot_category_stress.py --indices-json results/pilot/category_stress_indices.json
```

## Interpretation

These are **descriptive** scalars under a fixed rubric; causal claims require design features not in the pilot (e.g. intent-matched pairs). Pair with **Cramér’s V** and **Wilson CIs** in extended [`significance_stats.json`](results/pilot/significance_stats.json) from [`scripts/compute_significance.py`](scripts/compute_significance.py).
