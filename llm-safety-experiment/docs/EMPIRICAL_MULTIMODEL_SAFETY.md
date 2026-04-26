# Empirical multimodel safety study (structured red-team corpus)

**Navigation:** For the primary reader-facing document, see [`RESEARCH_MONOGRAPH.md`](RESEARCH_MONOGRAPH.md). For a **multimodel-first** manuscript, see [`MULTIMODEL_MANUSCRIPT.md`](MULTIMODEL_MANUSCRIPT.md). This file remains an alternate paper-style draft.

**Title (working).** Contextual Evasion Patterns Across API Tiers: A Fixed-Prompt, Multimodel Compliance Audit

**Abstract.** We evaluate harmful-request compliance under a **prespecified five-way elicitation taxonomy** (direct, indirect, emotional, escalation, roleplay) with **balanced replication** across **OpenAI**, **Anthropic**, and **Google Gemini** APIs. For each configuration we collect **n = 90** single-turn assistant outputs and assign **SAFE / PARTIAL / UNSAFE** labels under a fixed rubric. We report **stratum-conditional** rates of unsafe output and of **risk** (partial or unsafe), **excess unsafe vs direct** as a normalization, and **cross-model** fingerprints (PCA, refusal–risk frontier). **Tiering caveat:** Gemini **mid** and **expensive** tiers both call **`gemini-2.5-pro`** in our configuration; we therefore have **nine labeled runs** but **eight unique provider×model-id pairs**. Results are **descriptive and associational**—suitable for **evaluation methodology** and **monitoring hypotheses**, not for causal claims about training or internals.

---

## 1. Introduction

Alignment evaluations often emphasize **refusal under explicit harm**. Production traffic, however, includes **context-rich** requests: narrative framing, incremental escalation, and ostensibly benign cover stories. We ask whether **elicitation stratum** shifts compliance in a **replicable** way across commercial APIs.

**Contributions.**

1. A **frozen prompt bank** and **label schema** enabling **exact replication** and **cross-model comparison** on identical inputs.
2. A **3×3 experimental layout** (tier × provider) with explicit documentation of **Gemini tier equivalence** (same model id on two tiers).
3. **Open scripts** for **artifact auditing**, **significance** (pilot), **rate matrices**, **combined figures**, and **interpretability** plots.

## 2. Related work (pointer)

Structured red-teaming, harm taxonomies, and jailbreak literature are large; this corpus is **not** an adaptive attack search. It is a **fixed-factor** design aligned with **empirical safety** and **robustness** themes: **where** models fail under **controlled** elicitation diversity.

## 3. Method

### 3.1 Prompts

- **90 prompts** per run: 5 strata × 18 prompts.
- Strata: **direct**, **indirect**, **emotional**, **escalation**, **roleplay** (see main codebase `prompts.json`).

### 3.2 Models and tiers

Model ids are listed in [`configs/tier_models.json`](../configs/tier_models.json). **Gemini:** cheap = `gemini-2.5-flash`; mid = expensive = **`gemini-2.5-pro`** (documented in config `_comment`).

### 3.3 Labels

Human-assigned **SAFE**, **PARTIAL**, **UNSAFE** per response (definitions in [`LLM_SAFETY_EXPERIMENT_REPORT.md`](../LLM_SAFETY_EXPERIMENT_REPORT.md)). **Risk** indicator: \(R = 1\) iff label ∈ {PARTIAL, UNSAFE}.

### 3.4 Estimands

For stratum \(c\): \(\hat p_{\text{unsafe}}(c)\), \(\hat p_{\text{risk}}(c)\), with **\(n_c = 18\)**. **Excess unsafe vs direct:** \(\hat p_{\text{unsafe}}(c) - \hat p_{\text{unsafe}}(\text{direct})\).

### 3.5 Statistics

Pilot corpus: χ² and Fisher tests via `scripts/compute_significance.py` (see main report §3.6). Multimodel: primary displays are **rates + CIs implicit in design** (Wilson available per stratum in extended tooling); **multiplicity** is not exhaustively corrected—report as **exploratory** unless pre-registered.

## 4. Results (figure-driven)

Regenerate all cited multimodel figures with:

```bash
python scripts/reproduce_main_figures.py
```

Key outputs under **`figures/multimodel/`**:

| Output | Role |
|--------|------|
| `combined_signature_unsafe_heatmap.png` | Nine runs × strata, \(\hat p_{\text{unsafe}}\) |
| `combined_signature_excess_vs_direct.png` | Excess unsafe vs direct stratum |
| `combined_signature_risk_heatmap.png` | \(\hat p_{\text{risk}}\) |
| `combined_9panel_unsafe_by_category.png` | 3×3 tier × provider bar panels |
| `combined_safety_frontier.png` | Refusal vs risk (fingerprints) |
| `combined_fingerprint_pca.png` | 2D PCA of fingerprint features |

## 5. Robustness extensions (optional arms)

- **Mutations:** [`PROMPT_MUTATIONS.md`](../PROMPT_MUTATIONS.md)
- **Boundary stability:** [`BOUNDARY_STABILITY.md`](../BOUNDARY_STABILITY.md)
- **Associational proxies:** [`CAUSAL_PROXIES.md`](../CAUSAL_PROXIES.md) (naming is legacy; claims are **non-causal**)

## 6. Limitations

1. **Small n per stratum** → wide uncertainty; categories are **not** independent industrial prevalence estimates.
2. **Nine runs, eight unique Gemini SKUs** on mid/expensive as noted.
3. **Associational** proxy and frontier analyses; no **instrumental** identification.
4. **Human labels** without full dual-coding unless IRR protocol is executed.
5. **Single-turn**; no tool use or multi-turn coercion.

## 7. Ethics and use

Prompts are for **authorized safety research** only. Do not use outputs to harm.

## 8. Reproducibility

- [`ARTIFACT_INTEGRITY.md`](ARTIFACT_INTEGRITY.md)
- [`PROVENANCE.md`](../PROVENANCE.md)
- [`README.md`](../README.md)
