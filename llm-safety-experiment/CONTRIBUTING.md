# Contributing

This repository is maintained as an **open empirical safety evaluation toolkit** by **Aevion Labs** (see [`LICENSE`](LICENSE)). Bug reports, reproducibility fixes, and documentation improvements are welcome.

## Environment

- **Python:** 3.10+ recommended.
- **Install:** from the repo root (`llm-safety-experiment/`):

  ```bash
  python -m venv .venv
  .venv\Scripts\Activate.ps1   # Windows PowerShell
  pip install -r requirements.txt
  ```

- **API keys:** use a local `.env` (never commit secrets). See [`README.md`](README.md).

## Verify artifacts

After changing labeled results JSON:

```bash
python scripts/audit_multimodel_artifacts.py
python scripts/audit_multimodel_artifacts.py --strict
```

For the pilot chain:

```bash
python scripts/verify_artifact_chain.py
```

## Reproduce figures (no API calls)

```bash
python scripts/reproduce_main_figures.py
python scripts/reproduce_main_figures.py --extra-visuals --phd-visuals
```

Use `--skip-pilot` or `--skip-fingerprints` when only multimodel artifacts changed. See [`PROVENANCE.md`](PROVENANCE.md) and [`docs/ARTIFACT_INTEGRITY.md`](docs/ARTIFACT_INTEGRITY.md).

## Documentation map

- **Primary narrative:** [`docs/RESEARCH_MONOGRAPH.md`](docs/RESEARCH_MONOGRAPH.md)
- **Multimodel manuscript:** [`docs/MULTIMODEL_MANUSCRIPT.md`](docs/MULTIMODEL_MANUSCRIPT.md)
- **Index:** [`docs/README.md`](docs/README.md)
- **Long-form technical report:** [`LLM_SAFETY_EXPERIMENT_REPORT.md`](LLM_SAFETY_EXPERIMENT_REPORT.md)

## Citation

See [`docs/RESEARCH_MONOGRAPH.md`](docs/RESEARCH_MONOGRAPH.md) §9. [`CITATION.cff`](CITATION.cff) lists `repository-code` for the canonical Git URL.

## Extended workflow

For labeling order, optional tiers, and IRR, see [`REPLICATION_PROTOCOL.md`](REPLICATION_PROTOCOL.md), [`LOCAL_MULTI_MODEL_RUNBOOK.md`](LOCAL_MULTI_MODEL_RUNBOOK.md), and the script index in [`PROVENANCE.md`](PROVENANCE.md).

## Continuous integration

The root workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs `pip install`, `compileall`, and **`audit_multimodel_artifacts.py --strict`** against committed `results/` JSON (with `working-directory: llm-safety-experiment`).

## Ethics

Prompts are intended for **authorized safety research, scoped red teaming, or education**. Do not use outputs to harm. See the disclaimer in [`README.md`](README.md).
