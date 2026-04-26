# Cross-model normalization (Tier 3)

Descriptive quantities for comparing models **beyond raw** \(\hat P(\texttt{unsafe}\mid c)\). Not a causal adjustment and **not** a substitute for logits or calibrated harm scores.

See [`scripts/build_multimodel_rate_matrix.py`](scripts/build_multimodel_rate_matrix.py) (embedded `per_file[].normalization` and top-level `excess_p_unsafe_vs_direct`).

## Definitions

| Quantity | Symbol / formula |
| -------- | ---------------- |
| Baseline refusal tendency | \(B_m = \hat P(\texttt{safe} \mid \texttt{direct})_m\). If \(n_{\text{direct}}=0\), fallback: global \(\hat P(\texttt{safe})_m\) over all labeled rows in that file. |
| Direct-stratum unsafe | \(\hat P(\texttt{unsafe}\mid \texttt{direct})_m\) (same fallback behavior for the unsafe rate when direct is empty). |
| Excess unsafe vs direct | \(\Delta^U_{m,c} = \hat P(\texttt{unsafe}\mid c)_m - \hat P(\texttt{unsafe}\mid \texttt{direct})_m\). Undefined (JSON `null`) when \(n_{m,c}=0\) or baseline is missing. |
| Verbosity proxy | \(\log(1 + |\texttt{response}|)\) per labeled row. Rows whose `response` starts with `ERROR:` are **excluded** from length summaries. Reported per file: median, Q1, Q3, and count of rows used. |

## Outputs

- Full bundle: [`figures/multimodel/signature_rate_matrix.json`](figures/multimodel/signature_rate_matrix.json) (default `--out`) includes `p_hat`, `n`, `excess_p_unsafe_vs_direct`, and `per_file` details.
- Optional slim file: pass `--out-normalization figures/multimodel/normalization_layer.json` for normalization + verbosity only.

## Figures

- Raw rates: `python scripts/plot_multimodel_signature_heatmap.py --matrix-json figures/multimodel/signature_rate_matrix.json --kind raw`
- Excess vs direct (diverging): `--kind excess_vs_direct`

## Limitations

- Verbosity is a coarse correlate of model style; it does not isolate “pressure” on the assistant from the prompt text.
- \(\Delta^U\) is defined relative to the **direct** elicitation stratum in this design, not an external population baseline.
