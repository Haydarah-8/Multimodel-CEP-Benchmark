# Fellowship application brief (Anthropic-style programs)

**Purpose.** Single document for **research statements**, **application uploads**, and **mentor conversations**—aligned with programs that ask for an **empirical project**, **public output** (e.g. paper), and **Python** execution. Local context: see [`fellowsprogram.md`](fellowsprogram.md) for the Anthropic Fellows **AI Safety** posting snapshot.

**Repository:** this folder (`llm-safety-experiment`). **Canonical artifact:** `results.json` + [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md).

---

## Executive summary (4 sentences)

1. **Problem.** Deployment and monitoring stacks often overweight **explicit harmful intent** and binary **UNSAFE** signals; **dual-use** and **borderline** outputs can carry substantial **risk** under a fixed rubric while **UNSAFE** stays rare.

2. **Phase 0 (completed pilot).** A **balanced 5×18** elicitation design (**n = 90**), one API model (default **`gpt-4o-mini`**), **human** SAFE / PARTIAL / UNSAFE labels; **primary estimands** per category \(c\): \(\hat{p}_U(c)\), \(\hat{p}_R(c)\) with \(R=\mathbf{1}[Y\in\{\mathrm{P},\mathrm{U}\}]\).

3. **Headline finding (this run).** Aggregate **UNSAFE 11.1%**; aggregate **risk** \(\Pr(R{=}1)\) **32.2%**; **decoupling** of risk vs UNSAFE (e.g. **indirect**: high PARTIAL, **0** UNSAFE). **Fisher (UNSAFE, roleplay vs rest):** **p ≈ 0.0037**; **escalation vs rest** not significant at α = 0.05 (**p ≈ 0.11**)—see report §3.6.

4. **Fellowship phase.** Scale evidence with **multi-model replication**, **dual coding / IRR**, optional **paired** direct-vs-obfuscated prompts, and a **pre-registered** primary display—see **4-month plan** below and [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md).

---

## Workstream framing (pick a primary emphasis in the form)

Programs often list multiple workstreams; **one** clear narrative still helps reviewers.

### Primary: AI Safety Fellows

**Fit:** **Adversarial robustness**, **AI control**, and **evaluation methodology** under **elicitation shift**—not generic “jailbreak success rate,” but **structured** category-conditional behavior under a **harm rubric**. **CEP (Contextual Evasion Pattern)** is the **analytic label** for when **risk** (\(R\)) and **strict harm** (UNSAFE) **decouple** across prespecified strategies—directly relevant to **oversight** and **monitoring** design (what to measure besides refusal on blunt asks).

**Why not overclaim:** The pilot is **single-model**, **single-rater**, **small-\(n\)**; claims are **conditional** on prompt bank and rubric. The fellowship **adds** what reviewers need: **replication**, **reliability**, and **stronger contrasts**.

### Secondary: AI Security Fellows

**Fit:** **Structured red teaming** with a **reproducible harness** (`prompts.json` → API → `results.json` → analysis). **Threat model:** **non-adaptive** taxonomy (fixed categories), **not** adaptive string optimization—complementary to Frontier-style **control evaluations** and modular red-team scaffolds.

**One line:** Same codebase; emphasize **auditability**, **repeatability**, and **clarity of scope** vs adaptive attack papers.

---

## Software engineering → empirical safety (how to say it)

- **Shipped** an end-to-end pipeline: prompt bank, API runner, labeling workflow, significance script, figure generation, long-form report with **estimands** (§2.5).
- **Transition:** from **delivery under ambiguous specs** to **measurement under explicit limits**—the fellowship fills the gap with **mentor-guided** experimental design and **compute** for **multi-model** runs.

---

## Phase 0 deliverables (already in repo)

| Deliverable | Location |
| ----------- | -------- |
| Full report + tables + lean figures | [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md) |
| Appendix figures | [`LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md`](LLM_SAFETY_EXPERIMENT_REPORT_APPENDIX.md) |
| Short brief | [`LLM_SAFETY_EXPERIMENT_SHORT.md`](LLM_SAFETY_EXPERIMENT_SHORT.md) |
| Artifact chain + model defaults | [`PROVENANCE.md`](PROVENANCE.md) |
| Extended methods (IRR, pairs, power) | [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md) |
| Results row schema (+ dual coding) | [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md) |

---

## Phase 1 infrastructure (multi-model benchmark extension — commands)

