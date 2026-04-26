"""
Inter-rater reliability helpers: label normalization, Cohen's kappa, confusion matrix, bootstrap kappa.

Used by compute_irr_kappa.py and irr_multimodel_report.py.
"""

from __future__ import annotations

import math
from typing import Any

LABELS: tuple[str, ...] = ("safe", "partial", "unsafe")
IDX: dict[str, int] = {lab: i for i, lab in enumerate(LABELS)}
MIN_PAIRS_CATEGORY_KAPPA = 5


def normalize_label(s: object) -> str | None:
    if s is None:
        return None
    t = str(s).strip().lower()
    return t if t in IDX else None


def confusion_matrix(r1: list[str], r2: list[str]) -> list[list[int]]:
    """Counts with rows = primary (r1), columns = compare (r2), order safe, partial, unsafe."""
    k = len(LABELS)
    cm = [[0] * k for _ in range(k)]
    for a, b in zip(r1, r2):
        cm[IDX[a]][IDX[b]] += 1
    return cm


def confusion_matrix_normalized_rows(cm: list[list[int]]) -> list[list[float]]:
    """p(compare=j | primary=i) per row; zero rows -> all zeros."""
    k = len(cm)
    out: list[list[float]] = []
    for i in range(k):
        s = sum(cm[i][j] for j in range(k))
        if s == 0:
            out.append([0.0] * k)
        else:
            out.append([cm[i][j] / s for j in range(k)])
    return out


def cohen_kappa(r1: list[str], r2: list[str]) -> tuple[float | None, float, float, int]:
    """Return (kappa, p_o, p_e, n); kappa None if undefined."""
    n = len(r1)
    if n == 0:
        return None, 0.0, 0.0, 0
    kk = len(LABELS)
    cm = confusion_matrix(r1, r2)
    p_o = sum(cm[i][i] for i in range(kk)) / n
    row_m = [sum(cm[i][j] for j in range(kk)) for i in range(kk)]
    col_m = [sum(cm[i][j] for i in range(kk)) for j in range(kk)]
    p_e = sum(row_m[i] * col_m[i] for i in range(kk)) / (n * n)
    if p_e >= 1.0 - 1e-15:
        return (1.0 if p_o >= 1.0 - 1e-15 else None), p_o, p_e, n
    kappa = (p_o - p_e) / (1.0 - p_e)
    return kappa, p_o, p_e, n


def bootstrap_kappa(
    r1: list[str],
    r2: list[str],
    n_draws: int,
    seed: int,
) -> dict[str, Any] | None:
    """Resample paired rows with replacement; percentile CI for kappa. None if n<2."""
    import numpy as np

    n = len(r1)
    if n < 2 or n_draws < 1:
        return None
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    kappas: list[float] = []
    for _ in range(n_draws):
        samp = rng.choice(idx, size=n, replace=True)
        s1 = [r1[i] for i in samp]
        s2 = [r2[i] for i in samp]
        k, _, _, nn = cohen_kappa(s1, s2)
        if k is not None and not math.isnan(k):
            kappas.append(k)
    if not kappas:
        return {"n_draws": n_draws, "mean_kappa": None, "ci_low": None, "ci_high": None, "n_valid": 0}
    arr = np.array(kappas, dtype=float)
    return {
        "n_draws": n_draws,
        "mean_kappa": float(np.mean(arr)),
        "ci_low": float(np.percentile(arr, 2.5)),
        "ci_high": float(np.percentile(arr, 97.5)),
        "n_valid": len(kappas),
    }


def summarize_pairs(
    r1: list[str],
    r2: list[str],
) -> dict[str, Any]:
    kappa, p_o, p_e, n = cohen_kappa(r1, r2)
    cm = confusion_matrix(r1, r2)
    return {
        "n_pairs": n,
        "kappa": kappa,
        "p_o": p_o,
        "p_e": p_e,
        "disagreement_rate": 1.0 - p_o if n else None,
        "confusion_matrix": cm,
        "confusion_matrix_labels": {"rows_primary": list(LABELS), "columns_compare": list(LABELS)},
        "p_compare_given_primary": confusion_matrix_normalized_rows(cm),
    }
