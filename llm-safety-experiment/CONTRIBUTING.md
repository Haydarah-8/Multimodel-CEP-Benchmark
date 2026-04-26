# Contributing (package folder)

The **full** contributor guide lives at the repository root: **[`../CONTRIBUTING.md`](../CONTRIBUTING.md)** (environment, audits, CI, ethics, PR expectations).

If you are already in `llm-safety-experiment/`:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
python scripts/audit_multimodel_artifacts.py --strict
python scripts/reproduce_main_figures.py
```

Code of conduct: [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md). Security: [`../SECURITY.md`](../SECURITY.md).
