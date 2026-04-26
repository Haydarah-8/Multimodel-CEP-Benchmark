# Contributing to Multimodel-CEP-Benchmark

Thank you for helping improve this **open empirical safety evaluation** artifact. This guide is the **canonical** contributor reference for the repository (GitHub surfaces it from the root). Package-local paths below are relative to [`llm-safety-experiment/`](llm-safety-experiment/) unless noted.

---

## 1. Scope and principles

**In scope:** bug fixes, reproducibility repairs, documentation and figure-caption clarity, strict audit compliance for committed JSON, responsible extensions that preserve **estimand definitions** (see [`README.md`](README.md) and [`llm-safety-experiment/docs/RESEARCH_MONOGRAPH.md`](llm-safety-experiment/docs/RESEARCH_MONOGRAPH.md)).

**Out of scope or require maintainer discussion:** changing the **frozen prompt bank** or **primary rubric** without a versioned migration; removing or rewriting **committed research records** in ways that break replication hashes; requests that imply **non-consensual** red teaming or **illegal** use of model APIs.

**Communication:** follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). **Security-sensitive reports** (e.g. leaked credentials) must not use public issues—see [`SECURITY.md`](SECURITY.md).

### 1.1 Community and enforcement contact

**Code of Conduct enforcement:** maintainers must set the contact in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) (replace `[INSERT CONTACT METHOD]`). Until that is set, use the repository owner’s documented support channel or GitHub mechanisms appropriate to your situation.

---

## 2. Ways to contribute

| Track | Examples | Typical artifacts |
| ----- | -------- | ----------------- |
| **Bugs** | Script crashes, wrong path in docs, CI failure on `main` | Code or doc PR |
| **Reproducibility** | Figure does not match JSON after documented command | Issue + PR with audit output |
| **Documentation** | Monograph clarity, README cross-links, companion figure `.md` | Doc-only PR |
| **Analysis / figures** | New diagnostic plot behind a flag, clearer uncertainty display | Code + regenerated PNG/HTML if policy allows |
| **Methodology discussion** | Estimands, rubric edge cases | Issue or discussion (no PR required) |

Substantive **methodological** changes should cite **where** in [`LABEL_RUBRIC.md`](llm-safety-experiment/LABEL_RUBRIC.md), [`REPLICATION_PROTOCOL.md`](llm-safety-experiment/REPLICATION_PROTOCOL.md), or the monograph the behavior is defined, so reviewers can assess **backward compatibility** with frozen results.

---

## 3. Repository map

