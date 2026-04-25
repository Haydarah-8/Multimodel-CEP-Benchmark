# Prompt for external AI figure generation

Copy and adapt this brief when asking another model or designer to produce **publication-style** visuals for the LLM safety / CEP paper.

---

Create advanced, publication-quality visualizations for a research paper on **LLM safety** and **contextual evasion patterns (CEP)**.

**Focus on:**

- Flow of harmful compliance (**SAFE → PARTIAL → UNSAFE**) and where alignment “leaks” under framing
- **Hidden risk** (PARTIAL ∪ UNSAFE) vs **observed harm** (UNSAFE only)
- **Category-based behavioral fingerprints** (direct, indirect, emotional, escalation, roleplay)
- **Mechanistic diagrams** (objective tensions, boundary drift, multi-turn hypotheticals)—not only bar charts
- Optional: **causal or system-level** sketches that stay clearly labeled as interpretive, not measured internals

**Style:**

- **Dark theme**, minimal academic look, high legibility
- Prefer **interpretability** over decoration
- Avoid generic bar charts unless they are combined with structure (e.g., uncertainty, dual metrics, or narrative captions)

**Data:** When numbers are needed, use the labeled run in `results.json` (90 prompts, five categories × 18) or the tables in `LLM_SAFETY_EXPERIMENT_REPORT.md`.

---

This repo already ships Mermaid figures in the report and PNG exports from `scripts/generate_report_figures.py`; use this prompt when you want **additional** assets (slides, posters, or alternate aesthetics).
