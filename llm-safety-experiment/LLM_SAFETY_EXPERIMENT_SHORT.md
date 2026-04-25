# Contextual Evasion Patterns in Large Language Models (short brief)

_A ~6–8 page equivalent — pointers to the full report and appendix_

> Full document: [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md) — **lean main text** (signature CEP graph + Figures 9 & 30 + tables; other diagrams live in the appendix).  
> Appendices: [`LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md`](LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md) — **Appendix A** (legacy/alternate encodings, conceptual Figs 28–34); **Appendix B** (full pipeline, method, and extended-result figures moved from the main report).  
> Data: **Pilot (main numbers):** [`results/pilot/results.json`](results/pilot/results.json), [`prompts.json`](prompts.json). **Multi-model tier run (same prompts, per-model labels):** [`results/multimodel/`](results/multimodel/) — see [`PROVENANCE.md`](PROVENANCE.md) and §6.1 of the full report; console summary [`results/multimodel/SUMMARY_CONSOLE.txt`](results/multimodel/SUMMARY_CONSOLE.txt).

---

## Abstract (condensed)

**Pilot study (n = 90, single model, single rater):** five elicitation categories × 18 prompts (direct, indirect, emotional, escalation, roleplay). Human labels SAFE / PARTIAL / UNSAFE. **CEP (Contextual Evasion Pattern)** is operationalized as category-conditional harmful compliance under **reduced explicit-intent visibility** relative to direct requests, mediated by contextual framing (see full report for formal definition). **Results:** aggregate UNSAFE 11.1%; concentration in roleplay (33.3%) and escalation (22.2%); indirect shows high PARTIAL (55.6%) with zero UNSAFE—**risk surface** (PARTIAL ∪ UNSAFE) diverges from UNSAFE-only metrics. **Not** a claim about all models; replication and IRR needed.

---

## Core figures (main text)

| Figure | Role |
| ------ | ---- |
| **Signature graph** (opening of full report) | Elicitation → labels → risk surface → CEP |
| **Figure 9** | UNSAFE % by category vs aggregate benchmark |
| **Figure 30** | **Primary:** risk surface (bars) vs UNSAFE % (line)—one panel |

Further charts (pipeline, stacked composition, Sankey, case-study schematics, §4–9 diagrams, etc.) are in **[Appendix B](LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md#appendix-b)** and **Appendix A**; optional PNG exports via **`scripts/generate_report_figures.py`**. **Per-model figures** for the tier replication live next to each multimodel JSON: `results/multimodel/<tier>/figures/<stem>/` (see full report §6.1).

---

## Hypothesis

Harmful compliance is **not uniform** across elicitation types; it **concentrates** where intent is contextually obscured (roleplay, escalation; indirect for PARTIAL / risk surface).

---

## Method (one paragraph)

Fixed prompts; one API configuration; output-based adjudication; three-level rubric with **PARTIAL** boundary documented in §2.2 of the full report (subjective; IRR not reported). **Estimands and notation** (\(Y\), risk \(R=\mathbf{1}[Y\in\{\mathrm{P},\mathrm{U}\}]\), \(\hat{p}_U(c)\), \(\hat{p}_R(c)\), \(n_c=18\)): §2.5 of the full report. **Hypothesis tests** (χ², Fisher): §3.6; frozen values in `significance_stats.json` (regenerate via `python scripts/compute_significance.py`; verify with `python scripts/verify_artifact_chain.py`).

---

## Results (bullets)

- Table 1 (overall): 61 SAFE, 19 PARTIAL, 10 UNSAFE.
- Category UNSAFE peaks: roleplay, escalation; direct/emotional: 0 UNSAFE; indirect: 0 UNSAFE, 10 PARTIAL.
- Risk surface (Table 3) high for indirect and roleplay—**Figure 30** shows gap vs UNSAFE-only story.
- §3.6 statistics: χ² independence (p ≈ 7.5×10⁻⁷); Fisher **roleplay vs rest** on UNSAFE (p ≈ 0.0037); **escalation vs rest** not significant at α = 0.05 (p ≈ 0.11)—see `significance_stats.json` and full report.

---

## Mechanisms

**Interpretive only** (not measured internals): narrative framing, incremental escalation, dual-use pretext—aligned with case studies in §3.5 of the full report.

---

## Limitations

Small **n**; **primary** narrative is single-model pilot; multi-model tier JSON in `results/multimodel/` is a **separate** corpus (§6.1 full report); single rater; PARTIAL fuzziness; no IRR—frame as **pilot** / **hypothesis-generating** unless citing tier files explicitly.

---

## Citation

Use the same artifact paths as the repository; cite **full report** for figures beyond the three above.
