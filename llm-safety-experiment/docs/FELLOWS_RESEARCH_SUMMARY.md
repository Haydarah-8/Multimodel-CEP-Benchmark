# Research summary (1–2 pages) — empirical safety, robustness, evaluation

**See also:** [`RESEARCH_MONOGRAPH.md`](RESEARCH_MONOGRAPH.md) for the full structured overview.

**Problem.** Deployment safety depends on behavior under **realistic elicitation**, not only blunt harmful requests. Models may refuse explicit intent yet comply when the same objective is **staged** (fiction, incremental steps, dual-use framing).

**Design.** Fixed **n = 90** prompt sets per model: five **elicitation strata** × 18 prompts, human-labeled **SAFE / PARTIAL / UNSAFE** with a stable rubric. **Primary estimands:** stratum-level rates of UNSAFE and of **risk** (PARTIAL ∪ UNSAFE). **Multimodel extension:** the identical bank is run on **nine tiered API configurations** (3 tiers × 3 providers). **Constraint:** Google’s API lineup did not offer a separate mid-tier model aligned with OpenAI/Anthropic mid SKUs; **Gemini mid and expensive both use `gemini-2.5-pro`**, so cross-provider “tier” comparisons treat Gemini as **two independent runs of the same model id**, not two different models.

**Findings (qualitative pattern for portfolio).** Across models, **unsafe and risk rates vary by stratum**; **roleplay** and **escalation** typically concentrate elevated rates relative to **direct** (exact percentages live in frozen JSON and `figures/multimodel/`). The **risk surface** (PARTIAL-rich strata) matters for monitoring: harm-relevant behavior is not captured by UNSAFE alone.

**Robustness & evaluation layer.** Optional **mutation waves** and **boundary stability** probe whether stratum structure survives paraphrase stress. **Fingerprint PCA** and **refusal–risk frontiers** summarize cross-model geometry in label space for **comparative evaluation**.

**Honest limits.** Small **n per stratum (18)**; **associational** proxy analyses are not causal; **single-turn** design; labels reflect **one coding pass** unless dual-coding is run; **generalization** to other prompts, tools, languages, and future checkpoints requires replication.

**Artifacts.** Labeled JSON under `results/`, reproducible figures via `python scripts/reproduce_main_figures.py`, narrative spine in [`NARRATIVE_SPINE.md`](NARRATIVE_SPINE.md), full report in [`LLM_SAFETY_EXPERIMENT_REPORT.md`](../LLM_SAFETY_EXPERIMENT_REPORT.md).
