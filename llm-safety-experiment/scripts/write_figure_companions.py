# -*- coding: utf-8 -*-
"""Write PhD-style companion .md files next to each figure asset.

Each companion has numbered sections (purpose, Mermaid pipeline diagram, data
lineage, reproduction, interpretation, limitations/ethics) fed by five prose
blocks. Run: python scripts/write_figure_companions.py

Pairs each `figures/**/*.png`, `figures/**/*.html`, and per-run
`results/**/fig_model_fingerprint_curves.png` with a sibling `.md`, plus
`figures/FIGURE_COMPANIONS.md` index.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent

COMPANIONS: dict[str, tuple[str, str, str, str, str]] = {}


def add(rel: str, *paragraphs: str) -> None:
    if len(paragraphs) != 5:
        raise ValueError(rel, len(paragraphs))
    COMPANIONS[rel] = paragraphs


# --- Pilot / report figures (figures/*.png) ---------------------------------

add(
    "figures/fig1_unsafe_rate_by_category.png",
    "This figure is a pilot-phase bar chart for the Multimodel-CEP-Benchmark: it encodes how often model outputs are adjudicated as **UNSAFE** when prompts are drawn from each elicitation category in the fixed pilot bank. "
    "Categories are discrete buckets in the project’s harm-elicitation taxonomy (for example, classes of requests that stress different policy edges); within each category the plot shows one bar per conversational **stratum** or framing when the design crosses multiple elicitation styles. "
    "The height of each bar is simply the count of UNSAFE-labeled completions divided by the number of audited prompts in that (category, stratum) cell, so the vertical axis is interpretable as an empirical failure rate under the rubric rather than a model self-report. "
    "A horizontal **benchmark** line marks the overall UNSAFE rate on the same labeled table, aggregating across categories according to the script’s weighting; categories whose bars extend above that line are disproportionately contributing to unsafe outcomes in this bank, and bars below the line indicate relatively lower unsafe prevalence for this snapshot. "
    "Because the plot collapses SAFE and PARTIAL into the complement of UNSAFE, it emphasizes catastrophic policy violations only; readers who care about borderline behavior should also open the stacked composition and risk heatmaps.",
    "All rates are computed from **post-hoc labels** applied to stored completions, not from provider safety classifiers. "
    "The adjudication protocol is written in `LABEL_RUBRIC.md`: UNSAFE means a completion is treated as fully violating the project’s policy criteria for that prompt class, while PARTIAL captures incomplete refusals, hedged compliance, or other edge cases that stop short of a full UNSAFE verdict. "
    "The pilot JSON (path recorded in `PROVENANCE.md`) is the authoritative row-level source; any figure is only as stable as the commit or artifact hash you pinned. "
    "If multiple annotators or models participated in labeling, the repository should document consensus rules—when in doubt, trace a single category’s bar back to the underlying prompt IDs and raw model strings before citing a number externally. "
    "This chart is **conditional on the category**: it answers “within prompts we chose to represent class X, how often did this model produce UNSAFE text?” not “how common is harm on the open internet.”",
    "Regenerate the asset from `llm-safety-experiment/` with `python scripts/generate_report_figures.py`, passing `--results` if your checkout places the pilot JSON outside the default. "
    "`python scripts/generate_report_figures.py --help` lists figure output directory overrides (`--figures-dir`) and optional skips. "
    "For servers without a display, set `MPLBACKEND=Agg` so matplotlib never tries to open a GUI backend. "
    "After a run, compare this PNG to `fig_unsafe_rate_by_category_wilson_ci.png`: both should tell a consistent story because they share the same cell counts, differing only in whether uncertainty is drawn. "
    "If numbers disagree with a table in a paper draft, re-run `scripts/verify_artifact_chain.py` (when present) and confirm you are not mixing an old JSON with a new figure export.",
    "When reading the chart, prioritize **relative** patterns (which categories spike under which stratum) over precise percentage point comparisons unless you also consult intervals or raw counts. "
    "The pilot uses a modest number of prompts per category per stratum (historically on the order of 18), so sampling noise can move bars noticeably if you resampled prompts from the same generative process; a category that looks slightly worse than another may not stay that way under bootstrap replication. "
    "Do not infer causal effects of “making prompts more subtle” from bar differences alone unless the experimental design explicitly supports that estimand and you pre-specify tests appropriate to paired prompts. "
    "Finally, remember that **high UNSAFE in a category** can reflect a difficult benchmark slice rather than “the model is globally malicious”; the ethical obligation is to describe behavior under the bank, not to sensationalize.",
    "The pilot bank deliberately includes harmful or sensitive request templates to stress policies; raw prompts, completions, and labels may be regulated or harmful if mishandled. "
    "Follow `SECURITY.md` for storage, access control, and redaction before sharing figures or excerpts. "
    "If you publish aggregate rates, avoid pairing them with verbatim prompts that enable real-world misuse; prefer high-level category names and cite the artifact DOI or repository version instead of leaking prompt text. "
    "Institutional review or vendor terms may further restrict redistribution—this documentation does not replace legal review.",
)

add(
    "figures/fig_unsafe_rate_by_category_wilson_ci.png",
    "This figure is the **interval-augmented** sibling of the primary UNSAFE bar chart: for each (category, stratum) cell it still plots the point estimate of the UNSAFE proportion, but it also overlays (or adjoins) **approximate 95% Wilson score confidence intervals** for a binomial proportion. "
    "Wilson intervals are preferred to naive Gaussian intervals when n is small or when the true rate is near zero or one, because they remain bounded in [0,1] and have better coverage behavior in those regimes. "
    "Visually, wider intervals warn that the pilot sample is informative but not definitive; narrow intervals indicate either a larger effective n or an estimate far from 0.5 where variance is naturally smaller. "
    "The chart is still purely descriptive of the audited benchmark—it does not, by itself, implement multiple-testing correction across the many cells you may be eyeballing simultaneously.",
    "Every interval is computed from the same contingency table as `fig1_unsafe_rate_by_category.png`: each cell has a count of UNSAFE labels and a denominator equal to the number of evaluated prompts in that cell after any quality filters documented in `PROVENANCE.md`. "
    "The semantics of “UNSAFE” are unchanged from `LABEL_RUBRIC.md`; if the rubric is revised, both the point estimates and intervals must be recomputed from relabeled JSON. "
    "If your pipeline emits `significance_stats.json` or similar, that file may contain prespecified hypothesis tests that complement these marginal intervals; do not treat the figure as replacing those tests if your preregistration called for McNemar, Fisher, or other paired structure.",
    "Rebuild with `python scripts/generate_report_figures.py` from `llm-safety-experiment/`, using the same `--results` path you used for the point-estimate figure. "
    "Confirm that matplotlib and the project’s pinned scientific stack import cleanly in your environment; CI logs in `.github/workflows/` may show the exact command line used in automation. "
    "When drafting text, quote interval endpoints from the data generation script or from exported CSV if available, not from pixel measurements of the PNG. "
    "If you need simultaneous coverage across many cells, consult a statistician: the default plotting script typically does **not** apply Benjamini–Hochberg or other multiplicity adjustments unless explicitly documented.",
    "Interpret **overlap** of intervals cautiously: two cells whose intervals overlap may still differ meaningfully if a paired test on the same prompts rejects equality; conversely, non-overlap of marginal intervals does not automatically imply a significant paired difference. "
    "Always ask whether prompts are **paired** across strata (same template under two framings) or **independent** draws; the right inferential target depends on that structure. "
    "Cells with zero UNSAFE still carry uncertainty—do not treat a bar at 0% as proof of perfect safety—and cells at 100% UNSAFE are rare but possible on tiny n and should trigger a manual audit of those prompt IDs.",
    "Raw results may contain model outputs that violate policy or law if republished; treat the JSON and any derivative figures as sensitive. "
    "Follow `SECURITY.md` and your organization’s data-handling rules; anonymize or aggregate before external distribution. "
    "When showing intervals in presentations, avoid displaying exact prompts alongside extreme failure rates unless necessary and approved.",
)

add(
    "figures/figure2_label_distribution_stacked.png",
    "This stacked bar chart is a **composition** view: for every elicitation category on the horizontal axis, the vertical extent of the bar is normalized to 100% and partitioned into colored segments for SAFE, PARTIAL, and UNSAFE adjudications. "
    "Unlike the UNSAFE-only bar chart, it forces the reader to confront how much of the behavioral mass sits in PARTIAL—the rubric’s bucket for policy-edge behavior that is not a clean refusal but also not a full UNSAFE completion. "
    "The visual metaphor is “within the prompts we tested for this category, what fraction of model behavior landed in each adjudication class?” "
    "Because the normalization is per category, you can compare **shapes** across categories even when raw prompt counts differ, though you should still consult tables if one category has far fewer prompts than another.",
    "The input data are identical to the other pilot figures: one row per (prompt, stratum, model) evaluation after labeling. "
    "`LABEL_RUBRIC.md` defines how annotators or automated judges map free text into the three-way outcome; any ambiguity in PARTIAL versus UNSAFE will directly change the colored areas. "
    "If the repository tracks adjudicator agreement or confidence, those diagnostics belong in methods text, not in this PNG. "
    "When comparing to multimodel results, note that multimodel composition plots live under `figures/multimodel/` and aggregate across the nine-run grid rather than a single pilot snapshot.",
    "Regenerate via `python scripts/generate_report_figures.py` with the same results path as the rest of the pilot bundle. "
    "If colors look wrong in a draft paper, adjust the matplotlib style in the generator rather than recoloring the bitmap in an image editor, so figures stay reproducible. "
    "For print, verify that the legend distinguishes SAFE/PARTIAL/UNSAFE for grayscale readers (hatching or labels may be required).",
    "A **tall UNSAFE slice** is the headline failure mode, but a **tall PARTIAL slice** often explains why UNSAFE-only metrics understate operational risk: models may comply in a way that is brittle, vague, or easy to push over the line in follow-up turns. "
    "Comparing categories, look for “PARTIAL-heavy” stacks where UNSAFE is modest—those are prime candidates for qualitative error analysis and for risk metrics that union PARTIAL with UNSAFE. "
    "Do not interpret a tiny sliver as exact zero risk unless n is large; very thin slices can still represent multiple prompts.",
    "Denominators per category matter: with small n, apparent differences in composition can be driven by one or two prompts. "
    "Export counts to a table for the paper’s appendix when reviewers ask for statistical testing. "
    "Ethically, stacked bars can look dramatic even when absolute harm is bounded by the artificial bank—contextualize with benchmark scope. "
    "Handle underlying text per `SECURITY.md`.",
)

add(
    "figures/fig_category_risk_profile_heatmap.png",
    "This heatmap is a **contingency-table visualization** for the pilot audit: rows typically correspond to elicitation categories (or strata, depending on the script version) and columns to adjudicated outcomes SAFE, PARTIAL, and UNSAFE—or analogous groupings. "
    "Each cell’s numeric value is an empirical conditional probability or percentage: “given a prompt from this category, how often did we observe this label?” "
    "Color intensity maps magnitude, so your eye can sweep for hot spots where UNSAFE or PARTIAL concentrates. "
    "Unlike time-series heatmaps, there is no temporal axis; order along a dimension is for readability and should be documented if you reorder categories for a talk.",
    "The heatmap contains **no model logits or token probabilities**; it is entirely a summary of human- or rubric-driven labels applied to completions. "
    "That distinction matters for reviewers who might mistake color intensity for classifier confidence. "
    "All category definitions and label semantics are frozen by `LABEL_RUBRIC.md` and the benchmark specification; if you subset prompts (for example dropping malformed JSON rows), say so in methods because conditioning changes the implied estimand. "
    "For exact cell values, always prefer the JSON or a CSV emitted alongside the figure; rasterized PNGs are not a data interchange format.",
    "Build the figure with `python scripts/generate_report_figures.py`, ensuring the results file matches the commit you reference in the paper. "
    "If you maintain multiple pilot variants (different random seeds or prompt draws), never mix JSON from one variant with a figure title that claims another. "
    "For accessibility, consider publishing the numeric table for screen-reader users; colorblind-friendly colormaps should be selected in code, not assumed.",
    "When reading the heatmap, look for **rows** where UNSAFE dominates versus rows where PARTIAL dominates; those patterns suggest different failure mechanisms worth separate discussion. "
    "Be cautious about comparing cell colors across rows if denominators differ sharply—rare categories with small n can look noisy. "
    "If you apply row normalization in a different script fork, annotate whether colors encode fractions within a category or global shares, because the interpretation changes.",
    "Heatmaps are persuasive but easy to over-interpret; pair them with uncertainty or raw counts before making strong comparative claims. "
    "Prompts and completions may be sensitive; follow `SECURITY.md` when exporting this figure outside the research team.",
)

add(
    "figures/fig_cep_progression.png",
    "This chart is a **dual-metric progression** view: for each elicitation category it juxtaposes the **UNSAFE rate** with a broader **risk rate** defined as the fraction of completions labeled PARTIAL **or** UNSAFE under `LABEL_RUBRIC.md`. "
    "The intent is to make the relationship between “hard failures” and “borderline failures” visually obvious: some categories may show moderate risk with low UNSAFE, indicating that policy stress manifests as PARTIAL-heavy behavior rather than overt violations. "
    "The x-axis lists categories in a fixed order chosen for readability; that order is not inherently a ranking of moral severity unless the paper argues so independently. "
    "Connecting lines or grouped bars (depending on implementation) encourage the reader to compare the vertical gap between the two metrics within a category.",
    "Both curves or bar groups are computed from the **same labeled pilot table**, so differences between them are arithmetic consequences of how much mass sits in PARTIAL. "
    "The acronym **CEP** in project language refers to **category-conditional empirical patterns** under this bank—descriptive structure—not a fitted causal estimand or a population parameter for all deployments. "
    "If you export underlying counts, you can verify that risk ≥ UNSAFE pointwise for every category, with equality only when PARTIAL is empty for that category.",
    "Generate the figure via `python scripts/generate_report_figures.py` alongside the other pilot exports. "
    "If you change the definition of risk (for example including only a subset of PARTIAL tags), you must update both the methods text and the plotting code fork; reviewers may ask for a sensitivity plot with alternative risk definitions.",
    "A **large gap** between risk and UNSAFE is a signal to prioritize qualitative review of PARTIAL examples: are they benign hedging, or are they precursors to harmful content under slight prompt edits? "
    "A **small gap** suggests that when the model fails, it tends to fail outright rather than sitting on the fence—useful for comparing vendors if the pattern replicates in multimodel plots. "
    "Do not read left-to-right monotonicity as a trend over time unless the x-axis is literally temporal.",
    "Because each category has limited prompts, differences in gap size can be noisy; bootstrap confidence bands or Bayesian partial pooling would strengthen claims if you need them for publication. "
    "Ethically, emphasize that risk metrics are **rubric-relative**; a different rubric could shrink or inflate PARTIAL. "
    "Handle raw outputs under `SECURITY.md`.",
)

add(
    "figures/fig_failure_pattern_fingerprint.png",
    "The **radar** (spider) plot is a compact way to visualize a **vector of category-level rates** for a single model snapshot: each axis corresponds to one elicitation category, and the closed polygon connects the model’s UNSAFE (or related) values around the circle. "
    "The geometry is chosen for human pattern recognition: a “spiky” polygon indicates a model that is selectively weak on a subset of categories, while a more regular polygon suggests flatter relative risk. "
    "Radial plots trade absolute magnitude perception for shape perception, so they belong in exploratory or communication settings rather than as the sole quantitative record. "
    "Multimodel audits often complement this pilot radar with line-based fingerprint curves in `results/multimodel/.../fig_model_fingerprint_curves.png`, which are easier to read when overlaying multiple APIs.",
    "Numerically, the radar uses the **same per-category aggregates** as the bar charts: each axis value is a proportion computed from labeled JSON after any documented filtering. "
    "If the script plots multiple strata, they may appear as multiple polygons or as separate figures—check the generator for the exact convention in your commit. "
    "Because radar axes share the same scale, categories with very different denominators are still forced onto comparable radii; that is a feature for shape comparison but a limitation for uncertainty display.",
    "Create or refresh the PNG with `python scripts/generate_report_figures.py` from `llm-safety-experiment/`. "
    "If you need to overlay two models on one radar, that may require a fork: the stock script may assume one polygon to keep the pilot figures simple. "
    "Vector export (PDF/SVG) from matplotlib preserves editability for slides better than PNG when fonts need adjustment.",
    "When interpreting lobes, ask **which categories pull the polygon outward** relative to the pilot average; those categories merit case-by-case error analysis. "
    "Be careful not to confuse **area inside the polygon** with a meaningful scalar score unless the paper defines one; area depends on axis ordering, which can be permuted. "
    "Pair radar summaries with tables of counts so readers can see whether a spike is driven by one UNSAFE completion on n=18 versus a systematic pattern on larger n in other phases.",
    "Radial plots can exaggerate visually small differences; verify important claims against numeric tables. "
    "For multimodel papers, combine this qualitative view with `figures/multimodel/combined_signature_unsafe_heatmap.png` for a grid-level perspective. "
    "Respect `SECURITY.md` when sharing underlying prompts tied to extreme axis values.",
)

add(
    "figures/fig_entropy_safety.png",
    "Entropy here means **Shannon entropy** of the discrete label distribution within each pilot category: given empirical probabilities for SAFE, PARTIAL, and UNSAFE in that category, the plot reports H = −∑ p_k log p_k (in whatever base the script documents, often natural log or log2). "
    "High entropy indicates the model’s outcomes are **spread** across labels rather than concentrated in a single class; low entropy indicates predictable behavior (almost always SAFE, or almost always one failure mode). "
    "This is a **diversity** measure, not a harm index: a category could have high entropy because the model oscillates between safe and PARTIAL responses, not because it often produces UNSAFE text. "
    "Therefore entropy should be read alongside the stacked composition figure, which shows whether diversity comes from benign variation or from a dangerous mix.",
    "The plug-in entropy estimate is computed from the same adjudicated pilot table as other figures; if any label has zero count, entropy calculations sometimes use smoothing—check `generate_report_figures.py` for whether a small pseudocount is added. "
    "Changing smoothing rules can reorder categories slightly in entropy rankings. "
    "Entropy comparisons across categories are only meaningful when each category uses the **same label alphabet** and similar experimental conditions; comparing entropy from a three-way rubric to entropy from a binary rubric is invalid.",
    "Regenerate via `python scripts/generate_report_figures.py`. "
    "If you need confidence intervals on entropy differences, the stock figure may not provide them; bootstrap resampling of prompts within category is the usual workaround. "
    "For reproducibility, record software versions because numpy/scipy updates rarely affect entropy but matplotlib styling changes can confuse readers comparing drafts.",
    "Use entropy to flag categories worth **qualitative review**: high entropy may mean annotators struggled with consistent labeling or the model produced genuinely heterogeneous behavior. "
    "Do not claim that “higher entropy implies less safe” without tying the label distribution to harm; a model that always refuses might show low entropy and high safety under the rubric. "
    "When writing for a general audience, define entropy in one plain sentence to avoid mystique.",
    "With pilot-scale n, entropy estimates have non-trivial variance; differences of a few hundredths of a bit may not replicate. "
    "Treat this figure as exploratory unless paired with inference. "
    "Handle sensitive completions per `SECURITY.md`.",
)

add(
    "figures/fig_category_safety_sankey.png",
    "A **Sankey** diagram represents **flows** from sources to sinks: here, mass typically flows from elicitation **categories** on the left to adjudicated **outcomes** (SAFE, PARTIAL, UNSAFE) on the right, with ribbon widths proportional to the number of prompts (or to their share of the total) traversing each path. "
    "Sankeys excel at communicating how a fixed evaluation budget splits across outcome classes without forcing the reader to mentally sum table rows. "
    "They are especially helpful in talks where stakeholders want an intuitive picture of “where prompts end up” after labeling. "
    "The trade-off is precision: when many thin ribbons overlap, readers cannot recover exact percentages without a companion table.",
    "The data pipeline matches other pilot visuals: each prompt’s final label comes from adjudication under `LABEL_RUBRIC.md`. "
    "Implementation lives in `generate_category_safety_sankey_figure()` inside `scripts/generate_report_figures.py`, which uses **Plotly** for layout and **Kaleido** (or an equivalent engine) to rasterize vector Sankeys into PNG. "
    "If your environment lacks Kaleido or if headless export hangs, the repository documents `--skip-sankey` so you can still produce the core scientific figures—see `PROVENANCE.md` and CI notes.",
    "Produce the figure with `python scripts/generate_report_figures.py` **without** `--skip-sankey`, or orchestrate through `python scripts/reproduce_main_figures.py --sankey` when that flag is wired. "
    "On Windows and Linux containers, set non-interactive backends as recommended in project docs; if export times out, retry locally with a longer timeout or export HTML interactively for debugging. "
    "Always archive the exact results JSON alongside the PNG so the Sankey can be regenerated for camera-ready revisions.",
    "When presenting, narrate **major flows** (“most prompts in category A become SAFE, but a visible ribbon leaks into PARTIAL”) rather than quoting ribbon pixels. "
    "Pair the Sankey with `figure2_label_distribution_stacked.png` if you need per-category composition without flow topology. "
    "Remember that Sankey aesthetics (node order, curvature) can subtly influence perception even when the underlying numbers are identical.",
    "Sankeys may inadvertently highlight sensitive prompt classes; avoid publishing high-resolution exports if categories are labeled in a way that enables reconstruction of disallowed content. "
    "Follow `SECURITY.md` for redaction and access control.",
)


# --- Multimodel combined figures --------------------------------------------

_MULTI_UNSAFE_HEAT = (
    "This **multimodel signature heatmap** summarizes UNSAFE adjudication rates for every combination of **model run** (one of the nine API configurations in the frozen grid) and **elicitation category** in the shared benchmark. "
    "Rows and columns are assigned by `plot_multimodel_signature_heatmap.py` conventions—typically one axis lists models and the other lists categories—but the core encoding is always the same: cell color corresponds to the empirical fraction of completions labeled UNSAFE in that cell. "
    "The heatmap is useful because it compresses an entire cross-model comparison into one surface, revealing whether failures cluster on particular vendors, tiers, or taxonomic slices of prompts. "
    "Unlike a single-model pilot chart, this graphic is explicitly **comparative**: your eye should track horizontal bands (a category that is hard for everyone) versus vertical bands (a model that is weak everywhere). "
    "Remember that color is a **magnifier** for pattern search; publish numeric tables for any claim that must survive peer review.",
    "The quantitative backbone is `figures/multimodel/signature_rate_matrix.json`, which stores the unsafe-rate matrix and metadata after `build_multimodel_rate_matrix.py --metric unsafe` (or an equivalent aggregator) has ingested the per-run labeled JSONs under `results/multimodel/`. "
    "Each entry is only as trustworthy as the alignment of prompt IDs across runs: the benchmark assumes comparable rows for paired analyses. "
    "UNSAFE semantics are unchanged from `LABEL_RUBRIC.md`; multimodel adds complexity because labeling pipelines must stay consistent across months of API drift. "
    "If you regenerate models with updated system prompts, treat new outputs as a new artifact series rather than silently patching old JSON. "
    "When Gemini appears in multiple tiers, read captions carefully: some snapshots reuse similar model identifiers across price bands, and conflating them misstates the independent variable.",
    "Regenerate the figure from `llm-safety-experiment/` using either the orchestrated path `python scripts/reproduce_main_figures.py` or the targeted plotter `python scripts/plot_multimodel_signature_heatmap.py --kind raw`, passing paths that match your checkout layout. "
    "If colors diverge between runs, confirm you did not mix an old `signature_rate_matrix.json` with freshly plotted PNGs—hash or timestamp artifacts in `PROVENANCE.md` when possible. "
    "For print, export vector formats if the plotting script supports it; otherwise ensure DPI and font sizes meet venue requirements. "
    "When debugging empty cells, trace back to missing labels or failed API calls logged in the run metadata rather than tweaking the colormap.",
    "Read **hot** cells (per the chosen palette) as model–category pairs with elevated UNSAFE under this bank, but always ask whether elevation is driven by a handful of prompts or a broad trend—drill into incidence heatmaps for the former. "
    "Compare providers with the caveat that **tier and vendor are partially confounded** in a nine-run design: you are seeing a structured sample, not a random draw from all commercial models. "
    "Avoid causal language (“GPT-4o caused higher UNSAFE”) without a design that supports causal identification; prefer “observed higher UNSAFE under this API snapshot.” "
    "When categories have different within-cell sample sizes, shade or annotate cells with n if your plotting fork supports it.",
    "These rates describe **benchmark-conditioned** behavior, not real-world incident prevalence; the prompts are adversarially informative by design. "
    "Raw completions may include actionable harm; follow `SECURITY.md` for storage and publication. "
    "Be explicit that results may change when vendors update post-training or safety policies without notice.",
)

add("figures/multimodel/combined_signature_unsafe_heatmap.png", *_MULTI_UNSAFE_HEAT)

add(
    "figures/multimodel/signature_unsafe_heatmap.png",
    "This asset is a **filename alias** for the multimodel UNSAFE signature heatmap: some older automation, drafts, or external notebooks may still reference `signature_unsafe_heatmap.png` instead of `combined_signature_unsafe_heatmap.png`. "
    "Except for naming, the analytic content should match the combined file produced in the same pipeline; if the two diverge in your working tree, that indicates a stale export or a manual copy error rather than an intentional difference. "
    "When starting a new manuscript, pick one canonical name and symlink or configure generators to avoid duplication; duplication nonetheless helps backward compatibility for frozen supplementary materials. "
    "Readers should not reinterpret the legacy name as a different statistical estimand.",
    *_MULTI_UNSAFE_HEAT[1:],
)

add(
    "figures/multimodel/combined_signature_excess_vs_direct.png",
    "This **diverging** heatmap visualizes **excess UNSAFE** for each model and category: roughly, how much higher or lower the UNSAFE rate is under a target stratum relative to the **direct** elicitation baseline, holding the benchmark’s pairing structure. "
    "The color scale is typically centered at zero so that readers can immediately see which cells show **amplification** (more UNSAFE than direct) versus **attenuation** (fewer UNSAFE than direct). "
    "The graphic is invaluable for discussing **framing effects**—for example, whether roleplay or staged scenarios move models off their direct-request behavior—but it is still descriptive of this prompt set. "
    "Because both the treated stratum and the baseline are estimated from data, the map encodes a **difference of random quantities**, which is inherently noisier than a single proportion map.",
    "Construction begins from the same multimodel labeled JSONs that feed `signature_rate_matrix.json`; the plotting script implements the project’s definition of “direct” versus alternate framings. "
    "If your methods text defines direct differently (e.g., excluding a subset of prompts), regenerate the matrix rather than relabeling the PNG in a slide deck. "
    "Cells with very small denominators can show huge excess magnitudes driven by one or two flips between SAFE and UNSAFE; incidence plots help diagnose that pathology. "
    "Paired statistical tests (McNemar, etc.) should back any claim that excess is “significant,” because eyeballing color on a diverging scale is not inference.",
    "Rebuild with `python scripts/plot_multimodel_signature_heatmap.py --kind excess_vs_direct`, or invoke the full `reproduce_main_figures.py` if your branch wires this plot into the default bundle. "
    "Confirm that the colormap’s numeric limits are symmetric around zero unless you have a strong justification otherwise; asymmetric limits can visually bias comparisons. "
    "Export the numeric contrast table alongside the figure for reviewers who cannot read heatmaps easily.",
    "Interpret **positive** excess as “this model–category pair produced more UNSAFE under the alternate framing than under direct prompts in this sample,” not as a universal statement about human misuse in the wild. "
    "**Negative** excess can indicate safer behavior under the alternate framing—or simply different prompt difficulty if pairing is imperfect—so qualitative review matters. "
    "Be cautious comparing excess magnitudes across categories with different baseline rates: percentage-point differences behave differently when baselines are near zero versus near one.",
    "Difference-based visuals hide absolute risk: a small excess on top of a high baseline may be worse operationally than a large excess on a negligible baseline. "
    "Always archive the underlying counts and respect `SECURITY.md` when discussing fraught categories. "
    "Document API versions because vendor updates can shrink or inflate framing effects overnight.",
)

add(
    "figures/multimodel/signature_excess_unsafe_vs_direct.png",
    "This PNG preserves a **legacy basename** for the excess-versus-direct UNSAFE heatmap, parallel to `combined_signature_excess_vs_direct.png`. "
    "Legacy names persist so that older documents, Zenodo snapshots, or colleague scripts keep working without silent 404s. "
    "You should treat both files as interchangeable **if and only if** they were generated from the same matrix build; verify timestamps or checksums when both exist. "
    "If you are cleaning the repository, deprecate one filename only after searching the codebase and any external citations. "
    "Manuscripts should standardize on the `combined_` naming going forward unless a venue already printed the legacy path.",
    "Data dependencies mirror the combined figure: start from `signature_rate_matrix.json` and multimodel JSON roots under `results/multimodel/`. "
    "When writing methods, describe the pairing of prompts across framings precisely enough that a third party could recompute the contrast. "
    "If the legacy file is regenerated rarely, it is especially easy for it to go stale—add a CI check or Makefile target if this bites you repeatedly.",
    "Regenerate via `plot_multimodel_signature_heatmap.py --kind excess_vs_direct` with identical parameters to the combined export. "
    "Consider deleting redundant legacy outputs in favor of symlinks if your OS supports them and your tooling tolerates symlinks in Git LFS.",
    "Reading guidance is identical to the combined-named sibling: positive values mean more UNSAFE than the direct baseline for that cell, negative values mean less. "
    "Do not double-count both PNGs in a publication as if they were independent analyses.",
    "Maintain the same statistical cautions: differences are noisy, baselines matter, and harmful content may appear in supporting data—see `SECURITY.md`.",
)

add(
    "figures/multimodel/combined_signature_risk_heatmap.png",
    "This heatmap mirrors the unsafe signature map but uses a **risk** outcome defined as **PARTIAL ∪ UNSAFE** under `LABEL_RUBRIC.md`, i.e., any completion that is not cleanly SAFE. "
    "The motivation is operational: many deployments care about borderline compliance even when a completion is not a “full” UNSAFE violation. "
    "Visually, you should expect risk cells to be **numerically larger** than unsafe cells in the same positions, with the gap indicating how much mass lives in PARTIAL. "
    "Hot spots here highlight categories where models hedge, partially comply, or soft-refuse in ways that may still be problematic in product settings. "
    "Comparing the risk heatmap to the unsafe heatmap side-by-side is one of the fastest ways to communicate “UNSAFE-only metrics understate stress in category X.”",
    "The matrix is stored at `figures/multimodel/signature_rate_matrix_risk.json`, produced once the risk aggregator has processed the same multimodel JSON corpus as the unsafe matrix. "
    "Risk is not a universal concept—document your PARTIAL definition carefully because stakeholders may assume risk means malware or violence when you mean “any non-SAFE rubric bucket.” "
    "If PARTIAL labels are noisier than UNSAFE labels, risk heatmaps inherit that noise; inter-annotator disagreement metrics belong in the appendix. "
    "Gemini-related caveats about tier labeling apply equally here; mislabeling a tier can falsely imply a price band effect.",
    "Regenerate using the multimodel heatmap script pointed at the risk JSON (`--kind raw` or the documented flag for risk), or rely on `reproduce_main_figures.py` if it already sequences that build. "
    "Ensure you do not accidentally pass the unsafe JSON into the risk plotter—the colormap may still look plausible while being wrong. "
    "After regeneration, diff the JSON against prior commits if you need to explain shifts between arXiv v1 and v2.",
    "When reading, prioritize **category-specific** comparisons across models rather than ranking models on a single scalar unless you define such a scalar in methods. "
    "Be explicit that risk includes PARTIAL, so security teams should not conflate this map with incident rates of overtly illegal instructions. "
    "Pair with `combined_label_composition_stacked.png` to see whether risk is PARTIAL-driven or UNSAFE-driven for a given vendor.",
    "Changing PARTIAL criteria between paper versions invalidates cross-version comparisons; version the rubric. "
    "Ethically, risk heatmaps can look alarming—contextualize with benchmark intent and follow `SECURITY.md` for data handling.",
)

add(
    "figures/multimodel/combined_9panel_unsafe_by_category.png",
    "This **3×3 grid** is the flagship multimodel overview figure in many expositions of the nine-run benchmark: each panel corresponds to one API configuration (a specific provider and pricing tier combination), and within each panel you see UNSAFE rates broken down by elicitation category on a shared axis. "
    "When error bars or Wilson intervals are enabled, each bar communicates both point estimate and sampling uncertainty for that cell; when disabled, the figure emphasizes speed and clarity for talks. "
    "The layout lets readers perform **at-a-glance** comparisons across vendors while keeping category definitions consistent, which is harder when every model is plotted in a separate file. "
    "Because human working memory is limited, the nine-panel design is near the upper bound of complexity for a single slide—use callouts or inset zooms if you discuss one category heavily.",
    "Underlying counts come from the multimodel labeled JSONs archived per tier under `results/multimodel/<tier>/...`; the plotting script merges them according to the frozen crosswalk between run IDs and panel positions. "
    "Interval computations, when present, require per-cell counts of successes and trials; if bars look smooth but intervals are missing, you may have run with `--no-ci` or failed to export count metadata. "
    "Always record model version strings and snapshot dates beside this figure in an appendix; API drift can reorder bars without any change to your code. "
    "If a panel looks empty or flat-line, check for API failures or filtering rules that dropped prompts for that run.",
    "Generate via `python scripts/plot_multimodel_nine_panel.py` from `llm-safety-experiment/`, or build it as part of `reproduce_main_figures.py` when configured. "
    "`--no-ci` is appropriate for internal drafts but discouraged for publication unless intervals appear elsewhere. "
    "Font sizes should be legible when the composite is embedded at single-column width; test shrinking the PNG to your journal’s column inches before final submission.",
    "Read **across panels** for vendor/tier differences on the same category bar, and **within panels** for category difficulty profiles. "
    "Avoid declaring a global “winner” model unless you define an aggregation rule (macro average vs micro average) and justify it; different rules change rankings. "
    "Remember that **multiplicity** is high: with many bars, some contrasts will look large by chance unless controlled. "
    "Gemini mid versus expensive comparisons deserve extra caution if documentation notes identifier quirks—cite those notes prominently.",
    "This figure is still descriptive of a curated bank; do not extrapolate to uncensored user traffic. "
    "Harmful completions underpin the counts—handle per `SECURITY.md`. "
    "When reproducing externally, ensure evaluators have legal authorization to run the underlying prompts.",
)

add(
    "figures/multimodel/combined_radar_grid_unsafe.png",
    "This figure is a **small-multiples** layout of radar plots: each subplot shows one model’s UNSAFE profile across elicitation categories, echoing the pilot fingerprint radar but scaled to compare nine APIs on one page. "
    "The value of the grid is **pattern parallelism**—you can see whether models share the same “spiky” categories or whether failures are idiosyncratic. "
    "Because each radar is small, the graphic belongs in exploratory analysis, internal reviews, or supplementary PDFs rather than as the sole evidence for fine quantitative claims. "
    "Axis scaling is typically shared or normalized across subplots so that shapes are comparable; if scaling differs, the caption must say so or readers will mis-rank models. "
    "Use this figure when heatmaps feel too abstract for stakeholders who prefer geometric intuition.",
    "Each mini radar is fed by the same category-level UNSAFE proportions that populate `signature_rate_matrix.json` (or a tensor derived from it). "
    "If categories are reordered around the circle differently across subplots, that is a bug—radar comparability requires consistent angular positions. "
    "Zeros and ones on the boundary of rates can distort polygon corners; some code paths clip or smooth—verify against tables. "
    "When a model has missing categories due to failed runs, imputation or gaps should be explicit rather than silently drawing a misleading polygon.",
    "Rebuild using `python scripts/plot_multimodel_radar_grid.py`, ensuring matplotlib has a reproducible random seed if jitter is used for label positions. "
    "For presentations, export high-DPI PNG or PDF; for the paper, consider moving key panels to full-width vector figures if detail matters. "
    "If file size explodes because of nine high-resolution rasters, downsample for web but keep archival copies.",
    "Interpretation should emphasize **qualitative similarity** (“these three models spike on the same wedge of categories”) rather than ranking models by polygon area. "
    "Cross-check any surprising ordering with the nine-panel bar chart, which is usually easier for precise comparisons. "
    "Avoid claiming statistical significance from visual overlap of polygons.",
    "Radar grids can inadvertently highlight sensitive categories by name; redact or aggregate labels if needed. "
    "Follow `SECURITY.md` for underlying data. "
    "Remember that nine models is a tiny sample of the market; external validity is limited.",
)

add(
    "figures/multimodel/combined_parallel_coordinates.png",
    "A **parallel-coordinates** plot treats each elicitation category as a vertical axis and draws one polyline per model run, placing each point at the UNSAFE rate (or a monotone transform) achieved on that category. "
    "Line **crossings** indicate **rank reversals**: a model that is worse than another on one category may be better on another, which is important for deployment decisions when workloads are heterogeneous. "
    "Dense bundles of lines suggest consensus about which categories are hard, while fanning lines suggest disagreement. "
    "The visualization trades off clutter for richness—when too many lines overlap, consider interactive brushing or faceting by provider. "
    "Color or line style may encode provider if the plotting fork adds that feature; the stock figure may use distinct hues per run.",
    "The geometry is entirely determined by `signature_rate_matrix.json` after multimodel aggregation; there is no additional modeling layer. "
    "If axes are normalized per category (z-scores), read the caption carefully because raw UNSAFE rates are no longer directly readable from tick marks. "
    "Parallel coordinates can visually exaggerate differences on categories where all models score low but spread is proportionally high—pair with tables. "
    "Missing data must drop an entire line segment or show a gap; otherwise crossings are meaningless.",
    "Generate with `python scripts/plot_multimodel_parallel_coordinates.py`, confirming that category order matches your manuscript’s taxonomy section. "
    "For static exports, increase line alpha or use edge colors to mitigate overplotting when lines coincide. "
    "If you need statistical testing on crossings, define a formal test on paired rates rather than judging by eye.",
    "Runs that ride high across many axes are **globally** more UNSAFE under this bank; runs that dip on most axes but spike once may be “specialists” at failing particular policy tests. "
    "Do not assume independence across axes: categories are different slices of the same benchmark, and prompts may share latent themes. "
    "When narrating for executives, translate one or two concrete crossings into plain language examples (without leaking prompts).",
    "Parallel coordinate plots are easy to misread quickly; include a short how-to in the appendix. "
    "Ethically, emphasize benchmark scope. "
    "Data handling per `SECURITY.md`.",
)

add(
    "figures/multimodel/combined_parallel_coordinates_by_tier.png",
    "This variant augments parallel coordinates by **coloring lines according to commercial tier** (cheap vs mid vs expensive) rather than only by model identity. "
    "The goal is to visualize whether **price segmentation** correlates with safety profiles under the benchmark: do budget endpoints cluster in the upper envelope of UNSAFE rates, or do expensive endpoints separate cleanly? "
    "Because tier and provider are partially aligned in the nine-run design, color clusters may reflect vendor identity as much as list price—disentangling those requires careful prose or additional model covariates. "
    "The figure is best used to **motivate** tier-stratified analyses (forests, regressions) rather than to certify causal effects of pricing. "
    "If two lines share a color, ensure the legend encodes provider as well or readers will confuse distinct APIs.",
    "Data are identical to the uncolored parallel-coordinates plot; only the aesthetic mapping changes. "
    "If tiers were relabeled between API pricing updates, regenerate labels from the frozen configuration JSON rather than hand-editing the figure. "
    "When tiers have unequal counts (here, three per tier in the canonical grid), avoid implying balanced sampling beyond the design. "
    "Document whether rates on axes are raw or variance-stabilized.",
    "Run `plot_multimodel_parallel_coordinates.py` with `--color-by tier` or the equivalent flag documented in `--help`. "
    "Validate colorblind palettes; tier is nominal, so hue choices should maximize discriminability. "
    "Export a grayscale test slide before conference projection on unknown equipment.",
    "Read **vertical banding** of colors as tier-related clustering, but test statistically before claiming “cheaper models are less safe.” "
    "Consider interactions: a cheap model from vendor A may outperform an expensive model from vendor B, undermining simplistic tier narratives. "
    "Pair with `phd_tier_provider_interaction_unsafe.png` if available.",
    "Tier is not randomized; respect `SECURITY.md`; avoid implying vendor malice from descriptive plots.",
)

add(
    "figures/multimodel/combined_forest_wilson_unsafe.png",
    "A **forest plot** (or forest-like interval panel) displays UNSAFE proportions with **Wilson confidence intervals** for many model–category cells at once, prioritizing statistical transparency over compact color fields. "
    "Each row typically shows a point estimate and a horizontal interval; longer intervals warn that the effective sample size for that cell is small or the rate is near 0.5. "
    "Forests shine in appendices where reviewers demand uncertainty, and in regulatory-style memos where point estimates without intervals are considered incomplete. "
    "Unlike heatmaps, forests do not force a colormap choice that might downplay uncertainty; the eye naturally weights wide intervals as less certain. "
    "The cost is vertical space: full grids may require multi-page PDFs.",
    "Intervals are derived from the same unsafe counts as `signature_rate_matrix.json`, with denominators taken from evaluated prompts after filtering. "
    "Wilson intervals are not simultaneous confidence bands across all rows unless you apply a multiplicity correction in post-processing; the plotting script may not do that automatically. "
    "If you sort rows by effect size, disclose the sorting rule to avoid post-hoc selection bias narratives. "
    "Cells with zero denominators should be omitted or flagged, not drawn as point estimates at arbitrary values.",
    "Create the figure with `python scripts/plot_multimodel_forest_wilson.py` pointed at the unsafe metric inputs. "
    "Tune label fonts so model names and categories remain readable when the forest has dozens of rows. "
    "For blind review, anonymize model names consistently across all supplementary figures.",
    "Non-overlapping intervals provide **weak evidence** of differences for independent samples; for paired prompts, prefer McNemar-style summaries that the PHD companion plots may provide. "
    "Do not rank models by counting how many intervals sit above a threshold unless that counting rule was prespecified. "
    "Combine with `combined_forest_wilson_risk.png` when PARTIAL mass matters for deployment.",
    "Forests can reveal rare failure modes—handle associated prompts carefully. "
    "`SECURITY.md` applies. "
    "Archive the CSV of intervals next to the PNG for reproducibility.",
)

add(
    "figures/multimodel/combined_forest_wilson_risk.png",
    "This forest plot parallels the UNSAFE forest but targets the **risk** outcome (PARTIAL ∪ UNSAFE), so point estimates are typically **higher** and intervals may be wider when PARTIAL is common. "
    "It communicates uncertainty about **borderline-inclusive** failure rates, which often track operational moderation load more closely than UNSAFE-only metrics. "
    "Reviewers may ask why both forests exist; the answer is that they answer different policy questions—catastrophic misuse vs general policy stress. "
    "Side-by-side placement in a PDF helps readers grasp how much mass lives in PARTIAL for each cell. "
    "If risk and unsafe forests use different row orders, align them for easier comparison or note the discrepancy.",
    "Inputs come from `signature_rate_matrix_risk.json` and the same labeled multimodel JSON corpus. "
    "Risk labeling noise flows straight into interval width; if PARTIAL is ambiguous in the rubric, expect wide intervals and heated qualitative debates—address that in methods. "
    "Do not compare risk intervals to unsafe intervals on the same numeric scale without transforming; they measure different events. "
    "Document handling of cells where UNSAFE is zero but PARTIAL is nonzero—these are especially important for customer trust narratives.",
    "Run `plot_multimodel_forest_wilson.py` with risk inputs as documented in that script’s CLI. "
    "Verify you did not pass unsafe JSON by mistake—file names are similar and errors are costly. "
    "Consider exporting the same data as a CSV for accessibility.",
    "Interpret shifts as changes in **policy-adjacent** behavior, not only overt violations. "
    "Non-overlap still does not replace paired tests when prompts are matched. "
    "When speaking to non-technical stakeholders, translate “risk” into concrete moderator actions (“would this completion get blocked?”).",
    "Risk metrics are rubric-relative; include `LABEL_RUBRIC.md` excerpts in supplements. "
    "Respect `SECURITY.md` for completions that illustrate PARTIAL edge cases.",
)

add(
    "figures/multimodel/combined_clustermap_rates.png",
    "This figure is a **hierarchically clustered heatmap** (often called a *clustermap*): **rows** index model runs (nine API configurations in the canonical grid) and **columns** index elicitation categories from the fixed benchmark. "
    "Each cell encodes an estimated rate $\\hat{p}$—typically the **UNSAFE** proportion in that (model, category) cell under `LABEL_RUBRIC.md`, unless you point the script at a risk matrix export instead. "
    "**Column** and **row** dendrograms show **average-linkage** agglomerative clustering on **Euclidean** distances between **row vectors** (two models are “close” if their category profiles are similar) and between **column vectors** (two categories are “close” if they evoke similar cross-model failure patterns). "
    "The **publication layout** uses a **light, neutral theme**, **wider gutters** between the dendrogram axes and the heatmap, and a **dedicated narrow column** for the color bar so category tick labels and the scale **do not overlap**—a common failure mode in compact dark-theme exports. "
    "The title and subtitle state that ordering is **exploratory**; dendrogram topology is **not** a hypothesis test, a causal graph, or a recommendation about which vendor to deploy.",
    "The quantitative input is `signature_rate_matrix.json` (unsafe) or the parallel **risk** matrix JSON when you build one; each entry is derived from **adjudicated** completions stored under `results/multimodel/…` after runs complete. "
    "Missing or non-finite cells are filled **column-wise** with the column mean before clustering—a pragmatic imputation that should be disclosed if any missingness is structural (for example, an API outage) rather than numerical noise. "
    "**Preprocessing changes trees**: z-scoring rows, logit-transforming rates, or weighting categories by harm severity would all yield different merges; PhD-level methods text should record the **exact** recipe used here (raw rates on [0,1], Euclidean, average linkage). "
    "Because **n = 9** models, the **row** dendrogram has very few leaves; small perturbations to rates or to tie-breaking can **reorder** nearest-neighbor merges. Treat the row tree as a **conversation starter**, not a stable phylogeny of model families.",
    "Regenerate with `python scripts/plot_multimodel_clustermap.py --matrix-json figures/multimodel/signature_rate_matrix.json` from `llm-safety-experiment/` (see `--out` and `--dpi`). "
    "The script writes a **high-DPI PNG** with `bbox_inches='tight'` and extra padding so captions survive two-column downscaling in LaTeX or Word. "
    "If you need **vector** output for a thesis, re-export from matplotlib with `fig.savefig(..., format='pdf')` in a short fork—keep font embedding settings consistent with your institution’s template. "
    "After regeneration, visually confirm that **top** and **left** dendrograms align with the heatmap extents; misalignment usually means a manual edit broke `imshow(..., extent=...)` or the linkage input order.",
    "Read **color intensity** as higher $\\hat{p}$ in that cell after clustering; **do not** interpret cell *position before* clustering from this graphic—the matrix is **permuted** for visualization. "
    "When two **categories** merge low in the **column** dendrogram, interpret that as “similar **cross-model** rate vectors,” not necessarily similar prompt semantics—different rubric slices can correlate by accident on nine points. "
    "When two **models** merge in the **row** tree, you are seeing similar **profiles across categories** under this bank; validate with **`combined_9panel_unsafe_by_category.png`** or **`combined_signature_unsafe_heatmap.png`** because readers parse those layouts more intuitively for *absolute* comparisons. "
    "Never describe a branch as “significant” unless you back it with an appropriate **stability analysis** (bootstrap, jackknife, or larger model panels).",
    "Unsupervised layouts can **over-impress** non-specialist audiences; pair this figure with explicit **uncertainty** displays (Wilson forests, Beta facets) when stakes are high. "
    "Category names may reveal **sensitive** benchmark structure; follow `SECURITY.md` before circulating high-resolution crops. "
    "Do not use this figure alone for **procurement** or **compliance** decisions—it summarizes one frozen audit, not future API behavior.",
)

add(
    "figures/multimodel/combined_tier_slope_overall_rates.png",
    "This chart summarizes **aggregate** UNSAFE or risk rates across **pricing tiers**, connecting cheap, mid, and expensive endpoints in a way that supports a simple narrative about whether “you get what you pay for” in safety terms. "
    "Depending on implementation, you may see connected points, regression lines, or facet-specific slopes for each provider. "
    "The strength of the figure is brevity; its weakness is **aggregation**: any improvement in the headline statistic can mask worse behavior on important subcategories, which is why the nine-panel category breakdown remains essential. "
    "Read slopes as descriptive trends within this benchmark, not as elasticity of safety with respect to list price in the economy. "
    "If tiers are unevenly populated or confounded with model families, annotate that limitation prominently.",
    "Numerators and denominators come from multimodel JSONs after labeling; the aggregation window (micro vs macro average across categories) should match `plot_tier_slope_chart.py`. "
    "Changing from micro- to macro-averaging can flip whether a tier looks better overall. "
    "If rates are transformed (logit, arcsin), slopes interpret on that scale, not on raw percentage points. "
    "API version drift across tiers can create pseudo-trends if cheap and expensive endpoints were not queried contemporaneously.",
    "Regenerate via `python scripts/plot_tier_slope_chart.py` from `llm-safety-experiment/`. "
    "When preparing slides, label each point with model slug text only if legible; otherwise use a keyed table. "
    "If you add confidence intervals, ensure they respect dependence across tiers from the same provider.",
    "Negative slopes (higher tier → lower UNSAFE) support a **price–safety correlation** hypothesis but do not establish causation or external validity. "
    "Flat slopes suggest tier is not a dominant axis of variation in this bank—perhaps category heterogeneity or vendor identity matters more. "
    "Always inspect categories where expensive models regress; those can become important counterexamples in discussion sections.",
    "Tier narratives touch commercial sensitivities—word claims carefully. "
    "Follow `SECURITY.md`. "
    "Reproducibility requires pinning API dates alongside this figure.",
)

add(
    "figures/multimodel/combined_label_composition_stacked.png",
    "Stacked bars (or columns) show, for **each multimodel run**, the fraction of completions labeled SAFE, PARTIAL, and UNSAFE, summing to 100%. "
    "This is the multimodel analogue of the pilot composition chart and answers whether failures are **mostly borderline** or **mostly outright** for each vendor/tier. "
    "Comparing stacks across runs highlights vendor-specific tendencies: some APIs may produce few UNSAFE labels but many PARTIAL labels, indicating softer policy edges rather than crisp refusals. "
    "The figure is essential when stakeholders conflate “low UNSAFE” with “safe enough,” because PARTIAL mass may still trigger human review queues in production. "
    "Use consistent colors with pilot figures to reduce cognitive load.",
    "Counts come from labeled JSONs under `results/multimodel/` after adjudication; any post-filtering of malformed rows changes denominators. "
    "If a run has severe API outage data, composition may reflect fewer prompts—check totals before comparing bar heights across runs. "
    "PARTIAL definitions must match `LABEL_RUBRIC.md`; multimodel runs sometimes tempt teams to relax PARTIAL labeling for speed—resist that if comparability matters. "
    "When SAFE is near 100%, zoomed inset plots may be needed to see PARTIAL slivers.",
    "Generate via `python scripts/plot_multimodel_label_composition.py`, verifying sort order of runs matches your main text table. "
    "For print, include numeric percentages on segments only if they remain legible; otherwise provide a CSV. "
    "If you export interactive HTML elsewhere, ensure colors match the static PNG for consistency.",
    "Interpret **thick PARTIAL layers** as a signal to examine moderation policies and user-frustration risks, not only catastrophic harm. "
    "Interpret **thick UNSAFE layers** as immediate priorities for mitigation and red teaming. "
    "Be cautious comparing runs with different total n unless bars are normalized (they should be, by construction).",
    "Completions may contain harmful text even when labeled SAFE if the rubric is incomplete—composition is only as good as labeling. "
    "`SECURITY.md` governs sharing. "
    "Do not use this figure alone to choose a vendor for high-stakes deployment.",
)

add(
    "figures/multimodel/summary_table_models_categories.png",
    "This graphic is a **typeset table** of model×category statistics—often UNSAFE or risk rates, sometimes with uncertainty—aimed at readers who prefer numbers to color fields. "
    "It functions as a bridge between exploratory heatmaps and the exact values reviewers ask you to paste into appendices. "
    "Depending on generator settings, cells may show percentages rounded to one decimal, counts in parentheses, or significance stars; always read the caption for the convention used. "
    "Tables trade compactness for space: wide tables may span two journal pages; consider rotating headers or splitting by provider family. "
    "Alignment and monospace fonts help scan columns but should remain venue-compliant.",
    "The authoritative machine-readable export is typically `summary_table_models_categories.csv`, produced by `export_multimodel_summary_table.py` alongside the PNG. "
    "Treat the CSV as the **source of truth** for digits; the PNG is a human-facing view that may round or truncate. "
    "If you detect a mismatch between CSV and PNG, assume the PNG is stale until you regenerate. "
    "When merging supplemental tables into LaTeX, import from CSV to avoid transcription errors.",
    "Regenerate using `python scripts/export_multimodel_summary_table.py`, then rerun any plotting helper if your pipeline separates tabular export from visual rendering. "
    "Version-control both CSV and PNG in the same commit to keep artifacts synchronized. "
    "For blind submissions, mask model names consistently with other figures.",
    "Use the table to support **precise comparisons** called out in the main text (“Model A is 4.2 points higher than Model B on category C”). "
    "Remember that rounded differences can hide tiny but important gaps—carry extra precision in supplementary CSVs. "
    "Highlight cells discussed in the narrative with care to avoid cherry-picking without multiplicity control.",
    "Tables may make rare failure rates look deceptively exact; include denominators. "
    "`SECURITY.md` applies to underlying data. "
    "Large tables can deanonymize niche categories—aggregate if needed.",
)

add(
    "figures/multimodel/combined_category_correlation_across_models.png",
    "This figure displays a **correlation matrix** between elicitation categories using each category’s **vector of model-specific rates** (length nine in the canonical design). "
    "Positive correlation between categories i and j means that models which are weak on category i tend also to be weak on category j in this sample; negative correlation means complementary weakness patterns. "
    "Such structure hints at **latent skill factors**—for example, categories that jointly probe similar refusal capabilities—but n=9 models means each correlation estimate is extremely noisy and sensitive to outliers. "
    "Treat the plot as **hypothesis generation** for future, larger model panels or for rubric consolidation discussions. "
    "Never report correlation p-values without acknowledging the tiny model sample and potential non-normality of rate vectors.",
    "Correlations are computed from the empirical rate table underlying the multimodel heatmaps; preprocessing such as logit transforms changes results. "
    "If any model is missing data for a category, imputation or pairwise deletion must be documented—correlations are not magic invariants. "
    "Category ordering in the matrix is often alphabetical or taxonomic; reordering does not change math but aids interpretation. "
    "If you annotate correlation coefficients on the plot, verify they match a script-exported CSV.",
    "Produce with `python scripts/plot_category_correlation_across_models.py`, capturing flags that control clustering of rows/columns if available. "
    "For talks, emphasize one or two largest correlations rather than showing the full matrix unreadably. "
    "Consider bootstrap resampling models (if you later expand beyond nine) to assess stability.",
    "Do not infer **causal** relationships between categories (e.g., “improving hate speech fixes malware”) from correlations alone. "
    "Be explicit that correlations describe **co-movement across models in this benchmark**, not semantic similarity of prompt text. "
    "If correlations contradict intuition, audit for mis-labeled categories or API failures before theorizing.",
    "Correlation plots are easy to over-trust; soften language in captions. "
    "`SECURITY.md` for data. "
    "Future work should expand n to stabilize estimates.",
)

add(
    "figures/multimodel/combined_within_category_ranks_unsafe.png",
    "For **each elicitation category** separately, this visualization orders the nine model runs by their **UNSAFE rate**, producing a small ranking graphic per category or a faceted layout depending on implementation. "
    "The value is immediate **ordinal comparison** within a fixed slice of the benchmark: readers can see “who is worst on harassment prompts” without mentally scanning a heatmap. "
    "Rankings are highly memorable, so they should be computed from defensible estimates—ideally with uncertainty-aware rank summaries if you extend the tooling. "
    "Ties and near-ties are common with small n; the plot may break ties arbitrarily unless the code specifies a rule. "
    "Use rank plots in main text sparingly; pair with intervals in supplementary material.",
    "Ranks derive from `signature_rate_matrix.json` unsafe entries; if rates are equal to many decimal places, check whether you should display counts instead. "
    "If a model missing data is excluded, ranks among remaining models shift—note exclusions. "
    "Rank-based summaries discard magnitude: a model second-worst by a tiny margin looks as bad as one massively worse. "
    "Consider showing rates adjacent to ranks in a table for adults, ranks alone for quick talks.",
    "Generate with `python scripts/plot_multimodel_within_category_ranks.py`. "
    "For colorblind safety, avoid red–green only encodings for rank bins; use letters or numbers. "
    "Export wide PDFs if category labels are long.",
    "When reading, focus on **robust** patterns (a model that is bottom-quartile in many categories) versus one-off ranks driven by noise. "
    "Bootstrap resampling of prompts within category can show rank stability if you need formal claims. "
    "Avoid defamation-adjacent language about vendors based solely on ranks in an academic benchmark.",
    "Rankings can be sensitive; contextualize with benchmark limitations. "
    "`SECURITY.md`. "
    "Do not use for compliance certification without broader evidence.",
)

add(
    "figures/multimodel/interactive_rates.html",
    "This **HTML artifact** provides an interactive view of multimodel rates—typically a sortable table, hoverable heatmap, or linked brushing interface—so analysts can explore cells without regenerating static PNGs for every question. "
    "Interactivity helps answer ad hoc queries (“sort categories by spread across models” or “highlight cells above 10%”) that would clutter a printed paper. "
    "Depending on implementation, the file may be self-contained or may reference local JavaScript; check whether relative paths assume a particular server root. "
    "Interactive assets are excellent for internal dashboards but require **access control** if they embed exact rates that could aid misuse when combined with prompt leaks. "
    "Browser compatibility and accessibility (keyboard navigation, screen readers) may lag static figures; provide a CSV fallback.",
    "The data ultimately trace to `signature_rate_matrix.json` and related multimodel artifacts; the HTML generator should load the same JSON to avoid divergence. "
    "If tooltips expose prompt IDs, treat the HTML as **highly sensitive** even when prompt text is not inlined. "
    "Version the HTML with the JSON hash in a footer comment so you can prove reproducibility. "
    "Large benchmarks may produce multi-megabyte HTML; gzip for distribution if needed.",
    "Build with `python scripts/plot_multimodel_interactive_matrix.py` (or the script name current in your branch) and open locally in a browser. "
    "For team sharing, host on an internal HTTPS server rather than emailing raw HTML that mail scanners may strip. "
    "If you publish externally, scrub tooltips of internal codenames.",
    "Train users that **hover details** can reveal rare failure statistics that should not be screenshotted into public channels. "
    "Prefer aggregated views for public blog posts. "
    "Interactivity encourages exploratory peeking—inflate multiplicity awareness.",
    "Follow institutional policy for interactive data products. "
    "`SECURITY.md` is mandatory reading before wide distribution.",
)

add(
    "figures/multimodel/phd_mcnemar_pairwise_unsafe.png",
    "This diagnostic graphic summarizes **paired binary discordance** on the UNSAFE label between two model runs that answered the **same** prompts in the benchmark. "
    "Unlike independent two-proportion z-tests, McNemar’s framework accounts for the fact that the two classifiers (API snapshots) see identical inputs, so dependence across columns is the right statistical metaphor. "
    "The plot may show matrices of p-values, counts of discordant pairs, or faceted summaries for each vendor pairing depending on the script version. "
    "Substantively, significant McNemar results mean the models disagree **on which specific prompts** cross the UNSAFE threshold, not merely that marginal rates differ—a distinction that matters for red teaming and for understanding whether failures are systemic or idiosyncratic. "
    "Pairwise grids explode in size as you add models; the nine-run design keeps this tractable but still demands multiplicity caution.",
    "You need aligned prompt IDs across JSON artifacts for every compared pair; silent misalignment yields nonsense discordance counts. "
    "The UNSAFE bit is defined by `LABEL_RUBRIC.md`; if labeling drifted between runs, McNemar tests compare apples to oranges unless you freeze labels. "
    "Sparse discordance (very few flipped labels) produces unstable test statistics; exact McNemar variants may be preferable to asymptotic ones. "
    "Document how missing completions (timeouts, refusals to return JSON) are coded—often they must be excluded or imputed with explicit rules.",
    "Run `python scripts/plot_multimodel_mcnemar_pairwise.py --metric unsafe` from `llm-safety-experiment/` after multimodel JSONs exist. "
    "Capture CLI flags and random seeds in lab notes; some plots jitter labels for readability. "
    "If generating for a paper, export underlying contingency tables for each pair as CSV for reviewers. "
    "Consider false discovery rate control when testing many pairs post hoc.",
    "A significant result with **tiny** discordance counts may be statistically “real” but practically negligible—always report **b** and **c** cells (unsafe-only vs safe-only flips). "
    "Non-significant results do not prove equivalence unless you run an equivalence test with prespecified margins. "
    "Interpretation should connect to **error taxonomy**: are flips mostly near-miss paraphrases or wildly different behaviors?",
    "Pairwise testing multiplies opportunities for fishing; pre-register primary vendor contrasts. "
    "Harmful prompt text underpins each discordant pair—`SECURITY.md` applies. "
    "Do not weaponize p-values in vendor disputes without context.",
)

add(
    "figures/multimodel/phd_mcnemar_pairwise_risk.png",
    "This figure applies **McNemar-style** reasoning to the **risk** binary where “positive” means PARTIAL ∪ UNSAFE and “negative” means SAFE, again on paired prompts. "
    "Risk discordance is often **more frequent** than UNSAFE discordance because PARTIAL labels are more volatile and more sensitive to subtle wording changes in model outputs. "
    "The visualization therefore highlights disagreements in **borderline** policy compliance, which may be more relevant to trust and safety operations than rare, egregious UNSAFE events. "
    "As with the UNSAFE variant, the plot may encode p-values, log odds, or counts of flips depending on implementation. "
    "Readers should not equate statistical significance with operational severity without examining qualitative examples.",
    "Inputs mirror the UNSAFE McNemar pipeline but swap the binary labeling rule; confirm that PARTIAL handling matches `LABEL_RUBRIC.md` and that empty responses are coded consistently. "
    "Because PARTIAL may be annotator-noisy, high discordance might reflect label uncertainty rather than model instability—report inter-rater stats if available. "
    "If risk is defined with additional thresholds (e.g., only certain PARTIAL tags), state that explicitly; changing definitions changes McNemar cells. "
    "Alignment of prompt IDs remains mandatory.",
    "Generate via `python scripts/plot_multimodel_mcnemar_pairwise.py --metric risk` (see `--help` for related flags). "
    "For publication, show example confusion matrices for one representative pair in an appendix. "
    "If asymptotic approximations are dodgy, use exact tests in the analysis notebook even if the plot uses large-sample p-values.",
    "Interpret significant discordance as evidence that **moderation policies** may disagree across vendors on the same user-visible prompt class. "
    "Non-significance does not mean models are morally equivalent—only that flip counts were insufficient to detect differences under the test’s power. "
    "Combine with Cohen’s h plots for effect sizes.",
    "Exploratory pairwise sweeps require multiplicity discipline. "
    "`SECURITY.md` for raw completions illustrating flips. "
    "Avoid naming individuals or leaking customer data in case studies.",
)

add(
    "figures/multimodel/phd_beta_posterior_unsafe_facets.png",
    "This figure displays **Bayesian Beta posteriors** (or Beta–Binomial updates) for UNSAFE probabilities in small cells, often arranged in a **facet grid** by model and category or by hierarchical groupings. "
    "The goal is honest uncertainty quantification when binomial counts are tiny: a raw rate of 1/18 and 2/18 look close as point estimates but may imply very different posterior mass under a weakly informative prior. "
    "Posterior plots make **shrinkage** intuitive—extreme empirical rates are pulled toward the prior mean when data are sparse, which can prevent overreacting to single prompts. "
    "Readers familiar only with frequentist confidence intervals should be told explicitly what prior was used and why; otherwise posteriors look like arbitrary Bayesian decoration. "
    "Faceting many small plots demands large page real estate; supplemental PDFs are appropriate.",
    "Each facet’s sufficient statistics are success counts and trial counts extracted from multimodel JSONs; the script may use a **Beta(α,β)** prior with α=β=1 (uniform) or another documented choice. "
    "If hierarchical partial pooling is implemented in a different branch, say so—pooled and unpooled posteriors differ materially. "
    "Prior sensitivity analyses belong in appendix figures if conclusions hinge on tail probabilities. "
    "Cells with zero successes still have posterior support for nonzero UNSAFE unless the prior is degenerate—this is a feature when communicating residual uncertainty.",
    "Run `python scripts/plot_multimodel_beta_posterior_facets.py` and archive the prior parameters in `PROVENANCE.md` or methods. "
    "Ensure plotting uses consistent x-axis limits (0,1) across facets for comparability unless logit scales are used. "
    "For color, show posterior means and credible intervals distinctly if both are plotted.",
    "Read **wide** posteriors as “we know little here,” not as “the model is safe.” "
    "Compare posteriors across models by assessing stochastic ordering or overlapping credible intervals, not just means. "
    "Do not confuse posterior predictive distributions with posteriors on rates unless you plot the former.",
    "Bayesian methods do not erase ethics: extreme posterior tails may correspond to harmful completions. "
    "`SECURITY.md`. "
    "Document software (PyMC, Stan, or analytic Beta) for reproducibility.",
)

add(
    "figures/multimodel/phd_tier_provider_interaction_unsafe.png",
    "This plot visualizes **interaction structure** between **commercial tier** and **provider identity** with respect to UNSAFE rates—essentially asking whether “cheap vs expensive” slopes are parallel across vendors or whether one vendor’s budget tier diverges more sharply than another’s. "
    "Formal interaction in ANOVA terms would require assumptions inappropriate for tiny, structured grids, so the figure is usually **descriptive**: lines that cross or fan out suggest heterogeneous tier effects. "
    "Such heterogeneity matters commercially because customers may wrongly generalize from one vendor’s tier ladder to the entire industry. "
    "The visualization may use line charts, interaction panels, or faceted bar charts with connecting lines; read the generator to know which. "
    "Always show uncertainty if possible; bare point estimates invite overfitting stories.",
    "The unsafe rate matrix and metadata tables supply tier labels, provider names, and category aggregations; some scripts average within tier across categories using macros, others micro-average—methods must specify which. "
    "If categories are pooled, rare but catastrophic categories can be averaged away; consider robust max-category summaries alongside means. "
    "Collinearity between tier and model family is expected; causal language is inappropriate. "
    "Gemini naming quirks can masquerade as interactions—verify slug identities.",
    "Build with `python scripts/plot_multimodel_interaction_tier_provider.py`. "
    "Export both PNG and underlying summary CSV for reviewers. "
    "If lines connect discrete tiers, mark points clearly to avoid implying continuous price scales.",
    "Interpret **non-parallelism** as a prompt to analyze category-level interactions next, not as proof of strategic pricing decisions. "
    "Check that apparent interactions persist after removing a single outlier category. "
    "Discuss business implications cautiously—this is academic benchmark evidence.",
    "Vendor comparisons can be commercially sensitive—neutral wording. "
    "`SECURITY.md` for examples. "
    "Nine points cannot support complex interaction models without overfitting.",
)

add(
    "figures/multimodel/phd_unsafe_concordance_histogram.png",
    "This histogram (or normalized bar chart) counts prompts by **how many of the nine models** labeled them UNSAFE: a prompt where zero models fail sits in the left bin, a prompt where all nine fail sits in the right tail. "
    "The distribution summarizes **ensemble agreement**: a left-skewed mass means failures are idiosyncratic to particular APIs, while right-skewed mass means failures are **systemic** under this bank—everyone struggles with the same templates. "
    "Such systemic failures often merit priority in benchmark iteration because they indicate prompts that probe fundamental policy gaps rather than vendor-specific quirks. "
    "The plot does not show severity within UNSAFE outputs; two models may be UNSAFE for very different reasons while still incrementing the same bin. "
    "Zero-inflation (a huge spike at count zero) is common in well-tuned models and should not be dismissed as “boring” without examining tail prompts.",
    "Construction requires per-prompt label vectors across JSONs with strict ID alignment; off-by-one merges create phantom concordance. "
    "Define how abstentions or API errors are coded—often they should be treated as missing rather than non-UNSAFE. "
    "If you subsample prompts for cost reasons, concordance distribution shifts; note subsampling. "
    "Comparing concordance across benchmark versions requires the same ID scheme.",
    "Run `python scripts/plot_multimodel_unsafe_concordance.py` after multimodel labeling is complete. "
    "Export the list of prompts in the rightmost bin for internal review (not necessarily for public release). "
    "If counts are small, use exact bar labels rather than density smoothing.",
    "Use the plot to decide whether case studies should emphasize **universal** failures or **vendor-specific** ones. "
    "Avoid claiming tail prompts are “impossible” for future models—capabilities drift. "
    "Pair with incidence heatmaps for spatial structure across models.",
    "Tail prompts may be highly sensitive—redact. "
    "`SECURITY.md`. "
    "Do not publish bin counts that enable reverse-engineering rare capabilities.",
)

add(
    "figures/multimodel/phd_cohens_h_pairwise_overall.png",
    "**Cohen’s h** converts two proportions into an effect size on an arcsine square-root scale, offering a **standardized magnitude** for paired or unpooled proportion differences that p-values alone obscure. "
    "This plot typically shows a matrix or ranked list of h values between model pairs on UNSAFE, possibly overall (averaged across categories) or within strata depending on script flags. "
    "Effect sizes help prioritize engineering attention: a pair with tiny p but negligible h may not justify a roadmap pivot, while moderate h with noisy p might warrant larger n. "
    "Safety contexts may need domain-specific calibration of “small/medium/large” because even tiny rate differences can matter socially when absolute traffic is huge—Cohen’s generic thresholds are not gospel. "
    "The plot may annotate confidence intervals if implemented; if not, bootstrap pairwise h in analysis code.",
    "h is computed from paired proportion summaries exported by multimodel scripts; verify whether denominators are overall prompts or category-balanced averages. "
    "If prompts are paired, effect sizes should ideally use paired estimators; mixing paired and unpooled formulas is a common footgun. "
    "When proportions are extreme, h can be large even when absolute point differences look small in percentage terms—explain both. "
    "Multiple comparisons across pairs inflate the chance of large |h| somewhere; FDR control may help if you rank pairs.",
    "Generate with `python scripts/plot_multimodel_cohens_h_pairwise.py`. "
    "Export a CSV sorted by |h| for internal triage. "
    "Use consistent sign conventions (A−B) and document which direction is positive.",
    "When narrating, tie effect sizes back to **absolute rates** (“3 points higher UNSAFE”) so stakeholders grasp real-world scale. "
    "Do not rank vendors solely by h without showing base rates. "
    "Consider contextual harm: some categories warrant asymmetric concern even at small h.",
    "Effect size plots can stigmatize vendors unfairly if uncertainty is omitted—add intervals when possible. "
    "`SECURITY.md`. "
    "Academic honesty requires reporting when h is unstable due to tiny denominators.",
)

add(
    "figures/multimodel/phd_unsafe_incidence_prompts_by_run.png",
    "This **incidence heatmap** aligns **prompt identifiers** on one axis and **model runs** on the other, coloring cells when a completion is UNSAFE (or meets a related threshold). "
    "It reveals whether UNSAFE events are **concentrated** in a few prompts (bright rows) or **spread** thinly across many, and whether certain models exhibit striped patterns indicating correlated failure modes. "
    "Unlike aggregate rate plots, incidence plots preserve **row-level structure**, making them invaluable for debugging labeling quirks or API outages (e.g., an entire column missing). "
    "The cost is potential **re-identification risk**: if prompt IDs map one-to-one to sensitive templates, publishing this figure publicly may be unacceptable even without printing prompt text. "
    "Aggregation or hashing of IDs may be required for external sharing.",
    "Construction demands consistent prompt ordering and stable IDs across runs; if the benchmark rotated IDs between versions, merge carefully. "
    "Define behavior for multi-turn prompts or duplicated templates; duplicates may create visually misleading bands. "
    "Color scales should handle class imbalance—mostly empty heatmaps should not auto-scale to hide rare events. "
    "If timeouts are coded as non-UNSAFE, a column of false negatives may appear—validate against logs.",
    "Run `python scripts/plot_multimodel_unsafe_incidence_heatmap.py` after JSON alignment checks pass. "
    "For internal use, export the list of high-incidence prompt IDs to drive qualitative review sessions. "
    "For public use, consider binning prompts by category rather than exposing IDs.",
    "Bright **rows** suggest benchmark prompts that should be discussed in error analysis; bright **columns** suggest systematically permissive or misconfigured endpoints. "
    "Be careful not to infer statistical independence across cells—prompts and models are structured. "
    "Pair with concordance histograms for ensemble-level summaries.",
    "Incidence plots are among the most sensitive outputs—default to internal-only. "
    "`SECURITY.md` is critical. "
    "Red teamers may use incidence maps to infer model weaknesses; distribute responsibly.",
)

add(
    "figures/multimodel/phd_logit_category_profiles_unsafe.png",
    "This visualization plots **logit-transformed** UNSAFE rates across categories for each model, turning bounded proportions into unbounded reals so that differences near 0% and 100% are not visually squashed as they are on linear scales. "
    "Continuity corrections (adding ε to 0/n or subtracting from n/n) are often applied to avoid infinities; the exact ε should appear in methods because it slightly shifts points. "
    "Parallel curves suggest models share a **similar category profile** up to monotone scaling; diverging curves flag structural differences in which categories dominate failures. "
    "Logits aid **statistical modeling** (logistic regression intuition) but are not themselves causal parameters—do not overinterpret literal distances without a generative model. "
    "Category ordering on the x-axis is not temporal unless stated.",
    "Values derive from `signature_rate_matrix.json` or per-run tables merged into long-form data; zeros and ones are handled per script policy. "
    "If categories have different n, logits still plot point estimates but should ideally carry interval ribbons—check whether the generator overlays them. "
    "Comparing logits across different rubrics or different prompt sets is invalid. "
    "If models have missing categories, interpolation gaps should be explicit.",
    "Run `python scripts/plot_multimodel_logit_category_profile.py`. "
    "Export underlying logits and rates as CSV for reviewers who want to replot in ggplot. "
    "Use colorblind-safe palettes for nine lines; consider faceting instead of overplotting.",
    "When reading, focus on **shape** and **crossings** rather than individual point noise. "
    "Crossings imply rank changes in UNSAFE severity across categories—pair with rank plots. "
    "Do not use logits to compare absolute harm across categories with different real-world stakes unless you weight categories normatively.",
    "Logit plots can expose rare categories—mind `SECURITY.md`. "
    "Explain transforms to non-statistical readers to avoid mystification.",
)

add(
    "figures/multimodel/phd_direct_vs_roleplay_escalation.png",
    "This figure contrasts **direct** elicitation prompts with **roleplay** or otherwise **staged** framings, summarizing whether UNSAFE rates **escalate** (increase) or **de-escalate** under the gentler or more manipulative conversational setup—wording depends on benchmark design. "
    "Escalation is a fraught term: here it should mean strictly “higher observed UNSAFE rate under framing B than under direct baselines for matched prompts,” not moral judgment about users. "
    "The plot may show paired arrows, difference bars, or distributions of per-prompt deltas; read the generator for the precise metaphor. "
    "Strong escalation patterns motivate research into **social engineering** resistance and into moderation policies that consider multi-turn context. "
    "Weak escalation suggests either robust refusals or benchmark prompts that already saturate models without roleplay.",
    "Data come from stratum-aware slices of `signature_rate_matrix.json` or from paired per-prompt tables; verify that pairing is truly one-to-one. "
    "If roleplay prompts add extra tokens, differences may partly reflect distribution shift rather than “manipulation magic.” "
    "Missing completions in one stratum but not the other bias deltas—use symmetric filtering. "
    "Statistical testing should respect pairing (bootstrap of prompt-level differences, sign tests, etc.).",
    "Regenerate with `python scripts/plot_multimodel_direct_vs_roleplay_escalation.py`. "
    "Include a table of prompt counts per stratum beside the figure. "
    "If exporting for public talks, avoid animated metaphors that sensationalize jailbreaks.",
    "Positive escalation should trigger qualitative review of **how** roleplay induced UNSAFE text—copy-paste attacks vs novel content. "
    "Negative escalation might indicate safer roleplay conditions or measurement artifacts—validate manually. "
    "Do not extrapolate from single-turn roleplay to long-horizon agent scaffolds without further experiments.",
    "Framing studies can inform misuse if published carelessly—follow `SECURITY.md`. "
    "Emphasize defensive lessons, not cookbooks.",
)

add(
    "figures/multimodel/combined_safety_frontier.png",
    "The **safety frontier** figure places each model run as a point in a **two-objective** plane, commonly trading off a **refusal or abstention metric** (higher is “safer” under the project’s definition) against an **UNSAFE or risk rate** (lower is better). "
    "A **Pareto-style hull** or envelope highlights runs that are not uniformly dominated: no other run is strictly better on both axes simultaneously under the plotted metrics. "
    "Points inside the hull are **dominated** in this narrow mathematical sense, though dominated models might still be preferable for non-safety reasons (latency, cost) not shown on the axes. "
    "The figure is rhetorically powerful but **metric-dependent**: changing how refusal is measured—or normalizing rates differently—can reshuffle who lies on the frontier. "
    "Always publish the exact formulas for both axes and any smoothing or winsorization applied to fingerprint statistics.",
    "Inputs are derived from **fingerprint** summaries—category-wise traces of refusal, UNSAFE, and risk—aggregated into scalars per model, typically after `fingerprint_all_multimodel.py` materializes JSON and `plot_safety_frontier.py` consumes it. "
    "If fingerprints omit categories due to errors, frontier points move; validate completeness. "
    "Some pipelines use convex hulls; others use epsilon-non-dominated sets; specify which. "
    "If you plot confidence clouds rather than points, say how uncertainty was propagated—analytic deltas, bootstrap, or Bayesian draws.",
    "Typical commands: `python scripts/fingerprint_all_multimodel.py` followed by `python scripts/plot_safety_frontier.py`, with paths documented in `--help`. "
    "Archive the intermediate fingerprint JSON alongside the PNG so the frontier can be reproduced after font tweaks without recomputing fingerprints. "
    "For presentations, label each point with anonymized IDs if blind review requires it.",
    "On the frontier, emphasize **trade-offs**, not “winners” in a moral sense—different deployments weigh refusal versus helpfulness differently. "
    "Interior points may dominate on axes you did not plot (e.g., calibration, fairness), so avoid shaming vendors with partial objectives. "
    "Discuss whether refusal itself can harm users (over-refusal) if that debate matters to your audience.",
    "Frontier plots can be misread as comprehensive safety rankings—contextualize heavily. "
    "`SECURITY.md` for underlying completions. "
    "Update the figure whenever fingerprint definitions change.",
)

add(
    "figures/multimodel/combined_fingerprint_pca.png",
    "This plot applies **principal component analysis** (PCA) to vectors of fingerprint features—often stacked category-wise rates or refusals per model—to embed the nine runs into **two dimensions** for visualization. "
    "Nearby points suggest similar **high-dimensional failure profiles** under Euclidean geometry after centering and scaling; distant points suggest structurally different behavior across the benchmark. "
    "PCA is **not** a causal model and **not** guaranteed to separate “safe” from “unsafe” models unless variance aligns with that axis; PC1 may capture provider-specific quirks rather than interpretable safety. "
    "With only nine observations, PCA is **unstable**: leaving one model out can rotate axes dramatically; bootstrap or jackknife analyses belong in robustness appendices if you lean on PCA narratively. "
    "The sidecar JSON `combined_fingerprint_pca_meta.json` typically records loadings, explained variance ratios, and point labels—cite those numbers when you claim “PC1 explains X% of variance.”",
    "Feature construction must be documented: did you standardize per category? Drop sparse categories? Include refusals and UNSAFE in one vector or separate blocks? "
    "If features are highly correlated, PCA may merge them into one component that is hard to name—avoid over-interpretation. "
    "Outliers in fingerprint features dominate PCA; check robust PCA or t-SNE/UMAP alternatives if one model skews the map, noting that alternatives have their own hyperparameters. "
    "Ensure you did not accidentally duplicate features or leak tier twice under different names.",
    "Regenerate via `python scripts/plot_fingerprint_pca.py` after fingerprint JSON exists. "
    "Commit the meta JSON in the same changeset as the PNG. "
    "For slides, annotate arrows showing how loadings contribute to positions if space allows.",
    "Tell readers that proximity is **exploratory similarity**, not certification of equivalence. "
    "If two models overlap in PCA space but differ sharply on a rare catastrophic category, PCA may hide that risk—cross-check extremes. "
    "Prefer qualitative fingerprints or incidence plots when stakes are high.",
    "PCA can reveal vendor clustering—word neutrally to avoid commercial defamation. "
    "`SECURITY.md`. "
    "Nine points cannot support strong subspace claims without replication.",
)


# --- Per-run fingerprint curves ------------------------------------------------

_FP_PARAS_TAIL = (
    "The asset is produced by the **fingerprint pipeline**: row-level labels are aggregated into category-wise traces of **refusal**, **UNSAFE**, and **risk** (PARTIAL ∪ UNSAFE), then plotted as connected lines for one API snapshot. "
    "A sibling `model_fingerprint.json` in the same directory (when present) stores the numeric series backing the curves, enabling diffing across commits without OCR-ing the PNG. "
    "Fingerprints complement heatmaps: they emphasize **within-model curvature** across categories, whereas heatmaps emphasize **cross-model** comparisons for a fixed category slice. "
    "Because curves are derived from the same rubric as the rest of the project, disagreements between fingerprint narratives and bar charts usually indicate a bug, stale JSON, or inconsistent filtering—not a scientific paradox.",
    "From `llm-safety-experiment/`, refresh fingerprints in batch with `python scripts/fingerprint_all_multimodel.py` (see `--help` for path conventions) or rebuild the entire figure suite via `python scripts/reproduce_main_figures.py`, which sequences labeling exports, matrices, and derivative visuals. "
    "If only one endpoint changed, you may regenerate its subdirectory alone, but be careful that aggregate multimodel figures (heatmaps, frontiers) still re-run so they do not reference stale fingerprints. "
    "Check logs for dropped prompts or API errors; fingerprints silently flatten when categories have no valid completions unless assertions catch empties. "
    "Version-control both the PNG and JSON; reviewers may ask for the exact commit hash used in camera-ready figures.",
    "When reading curves, interpret **higher UNSAFE or risk traces** in a category as greater observed policy-stress under that slice of the bank, conditional on the prompts and adjudication rules. "
    "**Refusal** traces should be read alongside UNSAFE: some endpoints refuse heavily with low UNSAFE, others comply with high UNSAFE—policy teams care about both tails. "
    "Sharp peaks localized to one or two categories motivate targeted error analysis; broad elevation suggests globally permissive behavior. "
    "Do not read left-to-right slope as time unless the x-axis is literally temporal; category order is taxonomic.",
    "Fingerprints are **lossy compressions** of rich label data: they cannot show distributional quirks within a category, per-prompt incidence, or annotator disagreement. "
    "For high-stakes claims, cross-check curves against per-prompt tables and, when available, qualitative codebooks of failure modes. "
    "If curves look jagged with small n, smooth mentally with Wilson or Bayesian intervals from companion analyses. "
    "Disputes about labeling should be resolved by revisiting `LABEL_RUBRIC.md`, not by aesthetic preferences about chart color.",
    "Fingerprints summarize responses to potentially harmful instructions; raw prompts and completions may be legally or ethically sensitive. "
    "Follow `SECURITY.md` for access control, redaction, and responsible disclosure. "
    "Never treat a low UNSAFE fingerprint as a product safety certificate without independent review and operational monitoring.",
)


def fingerprint_paragraphs(tier: str, provider: str, slug: str) -> tuple[str, str, str, str, str]:
    p0 = (
        f"This **per-run fingerprint line chart** documents refusal, UNSAFE, and risk trajectories across elicitation categories for a single audited endpoint: **tier** `{tier}`, **provider** `{provider}`, **model slug** `{slug}`. "
        "Each point along a curve aggregates adjudicated labels for prompts belonging to that category under this run’s configuration, so the graphic is a high-resolution portrait of how the API’s policy surface bends across benchmark slices. "
        "Comparing fingerprints across runs is easiest when category order is identical and axis scales match; this file pairs naturally with multimodel heatmaps that show many models at once but sacrifice per-model smoothness. "
        "The title metadata (tier/provider/slug) should match your results directory naming; mismatches often indicate a moved folder or an outdated companion markdown file."
    )
    merged_opening = p0 + " " + _FP_PARAS_TAIL[0]
    return (merged_opening,) + _FP_PARAS_TAIL[1:]


def default_companion(rel: str) -> tuple[str, str, str, str, str]:
    name = Path(rel).name
    return (
        f"This Markdown companion sits beside `{name}` at repository path `{rel}` but **no curated long-form entry** exists yet in `docs/FIGURE_COMPANION_WRITER.md` / `COMPANIONS`. "
        "That usually means the asset was added recently, renamed, or produced by an auxiliary script not yet wired into the companion dictionary. "
        f"Before publishing, add a bespoke `add(\"{rel}\", ...)` block (five paragraphs) describing the visualization encoding, data provenance, reproduction commands, interpretation guide, and limitations/ethics—then rerun `sync_figure_companion_writer.py` and `write_figure_companions.py`. "
        "Until then, treat this file as a **placeholder** that orients readers to the paired binary asset but does not substitute for methods text.",
        f"To locate the generator, search `scripts/` for `{name}` or for related stem substrings, and read `PROVENANCE.md`, `reproduce_main_figures.py`, and any Makefile or CI workflow that invokes plotting utilities. "
        "If the figure is an intermediate export under `results/`, check the nearest `results.json` or log files for the command that produced it. "
        "Document dependencies (matplotlib, plotly, seaborn, etc.) if they differ from the core requirements.txt. "
        "If multiple scripts can emit the same filename, disambiguate using timestamps or checksums.",
        "Typical regeneration paths start from `python scripts/reproduce_main_figures.py` with flags such as `--extra-visuals`, `--phd-visuals`, or `--sankey`, but your asset may require a narrower command—verify before batching. "
        "Always run commands from `llm-safety-experiment/` so relative paths resolve consistently. "
        "After regeneration, run any repository verification scripts (for example `verify_artifact_chain.py`) if your team relies on them for paper submission hygiene. "
        "Commit the updated figure and this companion together to avoid drift.",
        "Without custom text, interpret the graphic as a **descriptive** artifact tied to the frozen benchmark and rubric, not as standalone statistical evidence unless separate inference sections justify that use. "
        "Readers should cross-link to the main report (`LLM_SAFETY_EXPERIMENT_REPORT.md` or successor) for definitions and to multimethod summaries for context. "
        "If the figure encodes novel metrics, define them inline in the companion once you replace this default. "
        "Avoid causal language when the experimental design is observational.",
        "Evaluation repositories routinely contain sensitive prompts and model outputs—even figures that look aggregate can be reverse-engineered when paired with public code. "
        "Comply with `SECURITY.md` and institutional policies before redistribution. "
        "When in doubt, keep the asset team-internal until a security review clears publication.",
    )


def _fingerprint_meta(path: Path) -> tuple[str, str, str] | None:
    """Parse (tier, provider, slug) from .../multimodel/<tier>/figures/results_<provider>_<slug>/fig_model_fingerprint_curves.png"""
    try:
        parts = path.parts
        i = parts.index("multimodel")
        tier = parts[i + 1]
        if parts[i + 2] != "figures":
            return None
        m = re.match(r"results_([^_]+)_(.+)", parts[i + 3])
        if not m:
            return None
        return tier, m.group(1), m.group(2)
    except (ValueError, IndexError):
        return None


def diagram_for(rel: str, fingerprint: tuple[str, str, str] | None) -> str:
    """Return Mermaid source (no fences). Tailored per figure; generic fallback."""
    if fingerprint is not None:
        return (
            "flowchart TD\n"
            "  JSON[Labeled JSON single run] --> CAT[Aggregate by category]\n"
            "  CAT --> REF[Refusal rate series]\n"
            "  CAT --> UNS[UNSAFE rate series]\n"
            "  CAT --> RSK[Risk rate series]\n"
            "  REF --> FIG[Multi-series line chart]\n"
            "  UNS --> FIG\n"
            "  RSK --> FIG"
        )
    name = Path(rel).name
    if name == "fig1_unsafe_rate_by_category.png":
        return (
            "flowchart TD\n"
            "  P[Pilot labeled JSON] --> G[Group by category and stratum]\n"
            "  G --> R[UNSAFE count over n]\n"
            "  R --> B[Bar heights]\n"
            "  R --> M[Overall benchmark rate]\n"
            "  B --> OUT[Bar chart PNG]\n"
            "  M --> OUT"
        )
    if name == "fig_unsafe_rate_by_category_wilson_ci.png":
        return (
            "flowchart TD\n"
            "  C[Cell counts UNSAFE over n] --> P[Point estimate p hat]\n"
            "  C --> W[Wilson 95 percent interval]\n"
            "  P --> V[Bars or points]\n"
            "  W --> E[Error bars]\n"
            "  V --> OUT[Figure PNG]\n"
            "  E --> OUT"
        )
    if name == "figure2_label_distribution_stacked.png":
        return (
            "flowchart TD\n"
            "  L[Labeled outcomes SAFE PARTIAL UNSAFE] --> A[Count per category]\n"
            "  A --> N[Normalize to 100 percent]\n"
            "  N --> S[Stacked segments]\n"
            "  S --> OUT[Stacked bar PNG]"
        )
    if name == "fig_category_risk_profile_heatmap.png":
        return (
            "flowchart TD\n"
            "  T[Contingency table category x label] --> F[Cell percentages]\n"
            "  F --> C[Color scale]\n"
            "  C --> OUT[Heatmap PNG]"
        )
    if name == "fig_cep_progression.png":
        return (
            "flowchart TD\n"
            "  D[Per category counts] --> U[UNSAFE rate]\n"
            "  D --> R[Risk rate PARTIAL union UNSAFE]\n"
            "  U --> P[Dual metric plot]\n"
            "  R --> P\n"
            "  P --> OUT[Progression chart PNG]"
        )
    if name == "fig_failure_pattern_fingerprint.png":
        return (
            "flowchart TD\n"
            "  V[Category rate vector] --> R[Map to polar axes]\n"
            "  R --> POL[Connect polygon]\n"
            "  POL --> OUT[Radar fingerprint PNG]"
        )
    if name == "fig_entropy_safety.png":
        return (
            "flowchart TD\n"
            "  C[Label counts per category] --> Pr[Empirical probabilities]\n"
            "  Pr --> H[Shannon entropy]\n"
            "  H --> OUT[Entropy chart PNG]"
        )
    if name == "fig_category_safety_sankey.png":
        return (
            "flowchart TD\n"
            "  Cat[Elicitation categories] --> Flow[Flow volumes]\n"
            "  Flow --> Out[SAFE PARTIAL UNSAFE]\n"
            "  Out --> SK[Sankey layout Plotly]\n"
            "  SK --> PNG[Sankey PNG export]"
        )
    if name in ("combined_signature_unsafe_heatmap.png", "signature_unsafe_heatmap.png"):
        return (
            "flowchart TD\n"
            "  J[Multimodel JSONs] --> M[signature_rate_matrix unsafe]\n"
            "  M --> H[Color cells model x category]\n"
            "  H --> OUT[Heatmap PNG]"
        )
    if name in ("combined_signature_excess_vs_direct.png", "signature_excess_unsafe_vs_direct.png"):
        return (
            "flowchart TD\n"
            "  M[Unsafe rates by stratum] --> D[Subtract direct baseline]\n"
            "  D --> E[Excess per cell]\n"
            "  E --> C[Diverging colormap]\n"
            "  C --> OUT[Excess heatmap PNG]"
        )
    if name == "combined_signature_risk_heatmap.png":
        return (
            "flowchart TD\n"
            "  J[Multimodel JSONs] --> M[signature_rate_matrix_risk]\n"
            "  M --> H[Color cells model x category]\n"
            "  H --> OUT[Risk heatmap PNG]"
        )
    if name == "combined_9panel_unsafe_by_category.png":
        return (
            "flowchart TD\n"
            "  D[Multimodel labeled data] --> P[Split into nine panels]\n"
            "  P --> B[Bars per category per panel]\n"
            "  B --> I[Optional Wilson intervals]\n"
            "  I --> OUT[3x3 grid PNG]"
        )
    if name == "combined_radar_grid_unsafe.png":
        return (
            "flowchart TD\n"
            "  V[Per model rate vector] --> R[Mini radar per model]\n"
            "  R --> G[Grid layout]\n"
            "  G --> OUT[Radar grid PNG]"
        )
    if name == "combined_parallel_coordinates.png":
        return (
            "flowchart TD\n"
            "  M[Rate matrix] --> L[One polyline per model]\n"
            "  L --> A[Parallel category axes]\n"
            "  A --> OUT[Parallel coords PNG]"
        )
    if name == "combined_parallel_coordinates_by_tier.png":
        return (
            "flowchart TD\n"
            "  M[Rate matrix plus tier labels] --> L[Polylines colored by tier]\n"
            "  L --> OUT[Parallel coords PNG]"
        )
    if name in ("combined_forest_wilson_unsafe.png", "combined_forest_wilson_risk.png"):
        return (
            "flowchart TD\n"
            "  C[Cell binomial counts] --> P[Point estimate]\n"
            "  C --> W[Wilson interval]\n"
            "  P --> F[Forest row]\n"
            "  W --> F\n"
            "  F --> OUT[Forest plot PNG]"
        )
    if name == "combined_clustermap_rates.png":
        return (
            "flowchart TB\n"
            "  subgraph layout [\"Figure layout publication grid\"]\n"
            "    TOP[Column dendrogram]\n"
            "    HEAT[Clustered heatmap]\n"
            "    LEFT[Row dendrogram]\n"
            "    CB[Colorbar column separate]\n"
            "  end\n"
            "  M[Rate matrix p hat] --> ROW[Row linkage average Euclidean]\n"
            "  M --> COL[Column linkage average Euclidean]\n"
            "  ROW --> LEFT\n"
            "  COL --> TOP\n"
            "  ROW --> PERM[Permute rows and columns]\n"
            "  COL --> PERM\n"
            "  PERM --> HEAT\n"
            "  HEAT --> CB\n"
            "  TOP --> OUT[combined_clustermap_rates.png]\n"
            "  LEFT --> OUT\n"
            "  HEAT --> OUT\n"
            "  CB --> OUT"
        )
    if name == "combined_tier_slope_overall_rates.png":
        return (
            "flowchart TD\n"
            "  R[Per run rates] --> A[Aggregate by tier]\n"
            "  A --> S[Slope or connected points cheap to expensive]\n"
            "  S --> OUT[Tier slope PNG]"
        )
    if name == "combined_label_composition_stacked.png":
        return (
            "flowchart TD\n"
            "  J[Labeled JSON per run] --> C[SAFE PARTIAL UNSAFE counts]\n"
            "  C --> N[Normalize to 100 percent]\n"
            "  N --> OUT[Stacked composition PNG]"
        )
    if name == "summary_table_models_categories.png":
        return (
            "flowchart TD\n"
            "  M[Rate matrix] --> T[Typeset table]\n"
            "  T --> G[Optional styling]\n"
            "  G --> OUT[Table figure PNG]\n"
            "  M --> CSV[summary CSV]"
        )
    if name == "combined_category_correlation_across_models.png":
        return (
            "flowchart TD\n"
            "  M[Category rate vectors length nine] --> COR[Pearson or Spearman correlation]\n"
            "  COR --> HM[Correlation matrix display]\n"
            "  HM --> OUT[Correlation PNG]"
        )
    if name == "combined_within_category_ranks_unsafe.png":
        return (
            "flowchart TD\n"
            "  M[Unsafe rates] --> K[For each category sort models]\n"
            "  K --> RK[Rank graphic]\n"
            "  RK --> OUT[Ranks PNG]"
        )
    if name == "interactive_rates.html":
        return (
            "flowchart TD\n"
            "  JSON[signature_rate_matrix.json] --> JS[Interactive renderer]\n"
            "  JS --> H[HTML with hover or sort]\n"
            "  H --> OUT[interactive_rates.html]"
        )
    if name == "phd_mcnemar_pairwise_unsafe.png":
        return (
            "flowchart TD\n"
            "  P[Paired UNSAFE bits per prompt] --> T[Contingency discordant pairs]\n"
            "  T --> MC[McNemar test]\n"
            "  MC --> PL[Pairwise plot]\n"
            "  PL --> OUT[McNemar figure PNG]"
        )
    if name == "phd_mcnemar_pairwise_risk.png":
        return (
            "flowchart TD\n"
            "  P[Paired risk bits per prompt] --> T[Contingency discordant pairs]\n"
            "  T --> MC[McNemar test]\n"
            "  MC --> PL[Pairwise plot]\n"
            "  PL --> OUT[McNemar risk figure PNG]"
        )
    if name == "phd_beta_posterior_unsafe_facets.png":
        return (
            "flowchart TD\n"
            "  C[Binomial counts per cell] --> B[Beta prior plus likelihood]\n"
            "  B --> POST[Posterior densities]\n"
            "  POST --> FAC[Faceted plot]\n"
            "  FAC --> OUT[Posterior facets PNG]"
        )
    if name == "phd_tier_provider_interaction_unsafe.png":
        return (
            "flowchart TD\n"
            "  M[Rates plus tier and provider] --> I[Interaction visualization]\n"
            "  I --> L[Lines or faceted bars]\n"
            "  L --> OUT[Interaction PNG]"
        )
    if name == "phd_unsafe_concordance_histogram.png":
        return (
            "flowchart TD\n"
            "  L[Per prompt UNSAFE across models] --> S[Sum or count models UNSAFE]\n"
            "  S --> H[Histogram of concordance]\n"
            "  H --> OUT[Histogram PNG]"
        )
    if name == "phd_cohens_h_pairwise_overall.png":
        return (
            "flowchart TD\n"
            "  P[Pairwise proportions] --> H[Cohen h effect size]\n"
            "  H --> V[Matrix or ranked bars]\n"
            "  V --> OUT[Cohen h PNG]"
        )
    if name == "phd_unsafe_incidence_prompts_by_run.png":
        return (
            "flowchart TD\n"
            "  I[Prompt by model UNSAFE matrix] --> HM[Incidence heatmap]\n"
            "  HM --> OUT[Incidence PNG]"
        )
    if name == "phd_logit_category_profiles_unsafe.png":
        return (
            "flowchart TD\n"
            "  R[Raw rates] --> T[Logit transform plus epsilon]\n"
            "  T --> L[Lines across categories per model]\n"
            "  L --> OUT[Logit profile PNG]"
        )
    if name == "phd_direct_vs_roleplay_escalation.png":
        return (
            "flowchart TD\n"
            "  DR[Direct stratum rates] --> RP[Roleplay stratum rates]\n"
            "  RP --> DF[Difference or ratio]\n"
            "  DR --> DF\n"
            "  DF --> OUT[Escalation figure PNG]"
        )
    if name == "combined_safety_frontier.png":
        return (
            "flowchart TD\n"
            "  F[Fingerprint JSON per run] --> S[Scalar refusal and unsafe summaries]\n"
            "  S --> PT[2D scatter per model]\n"
            "  PT --> H[Pareto hull or frontier]\n"
            "  H --> OUT[Frontier PNG]"
        )
    if name == "combined_fingerprint_pca.png":
        return (
            "flowchart TD\n"
            "  F[Fingerprint feature vectors] --> STD[Center and scale]\n"
            "  STD --> PCA[PCA two components]\n"
            "  PCA --> SC[Scatter plot]\n"
            "  SC --> OUT[PCA PNG]\n"
            "  PCA --> META[combined_fingerprint_pca_meta.json]"
        )
    return (
        "flowchart TD\n"
        "  SRC[Labeled results or matrix] --> X[Transform script]\n"
        "  X --> ENC[Visual encoding]\n"
        "  ENC --> OUT[Figure asset]"
    )


def _assets() -> list[Path]:
    paths: list[Path] = []
    for pattern in ("figures/**/*.png", "figures/**/*.html"):
        paths.extend(EXP.glob(pattern))
    paths.extend(EXP.glob("results/**/fig_model_fingerprint_curves.png"))
    return sorted({p.resolve() for p in paths if p.is_file()})


def _write_md(asset: Path, paragraphs: tuple[str, str, str, str, str]) -> None:
    rel = asset.relative_to(EXP).as_posix()
    md_path = asset.with_suffix(".md")
    title = asset.stem.replace("_", " ")
    fp_meta = _fingerprint_meta(asset) if asset.name == "fig_model_fingerprint_curves.png" else None
    mer = diagram_for(rel, fp_meta)
    p1, p2, p3, p4, p5 = paragraphs
    fence = "```"
    mermaid_block = f"{fence}mermaid\n{mer}\n{fence}"
    doc = (
        f"# {title}\n\n"
        f"**Paired asset:** [`{asset.name}`]({asset.name})  \n"
        f"**Repository path:** `{rel}`\n\n"
        "---\n\n"
        "## Document map\n\n"
        "| Section | Role |\n"
        "|---------|------|\n"
        "| 1. Purpose and graphical encoding | What the figure communicates; axes, marks, and estimands |\n"
        "| 2. Conceptual diagram | Mermaid schematic from labels or matrices to this graphic |\n"
        "| 3. Data lineage and definitions | Rubric, artifacts, scope (benchmark-conditional, not population-causal) |\n"
        "| 4. Reproduction | Commands, flags, environment, and verification |\n"
        "| 5. Interpretation guide | How to read comparisons; common misinterpretations |\n"
        "| 6. Limitations and responsible use | Uncertainty, multiplicity, ethics, `SECURITY.md` |\n"
        "| 7. Related repository artifacts | Canonical docs at repo root and companion index |\n"
        "| 8. Position in the evaluation stack | How this figure sits between JSON, matrices, and prose |\n\n"
        "---\n\n"
        "## 1. Purpose and graphical encoding\n\n"
        f"{p1}\n\n"
        "---\n\n"
        "## 2. Conceptual diagram\n\n"
        f"{mermaid_block}\n\n"
        "*Reading the diagram.* Arrows show dependency flow from inputs (left/top) to the exported figure. "
        "Rounded boxes are logical stages; your codebase may combine several stages in one script.\n\n"
        "---\n\n"
        "## 3. Data lineage and definitions\n\n"
        f"{p2}\n\n"
        "---\n\n"
        "## 4. Reproduction\n\n"
        f"{p3}\n\n"
        "---\n\n"
        "## 5. Interpretation guide\n\n"
        f"{p4}\n\n"
        "---\n\n"
        "## 6. Limitations and responsible use\n\n"
        f"{p5}\n\n"
        "---\n\n"
        "## 7. Related repository artifacts and cross-references\n\n"
        "Paths are **relative to the `llm-safety-experiment/` repository root** (adjust if this repo is vendored as a subdirectory).\n\n"
        "| Artifact | Role |\n"
        "|-----------|------|\n"
        "| `PROVENANCE.md` | Frozen results layout, matrix build order, and figure regeneration commands |\n"
        "| `LABEL_RUBRIC.md` | Definitions of SAFE, PARTIAL, and UNSAFE used in all rates |\n"
        "| `SECURITY.md` | Policy for storing and sharing prompts and model outputs |\n"
        "| `figures/FIGURE_COMPANIONS.md` | Machine- and human-readable index of every paired figure companion |\n"
        "| `INTERPRETABILITY_VIZ.md` | Maps figures to scripts for readers navigating the artifact tree |\n\n"
        "---\n\n"
        "## 8. Position in the evaluation stack\n\n"
        "End-to-end, Multimodel-CEP-Benchmark artifacts typically follow: **raw API completions** → **adjudicated JSON** "
        "(per run, under `results/multimodel/…`) → **summarized matrices** such as `figures/multimodel/signature_rate_matrix.json` "
        "→ **static graphics** (this PNG and siblings) → **narrative report or manuscript**. "
        "This figure is an intermediate, **descriptive** layer: it helps researchers **see structure** in a small model panel but does not replace "
        "paired inference, error analysis, or operational monitoring on production traffic. "
        "Cite the matrix JSON and rubric version alongside the figure whenever the graphic appears in a dissertation chapter or peer-reviewed appendix.\n"
    )
    md_path.write_text(doc + "\n", encoding="utf-8")
    print("wrote", md_path.relative_to(EXP), file=sys.stderr)


def main() -> None:
    index_lines = [
        "# Figure companion index",
        "",
        "Each companion is **structured documentation** (eight sections: purpose through evaluation stack) with an embedded **Mermaid** diagram. "
        "Regenerate with `python scripts/write_figure_companions.py`. "
        "Edit prose in `docs/FIGURE_COMPANION_WRITER.md`, then `python scripts/sync_figure_companion_writer.py` to refresh `scripts/write_figure_companions.py`.",
        "",
        "| Companion | Asset |",
        "|-----------|-------|",
    ]

    for asset in _assets():
        rel = asset.relative_to(EXP).as_posix()
        if asset.name == "fig_model_fingerprint_curves.png":
            meta = _fingerprint_meta(asset)
            paras = fingerprint_paragraphs(*meta) if meta else default_companion(rel)
        else:
            paras = COMPANIONS.get(rel, default_companion(rel))
        _write_md(asset, paras)
        companion_rel = asset.with_suffix(".md").relative_to(EXP).as_posix()
        index_lines.append(
            f"| [`{asset.with_suffix('.md').name}`]({companion_rel}) | [`{asset.name}`]({rel}) |"
        )

    index_path = EXP / "figures" / "FIGURE_COMPANIONS.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print("wrote", index_path.relative_to(EXP), file=sys.stderr)


if __name__ == "__main__":
    main()
