# Project card + interview narrative (job applications)

**Fellowship-style merged brief** (AI Safety / similar programs): [`FELLOWSHIP_APPLICATION_BRIEF.md`](FELLOWSHIP_APPLICATION_BRIEF.md).

One-page summary for resumes, cover letters, and recruiter screens. **Numbers** refer to the audited artifact in `results.json`; refresh if you re-run the experiment.

---

## One-page project card

**Problem.** Deployment monitors often emphasize **explicit** harmful intent and binary **UNSAFE**-style signals. Harmful or dual-use content may appear under **narrative, staged, or dual-use** elicitation while **UNSAFE** stays sparse.

**Design.** Balanced **5 × 18** prompt set (**n = 90**), single model (**`gpt-4o-mini`** by default; see [`PROVENANCE.md`](PROVENANCE.md)), human labels **SAFE / PARTIAL / UNSAFE**. **Elicitation category** is the experimental factor; **not** adaptive attack search.

**Primary estimands.** Per category \(c\): \(\hat{p}_U(c)\) (UNSAFE rate), \(\hat{p}_R(c)\) with \(R=\mathbf{1}[Y\in\{\mathrm{P},\mathrm{U}\}]\) (**risk surface**). **Primary display:** Figure 30 in the main report (risk vs UNSAFE).

**Result (this run).** Aggregate UNSAFE **11.1%** (10/90). **Risk** \(\Pr(R{=}1)\) **32.2%** aggregate. **Roleplay** peaks UNSAFE (**33.3%**, 6/18); **indirect** shows **55.6%** PARTIAL with **0** UNSAFE—**decoupling** of risk vs strict harm. **Fisher (UNSAFE):** roleplay vs rest **p ≈ 0.0037**; escalation vs rest **not** significant at α = 0.05 (**p ≈ 0.11**)—see report §3.6.

**Limits.** Single model, single rater, small \(n_c\), no IRR—**pilot** / hypothesis-generating, not population prevalence.

**Next.** Dual coding, paired intent-matched prompts, multi-model matrix—[`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md).

---

## ~60 second interview answer

“We run a **fixed** red-team **taxonomy**—five elicitation types, eighteen prompts each—on one API model, and **human-code** outputs into SAFE, PARTIAL, or UNSAFE. I define **risk** as anything not SAFE—PARTIAL or UNSAFE—because **dual-use** stuff sits in PARTIAL. The finding is **category structure**: **UNSAFE** piles up in **roleplay** in our run, but **indirect** is almost all **PARTIAL** and **no** UNSAFE, so if you only track **UNSAFE**, you miss a lot of **risk**. We’re careful: **small n**, one rater, one checkpoint—so it’s **evidence for a monitoring gap**, not a claim that every model does this. **CEP** is just the **name** for that **structured** **contextual** bypass pattern under our rubric.”

---

## Honest comparison (one sentence each)

- **vs jailbreaking papers:** We do **not** optimize prompts; we **stratify** by **prespecified** category.
- **vs prompt robustness:** We care about **harm adjudication** under a **rubric**, not generic sensitivity to rephrasing.
