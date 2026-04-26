"""
Shared statistics helpers for significance, stress indices, and figures.

- Wilson score CI for binomial proportion (matches scipy.stats.binomtest ... wilson)
- Cramér's V for chi-square on r x c contingency
- Woolf (log) asymptotic 95% CI for 2x2 odds ratio
"""

from __future__ import annotations

import math
from typing import Any

from scipy.stats import binomtest


def wilson_proportion_ci(
    k: int, n: int, confidence_level: float = 0.95
) -> tuple[float, float, float]:
    """Return (low, high, p_hat) for proportion k/n; if n<=0 returns (0,0,0)."""
    if n <= 0:
        return 0.0, 0.0, 0.0
    kk = max(0, min(int(k), int(n)))
    ci = binomtest(kk, int(n)).proportion_ci(confidence_level=confidence_level, method="wilson")
    phat = kk / int(n)
    return float(ci.low), float(ci.high), float(phat)


def cramers_v(chi2: float, n: int, n_rows: int, n_cols: int) -> float:
    """Cramér's V = sqrt(chi2 / (n * min(r-1, c-1)))."""
    if n <= 0 or n_rows < 2 or n_cols < 2:
        return 0.0
    denom = n * min(n_rows - 1, n_cols - 1)
    if denom <= 0:
        return 0.0
    return float(math.sqrt(max(0.0, chi2) / denom))


def odds_ratio_2x2(a: int, b: int, c: int, d: int) -> float:
    """OR for [[a,b],[c,d]] as scipy Fisher: (a/b)/(c/d) = a*d/(b*c)."""
    if b == 0 or c == 0:
        return float("inf") if a * d > 0 else float("nan")
    return float(a * d / (b * c))


def odds_ratio_woolf_ci(
    a: int, b: int, c: int, d: int, z: float = 1.96
) -> tuple[float, float, float]:
    """
    Approximate 95% CI for 2x2 odds ratio (Woolf / log-OR).
    If any cell is 0, uses +0.5 continuity (Haldane–Anscombe) for CI only.
    Returns (or_point, ci_low, ci_high).
    """
    aa, bb, cc, dd = float(a), float(b), float(c), float(d)
    if min(aa, bb, cc, dd) <= 0:
        aa, bb, cc, dd = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    or_point = (aa * dd) / (bb * cc) if bb > 0 and cc > 0 else float("nan")
    log_or = math.log(aa) + math.log(dd) - math.log(bb) - math.log(cc)
    se = math.sqrt(1.0 / aa + 1.0 / bb + 1.0 / cc + 1.0 / dd)
    lo = math.exp(log_or - z * se)
    hi = math.exp(log_or + z * se)
    return float(or_point), float(lo), float(hi)


def fisher_table_to_json_ci_block(tab: list[list[int]]) -> dict[str, Any]:
    """tab is [[a,b],[c,d]] from Fisher UNSAFE vs not, focal vs rest."""
    a, b = int(tab[0][0]), int(tab[0][1])
    c, d = int(tab[1][0]), int(tab[1][1])
    _or_pt, lo, hi = odds_ratio_woolf_ci(a, b, c, d)
    return {"odds_ratio_ci95_approx_woolf": {"low": lo, "high": hi}}