- **Root:** project `README.md`, [`LICENSE`](LICENSE), [`SECURITY.md`](SECURITY.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), this file, [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
- **[`llm-safety-experiment/`](llm-safety-experiment/):** Python entrypoints, `scripts/`, committed **`results/`** JSON, **`figures/`**, long-form reports, `PROVENANCE.md`, `CITATION.cff`.

Continuous integration runs with **`working-directory: llm-safety-experiment`** (see workflow file). Local commands below assume you `cd llm-safety-experiment` unless you prefix paths.

---

## 4. Development environment

- **Python:** 3.10+ recommended; CI uses 3.12.
- **Install:**

  ```bash
  cd llm-safety-experiment
  python -m venv .venv
  # Windows PowerShell:
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

- **Secrets:** use a local `.env` or your shell; **never** commit API keys. See [`llm-safety-experiment/README.md`](llm-safety-experiment/README.md).

---

## 5. Integrity and the CI contract

This project’s credibility rests on **bit-reproducible** or **audit-verifiable** committed artifacts.

### 5.1 Multimodel strict audit

After any change that touches **labeled** multimodel JSON under `results/`:

```bash
cd llm-safety-experiment
python scripts/audit_multimodel_artifacts.py
python scripts/audit_multimodel_artifacts.py --strict
```

**Non-strict** mode may be useful for exploratory branches; **`--strict`** is what **CI** runs and what `main` should satisfy. If strict fails, read the script’s diagnostics and [`llm-safety-experiment/docs/ARTIFACT_INTEGRITY.md`](llm-safety-experiment/docs/ARTIFACT_INTEGRITY.md).

### 5.2 Pilot / legacy chain

When working on the pilot artifact chain:

```bash
cd llm-safety-experiment
python scripts/verify_artifact_chain.py
```

### 5.3 Byte-compilation

CI runs `compileall` on `scripts/`, `prompt_mutations/`, and top-level modules. Before pushing:

```bash
cd llm-safety-experiment
python -m compileall -q scripts prompt_mutations
python -m compileall -q run_experiment.py run_multi_model.py analyze_results.py provider_clients.py paths.py _label_audit_mid.py
```

---

## 6. Regenerating figures (no API calls)

From `llm-safety-experiment/`:

```bash
python scripts/reproduce_main_figures.py
python scripts/reproduce_main_figures.py --extra-visuals --phd-visuals
```

Use **`--skip-pilot`** or **`--skip-fingerprints`** when only a subset of artifacts changed. Exact script-level commands and outputs are indexed in [`llm-safety-experiment/PROVENANCE.md`](llm-safety-experiment/PROVENANCE.md).

**Figure companions:** auto-generated Markdown siblings for PNGs/HTML are produced by `scripts/write_figure_companions.py` (source prose in `docs/FIGURE_COMPANION_WRITER.md`). If you change companion text, run the sync script then the writer—see [`llm-safety-experiment/docs/FIGURE_COMPANION_WRITER.md`](llm-safety-experiment/docs/FIGURE_COMPANION_WRITER.md).

---

## 7. Change types and review expectations

| Change | Reviewers will check |
| ------ | -------------------- |
| **Code only** | Tests/compile, clarity, no accidental path breaks |
| **`results/**/*.json`** | `audit_multimodel_artifacts.py --strict`, diff size and rationale |
| **Generated figures** | Matching commands in PR description; no spurious binary churn |
| **Prompts / outputs** | Ethics note, alignment with `SECURITY.md` and README responsible-use section |

Prefer **small, focused PRs**; bundle **doc + audit fix** when a JSON change forces figure regeneration.

---

## 8. Pull requests

Use the [pull request template](.github/pull_request_template.md). In summary:

- Describe **what** changed and **why**.
- Note **commands run** (audit, reproduce figures, compileall).
- Confirm **no secrets** and no **machine-specific** absolute paths in committed files.

---

## 9. Documentation and citation

- **Primary narrative:** [`llm-safety-experiment/docs/RESEARCH_MONOGRAPH.md`](llm-safety-experiment/docs/RESEARCH_MONOGRAPH.md)
- **Multimodel manuscript:** [`llm-safety-experiment/docs/MULTIMODEL_MANUSCRIPT.md`](llm-safety-experiment/docs/MULTIMODEL_MANUSCRIPT.md)
- **Docs index:** [`llm-safety-experiment/docs/README.md`](llm-safety-experiment/docs/README.md)
- **Long technical report:** [`llm-safety-experiment/LLM_SAFETY_EXPERIMENT_REPORT.md`](llm-safety-experiment/LLM_SAFETY_EXPERIMENT_REPORT.md)
- **Citation:** monograph §9 and [`llm-safety-experiment/CITATION.cff`](llm-safety-experiment/CITATION.cff)

Doc PRs should preserve **relative links** that work from both the repo root and `llm-safety-experiment/` where dual links are already established in [`README.md`](README.md).

---

## 10. Ethics and responsible disclosure

Prompts and committed completions are **research records** for transparency. Use them only in line with [`SECURITY.md`](SECURITY.md) and [`README.md`](README.md) §8. Do not use the project to harass, defraud, or harm people.

---

## 11. Extended workflow references

Labeling order, optional tiers, inter-rater reliability, and multimodel runbooks:

- [`llm-safety-experiment/REPLICATION_PROTOCOL.md`](llm-safety-experiment/REPLICATION_PROTOCOL.md)
- [`llm-safety-experiment/LOCAL_MULTI_MODEL_RUNBOOK.md`](llm-safety-experiment/LOCAL_MULTI_MODEL_RUNBOOK.md)
- Script index: [`llm-safety-experiment/PROVENANCE.md`](llm-safety-experiment/PROVENANCE.md)

---

## 12. Licensing

By contributing, you agree your contributions are licensed under the same terms as the project ([`LICENSE`](LICENSE)), unless you state otherwise in a manner the maintainers accept for that contribution.
