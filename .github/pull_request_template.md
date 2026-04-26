## Description

<!-- What does this PR change and why? Link issues: Fixes # -->

## Type of change

<!-- Check all that apply -->

- [ ] Bug fix (non-breaking)
- [ ] Documentation only
- [ ] New script / analysis (additive)
- [ ] Updates committed `results/**/*.json` or other frozen artifacts
- [ ] Regenerated figures / HTML / companions

## Testing

<!-- Commands you ran (from `llm-safety-experiment/` unless noted) -->

```bash
# Examples:
# python scripts/audit_multimodel_artifacts.py --strict
# python scripts/reproduce_main_figures.py
# python -m compileall -q scripts prompt_mutations
```

## Checklist

- [ ] No API keys, tokens, or local-only absolute paths committed
- [ ] If `results/**/*.json` changed: `python scripts/audit_multimodel_artifacts.py --strict` passes locally
- [ ] If plotting or companion scripts changed: regeneration command noted above or binaries omitted intentionally
- [ ] Documentation links remain valid from repo root (and from `llm-safety-experiment/` where dual paths exist)
- [ ] If prompts, labels, or model outputs changed: ethics / responsible-use note included for reviewers ([`SECURITY.md`](../SECURITY.md), [`README.md`](../README.md) §8)
- [ ] I have read and follow the [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md)

## Related documentation

<!-- e.g. PROVENANCE.md, ARTIFACT_INTEGRITY.md, monograph section -->