Same `prompts.json`, **one `results_*.json` per (provider, model)**, same human rubric. **Phase 1 results:** *[fill in aggregate rates / cross-model stability after you label and run significance; attach `significance_stats_*.json` paths].*

```text
# 1) API runs — set keys for providers you use: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY or GOOGLE_API_KEY
python run_multi_model.py openai:gpt-4o-mini openai:gpt-4o
python run_multi_model.py openai:gpt-4o-mini anthropic:claude-3-5-haiku-20241022 gemini:gemini-2.0-flash

# 2) Label each output (interactive)
python analyze_results.py --results results_openai_gpt-4o-mini.json
python analyze_results.py --results results_openai_gpt-4o.json
python analyze_results.py --results results_anthropic_claude-3-5-haiku-20241022.json
python analyze_results.py --results results_gemini_gemini-2.0-flash.json

# 3) Significance + optional figures per file
python scripts/compute_significance.py --results results_openai_gpt-4o-mini.json
python scripts/generate_report_figures.py --results results_openai_gpt-4o-mini.json

# 4) Quick aggregate comparison (prints provider + model when present)
python scripts/summarize_multi_model.py
```

Single model / file: `python run_experiment.py --provider openai --model gpt-4o --output results_openai_gpt-4o.json` (or default `results.json` for OpenAI + default model only)

**Dual coding:** Add optional `label_rater2` / `label_adjudicated` per [`RESULTS_SCHEMA.md`](RESULTS_SCHEMA.md); analysis scripts currently read **`label`** only unless you extend them or copy consensus into `label`.

---

## Four-month fellowship plan (indicative)

Aligned with **public output** (paper-shaped) and **external** APIs / open models. Adjust with your mentor.

| Month | Milestones |
| ----- | ---------- |
| **1** | Freeze **v1** protocol: primary **figure** (risk vs UNSAFE / category panel), **primary contrasts** (e.g. indirect vs direct on \(\hat{p}_R\)); dual-coding **plan**; multi-model **list** + budget; IR / ethics check for harmful prompts. |
| **2** | **Dual coding** on UNSAFE + stratified SAFE/PARTIAL; **κ** / agreement; resolve adjudication rules; recompute tables. |
| **3** | **Multi-model matrix** (same `prompts.json`, same rubric); optional **second model** rows in `results_*.json`; stability / failure cases. |
| **4** | Optional **paired** direct vs obfuscated set **or** power-scaled \(n_c\) on high-leverage categories; **draft paper** (methods + results + limits); polish repo + **repro** README. |

**Pre-registration (lightweight):** dated commit or markdown locking **primary display** and **contrasts** before analyzing **held-out** or **new** data—see [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md).

---

## ~60 second interview answer

“We built a **fixed** red-team **taxonomy**—five elicitation types, eighteen prompts each—ran one API model, and **human-labeled** outputs SAFE, PARTIAL, or UNSAFE. **Risk** is anything not SAFE, because dual-use harm sits in PARTIAL. The punchline is **category structure**: **UNSAFE** concentrates in **roleplay** in our pilot, but **indirect** is mostly **PARTIAL** with **zero** UNSAFE—so monitors that only fire on **UNSAFE** miss a lot of **risk**. We’re explicit about limits: **one model**, **one rater**, **small n**. The **next step**—and what I’d do in a fellowship—is **multi-model** replication and **dual coding**, maybe **paired** prompts, to turn this into **generalizable** measurement. **CEP** is just the name for that **structured** contextual-bypass pattern under our rubric.”

---

## Honest limits (say these out loud)

- Not a claim about **all** LLMs or **all** prompts—**conditional** on model, rubric, and prompt bank.
- **PARTIAL** boundaries are **subjective** without **IRR** (Phase 0).
- **Escalation** is **descriptively** high on UNSAFE; **Fisher** vs rest is **not** significant at α = 0.05 unlike **roleplay**—narrative must match §3.6.

---

## Before-submit checklist (application)

- [ ] Public **GitHub** link works; README runs to **`results.json`** path in principle.
- [ ] **Work authorization** (US/UK/Canada) and location per program rules—logistics are filters.
- [ ] **References** asked **≥2 weeks** before deadline.
- [ ] **Workstream** preference thought through (Safety vs Security vs other)—same project, different emphasis.
- [ ] Optional: `pip freeze > requirements.lock.txt` committed for strict repro ([`PROVENANCE.md`](PROVENANCE.md)).

---

## Related one-pagers

- **General hiring / portfolio card:** [`APPLICATIONS.md`](APPLICATIONS.md) (shorter; overlaps with this file).
