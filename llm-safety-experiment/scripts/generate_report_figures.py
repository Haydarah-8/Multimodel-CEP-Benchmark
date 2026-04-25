"""
Generate publication-style PNG figures for LLM_SAFETY_EXPERIMENT_REPORT.md.

Run from repo root or this directory:
  python scripts/generate_report_figures.py
  python scripts/generate_report_figures.py --results ../results_openai_gpt-4o-mini.json

Reads: ../results.json (or --results)
Writes:
  ../figures/fig1_unsafe_rate_by_category.png  — UNSAFE % by category + aggregate benchmark
  ../figures/fig_unsafe_rate_by_category_wilson_ci.png  — UNSAFE % + 95% Wilson score CIs (per-category n)
  ../figures/figure2_label_distribution_stacked.png — 100% stacked SAFE/PARTIAL/UNSAFE (normalized, sorted by UNSAFE %)
  ../figures/fig_category_risk_profile_heatmap.png — category × label % heatmap (column-specific gradients)
  ../figures/fig_cep_progression.png — UNSAFE % vs risk surface (PARTIAL+UNSAFE) across CEP categories
  ../figures/fig_category_safety_sankey.png — Sankey: category → label outcome (requires plotly + kaleido)
  ../figures/fig_failure_pattern_fingerprint.png — radar: SAFE/PARTIAL/UNSAFE % by category
  ../figures/fig_entropy_safety.png — Shannon entropy of label distribution per category
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import sys
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import PILOT_RESULTS_JSON  # noqa: E402

# Set at runtime from --results / --figures-dir in main()
RESULTS_PATH = PILOT_RESULTS_JSON
OUT_DIR = ROOT / "figures"
OUT_STACKED = OUT_DIR / "figure2_label_distribution_stacked.png"
OUT_UNSAFE = OUT_DIR / "fig1_unsafe_rate_by_category.png"
OUT_UNSAFE_CI = OUT_DIR / "fig_unsafe_rate_by_category_wilson_ci.png"
OUT_HEATMAP = OUT_DIR / "fig_category_risk_profile_heatmap.png"
OUT_CEP = OUT_DIR / "fig_cep_progression.png"
OUT_SANKEY = OUT_DIR / "fig_category_safety_sankey.png"
OUT_RADAR = OUT_DIR / "fig_failure_pattern_fingerprint.png"
OUT_ENTROPY = OUT_DIR / "fig_entropy_safety.png"


def set_output_dir(out: Path) -> None:
    """Point all figure paths at a directory (default or per-model subfolder)."""
    global OUT_DIR, OUT_STACKED, OUT_UNSAFE, OUT_UNSAFE_CI, OUT_HEATMAP, OUT_CEP, OUT_SANKEY, OUT_RADAR, OUT_ENTROPY
    OUT_DIR = out
    OUT_STACKED = OUT_DIR / "figure2_label_distribution_stacked.png"
    OUT_UNSAFE = OUT_DIR / "fig1_unsafe_rate_by_category.png"
    OUT_UNSAFE_CI = OUT_DIR / "fig_unsafe_rate_by_category_wilson_ci.png"
    OUT_HEATMAP = OUT_DIR / "fig_category_risk_profile_heatmap.png"
    OUT_CEP = OUT_DIR / "fig_cep_progression.png"
    OUT_SANKEY = OUT_DIR / "fig_category_safety_sankey.png"
    OUT_RADAR = OUT_DIR / "fig_failure_pattern_fingerprint.png"
    OUT_ENTROPY = OUT_DIR / "fig_entropy_safety.png"

# Dark theme (aligned with Mermaid dark figures)
BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
SAFE_COLOR = "#238636"
PARTIAL_COLOR = "#d29922"
UNSAFE_COLOR = "#da3633"
BAR_ORANGE = "#f0883e"
BENCHMARK_LINE = "#e6edf3"

CAT_ORDER = ["direct", "indirect", "emotional", "escalation", "roleplay"]
OUTCOME_ORDER = ["safe", "partial", "unsafe"]
OUTCOME_LABELS = ["SAFE", "PARTIAL", "UNSAFE"]
N_PER_CAT = 18

# Left-column node fill (distinct from flows, dark-theme)
NODE_LEFT = "#21262d"


def load_category_counts() -> dict[str, dict[str, int]]:
    with RESULTS_PATH.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    counts: dict[str, dict[str, int]] = {
        c: {"safe": 0, "partial": 0, "unsafe": 0} for c in CAT_ORDER
    }
    for r in rows:
        cat = r.get("category", "")
        lab = (r.get("label") or "").strip().lower()
        if cat in counts and lab in counts[cat]:
            counts[cat][lab] += 1
    return counts


def label_entropy_bits(s: int, p: int, u: int) -> float:
    """Shannon entropy (bits) of SAFE/PARTIAL/UNSAFE proportions within a category."""
    tot = s + p + u
    if tot <= 0:
        return 0.0
    ent = 0.0
    for c in (s, p, u):
        x = c / tot
        if x > 0:
            ent -= x * math.log2(x)
    return float(ent)


def generate_failure_pattern_fingerprint_figure() -> None:
    """Radar-style polar plot: three series (SAFE %, PARTIAL %, UNSAFE %) over categories."""
    counts = load_category_counts()
    n = len(CAT_ORDER)
    safe_pct = np.zeros(n)
    partial_pct = np.zeros(n)
    unsafe_pct = np.zeros(n)
    for i, cat in enumerate(CAT_ORDER):
        s = counts[cat]["safe"]
        p = counts[cat]["partial"]
        u = counts[cat]["unsafe"]
        tot = s + p + u
        if tot <= 0:
            continue
        safe_pct[i] = 100.0 * s / tot
        partial_pct[i] = 100.0 * p / tot
        unsafe_pct[i] = 100.0 * u / tot

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    angles_closed = np.append(angles, angles[0])

    fig, ax = plt.subplots(figsize=(7.0, 7.0), subplot_kw=dict(projection="polar"), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles), CAT_ORDER, color=FG, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percent", color=MUTED, fontsize=9, labelpad=30)
    ax.tick_params(axis="y", colors=MUTED, labelsize=8)
    ax.grid(color=MUTED, alpha=0.4, linestyle="--")
    ax.set_title("Failure Pattern Fingerprint", color=FG, fontsize=12, fontweight="semibold", pad=16)

    for vals, color, lab in (
        (safe_pct, SAFE_COLOR, "SAFE"),
        (partial_pct, PARTIAL_COLOR, "PARTIAL"),
        (unsafe_pct, UNSAFE_COLOR, "UNSAFE"),
    ):
        v = np.append(vals, vals[0])
        ax.plot(angles_closed, v, color=color, linewidth=2.0, label=lab)
        ax.fill(angles_closed, v, color=color, alpha=0.12)

    leg = ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.15, 1.05),
        facecolor=BG,
        edgecolor=MUTED,
        labelcolor=FG,
        fontsize=9,
    )
    for t in leg.get_texts():
        t.set_color(FG)

    fig.tight_layout()
    fig.savefig(OUT_RADAR, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_RADAR}")


def generate_entropy_safety_figure() -> None:
    """Bar chart: entropy of (SAFE, PARTIAL, UNSAFE) label distribution per category."""
    counts = load_category_counts()
    ents: list[float] = []
    for cat in CAT_ORDER:
        s = counts[cat]["safe"]
        p = counts[cat]["partial"]
        u = counts[cat]["unsafe"]
        ents.append(label_entropy_bits(s, p, u))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.0), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(CAT_ORDER))
    width = 0.62
    ax.bar(x, ents, width, color=BAR_ORANGE, edgecolor=BG, linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(CAT_ORDER, rotation=22, ha="right", color=FG, fontsize=10)
    ax.tick_params(axis="y", colors=FG)
    ax.set_ylabel("Entropy (bits)", color=FG, fontsize=10)
    ax.set_title(
        "Entropy of Label Distribution by Category",
        color=FG,
        fontsize=11,
        pad=12,
    )
    ax.text(
        0.5,
        0.02,
        "H = −Σ p_k log₂ p_k over SAFE / PARTIAL / UNSAFE within each category",
        transform=fig.transFigure,
        ha="center",
        fontsize=8.5,
        color=MUTED,
    )

    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=MUTED)

    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT_ENTROPY, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_ENTROPY}")


def _hex_to_rgb01(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _hex_to_rgba_str(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb01(hex_color)
    return (
        f"rgba({int(round(r * 255))},{int(round(g * 255))},{int(round(b * 255))},{alpha})"
    )


def _lerp_hex(a: str, b: str, t: float) -> tuple[float, float, float]:
    t = float(np.clip(t, 0.0, 1.0))
    ca = np.array(_hex_to_rgb01(a), dtype=float)
    cb = np.array(_hex_to_rgb01(b), dtype=float)
    return tuple((ca + (cb - ca) * t).tolist())


def _text_on_cell(bg_rgb: tuple[float, float, float]) -> str:
    """Light text on dark cells, dark text on bright cells."""
    r, g, b = bg_rgb
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return BG if lum > 0.45 else FG


def generate_category_risk_profile_heatmap() -> None:
    """
    Rows = categories, columns = SAFE / PARTIAL / UNSAFE.
    Cell value = percent of that category's labeled rows (0–100).
    Each column uses its own gradient: dark (low) → green / amber / red (high).
    """
    counts = load_category_counts()
    col_hues = (SAFE_COLOR, PARTIAL_COLOR, UNSAFE_COLOR)

    pct = np.zeros((len(CAT_ORDER), 3), dtype=float)
    for i, cat in enumerate(CAT_ORDER):
        s = counts[cat]["safe"]
        p = counts[cat]["partial"]
        u = counts[cat]["unsafe"]
        tot = s + p + u
        if tot <= 0:
            continue
        pct[i, 0] = 100.0 * s / tot
        pct[i, 1] = 100.0 * p / tot
        pct[i, 2] = 100.0 * u / tot

    rgb = np.zeros((len(CAT_ORDER), 3, 3), dtype=float)
    for i in range(len(CAT_ORDER)):
        for j in range(3):
            rgb[i, j, :] = _lerp_hex(BG, col_hues[j], pct[i, j] / 100.0)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.2, 6.0), facecolor=BG)
    ax.set_facecolor(BG)
    ax.imshow(rgb, aspect="auto", interpolation="nearest", origin="upper")

    for i in range(len(CAT_ORDER)):
        for j in range(3):
            v = pct[i, j]
            tc = _text_on_cell(tuple(rgb[i, j, :]))
            t = ax.text(
                j,
                i,
                f"{v:.1f}%",
                ha="center",
                va="center",
                color=tc,
                fontsize=11,
                fontweight="medium",
            )
            if tc == FG:
                t.set_path_effects([pe.withStroke(linewidth=2.0, foreground=BG)])

    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(["SAFE", "PARTIAL", "UNSAFE"], color=FG, fontsize=11, fontweight="medium")
    ax.set_yticks(np.arange(len(CAT_ORDER)))
    ax.set_yticklabels(CAT_ORDER, color=FG, fontsize=10)
    ax.tick_params(axis="both", length=0)
    ax.set_title("Category-Level Risk Profile Heatmap", color=FG, fontsize=12, fontweight="semibold", pad=14)

    for spine in ax.spines.values():
        spine.set_color(MUTED)
        spine.set_linewidth(0.8)

    fig.tight_layout()
    fig.savefig(OUT_HEATMAP, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_HEATMAP}")


def generate_unsafe_rate_figure() -> None:
    """Match report Figure 9: per-category UNSAFE % with overall 10/90 benchmark line."""
    counts = load_category_counts()
    unsafe_pct = np.array([counts[c]["unsafe"] / N_PER_CAT * 100.0 for c in CAT_ORDER], dtype=float)
    overall_unsafe_pct = sum(counts[c]["unsafe"] for c in CAT_ORDER) / (len(CAT_ORDER) * N_PER_CAT) * 100.0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(CAT_ORDER))
    width = 0.62
    ax.bar(x, unsafe_pct, width, color=BAR_ORANGE, edgecolor=BG, linewidth=0.5, label="UNSAFE % (category)")
    ax.axhline(
        overall_unsafe_pct,
        color=BENCHMARK_LINE,
        linestyle="--",
        linewidth=1.2,
        alpha=0.85,
        label=f"Overall UNSAFE ({overall_unsafe_pct:.1f}%)",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(CAT_ORDER, rotation=22, ha="right", color=FG, fontsize=10)
    ax.tick_params(axis="y", colors=FG)
    ax.set_ylabel("UNSAFE %", color=FG, fontsize=10)
    ax.set_ylim(0, 35)
    ax.set_title("UNSAFE rate by category (n = 18 per category)", color=FG, fontsize=11, pad=12)
    leg = ax.legend(
        facecolor=BG,
        edgecolor=MUTED,
        labelcolor=FG,
        loc="upper right",
        framealpha=1.0,
        fontsize=9,
    )
    for t in leg.get_texts():
        t.set_color(FG)
    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=MUTED)
    fig.tight_layout()
    fig.savefig(OUT_UNSAFE, dpi=160, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_UNSAFE}")


def generate_unsafe_rate_wilson_ci_figure() -> None:
    """
    Per-category UNSAFE proportion with 95% Wilson score intervals (binomial).
    Uses labeled row count per category as n (typically 18 when fully labeled).
    """
    counts = load_category_counts()
    pcts: list[float] = []
    err_lo: list[float] = []
    err_hi: list[float] = []
    ns: list[int] = []

    for cat in CAT_ORDER:
        k = counts[cat]["unsafe"]
        tot = counts[cat]["safe"] + counts[cat]["partial"] + counts[cat]["unsafe"]
        ns.append(tot)
        if tot <= 0:
            pcts.append(0.0)
            err_lo.append(0.0)
            err_hi.append(0.0)
            continue
        ci = binomtest(k, tot).proportion_ci(confidence_level=0.95, method="wilson")
        pct = 100.0 * k / tot
        lo = 100.0 * float(ci.low)
        hi = 100.0 * float(ci.high)
        pcts.append(pct)
        err_lo.append(pct - lo)
        err_hi.append(hi - pct)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(len(CAT_ORDER))
    width = 0.62
    yerr = np.array([err_lo, err_hi], dtype=float)

    ax.bar(
        x,
        pcts,
        width,
        color=BAR_ORANGE,
        edgecolor=BG,
        linewidth=0.5,
        yerr=yerr,
        capsize=4,
        error_kw=dict(
            ecolor=FG,
            elinewidth=1.15,
            capthick=1.15,
            alpha=0.9,
        ),
    )

    ax.set_xticks(x)
    ax.set_xticklabels(CAT_ORDER, rotation=22, ha="right", color=FG, fontsize=10)
    ax.tick_params(axis="y", colors=FG)
    ax.set_ylabel("UNSAFE rate (%)", color=FG, fontsize=10)
    tops = np.array(pcts, dtype=float) + np.array(err_hi, dtype=float)
    ymax = float(np.max(tops)) if tops.size else 1.0
    ymax = max(12.0, ymax, 1.0)
    ax.set_ylim(0, min(100.0, ymax * 1.15))
    ax.set_title(
        "UNSAFE Rate by Category with Confidence Intervals",
        color=FG,
        fontsize=11,
        pad=12,
    )

    for i in range(len(CAT_ORDER)):
        if ns[i] > 0:
            ax.text(
                x[i],
                pcts[i] + err_hi[i] + ymax * 0.035,
                f"n={ns[i]}",
                ha="center",
                va="bottom",
                fontsize=8,
                color=MUTED,
            )

    fig.text(
        0.5,
        0.01,
        "Error bars: 95% Wilson score intervals (binomial). Bar height = point estimate.",
        ha="center",
        fontsize=9,
        color=MUTED,
    )

    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=MUTED)

    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT_UNSAFE_CI, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_UNSAFE_CI}")


LABEL_MIN_PCT = 6.0  # omit in-bar label below this height (%)


def _text_color_for_segment(color: str) -> str:
    """Light text on green/red; dark text on amber for contrast."""
    if color == PARTIAL_COLOR:
        return BG
    return FG


def generate_label_distribution_stacked_figure() -> None:
    """100% stacked bars per category, sorted by UNSAFE rate (highest left), in-bar % labels."""
    counts = load_category_counts()
    rows: list[tuple[str, float, float, float, float]] = []
    for cat in CAT_ORDER:
        s = counts[cat]["safe"]
        p = counts[cat]["partial"]
        u = counts[cat]["unsafe"]
        tot = s + p + u
        if tot <= 0:
            continue
        safe_pct = 100.0 * s / tot
        partial_pct = 100.0 * p / tot
        unsafe_pct = 100.0 * u / tot
        unsafe_rate = u / tot
        rows.append((cat, safe_pct, partial_pct, unsafe_pct, unsafe_rate))

    rows.sort(key=lambda t: (-t[4], t[0]))

    cats = [t[0] for t in rows]
    safe_pct = np.array([t[1] for t in rows], dtype=float)
    partial_pct = np.array([t[2] for t in rows], dtype=float)
    unsafe_pct = np.array([t[3] for t in rows], dtype=float)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n = len(cats)
    if n == 0:
        print("No labeled rows — skipped stacked label figure.")
        return

    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=BG)
    ax.set_facecolor(BG)
    x = np.arange(n)
    width = 0.62

    ax.bar(x, safe_pct, width, label="SAFE", color=SAFE_COLOR, edgecolor=BG, linewidth=0.5)
    ax.bar(x, partial_pct, width, bottom=safe_pct, label="PARTIAL", color=PARTIAL_COLOR, edgecolor=BG, linewidth=0.5)
    ax.bar(
        x,
        unsafe_pct,
        width,
        bottom=safe_pct + partial_pct,
        label="UNSAFE",
        color=UNSAFE_COLOR,
        edgecolor=BG,
        linewidth=0.5,
    )

    segments = [
        (safe_pct, np.zeros(n), SAFE_COLOR),
        (partial_pct, safe_pct, PARTIAL_COLOR),
        (unsafe_pct, safe_pct + partial_pct, UNSAFE_COLOR),
    ]
    for heights, bottoms, seg_color in segments:
        for i in range(n):
            h = float(heights[i])
            if h < LABEL_MIN_PCT:
                continue
            y = float(bottoms[i]) + h / 2.0
            txt = f"{h:.1f}%"
            tc = _text_color_for_segment(seg_color)
            t = ax.text(
                x[i],
                y,
                txt,
                ha="center",
                va="center",
                color=tc,
                fontsize=9,
                fontweight="medium",
            )
            if tc == FG:
                t.set_path_effects([pe.withStroke(linewidth=2.5, foreground=BG)])

    ax.set_xticks(x)
    ax.set_xticklabels(cats, rotation=22, ha="right", color=FG, fontsize=10)
    ax.tick_params(axis="y", colors=FG)
    ax.set_ylabel("Share of category (%)", color=FG, fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_title("Label Distribution by Category (Normalized)", color=FG, fontsize=11, pad=12)
    leg = ax.legend(
        facecolor=BG,
        edgecolor=MUTED,
        labelcolor=FG,
        loc="upper right",
        framealpha=1.0,
        fontsize=9,
    )
    for t in leg.get_texts():
        t.set_color(FG)

    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=MUTED)

    fig.tight_layout()
    fig.savefig(OUT_STACKED, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_STACKED}")


def _unsafe_and_risk_surface_pct() -> tuple[np.ndarray, np.ndarray]:
    """Per-category UNSAFE % and (PARTIAL + UNSAFE) % among labeled rows."""
    counts = load_category_counts()
    n = len(CAT_ORDER)
    unsafe_pct = np.zeros(n, dtype=float)
    risk_surface_pct = np.zeros(n, dtype=float)
    for i, cat in enumerate(CAT_ORDER):
        s = counts[cat]["safe"]
        p = counts[cat]["partial"]
        u = counts[cat]["unsafe"]
        tot = s + p + u
        if tot <= 0:
            continue
        unsafe_pct[i] = 100.0 * u / tot
        risk_surface_pct[i] = 100.0 * (p + u) / tot
    return unsafe_pct, risk_surface_pct


def generate_cep_progression_figure() -> None:
    """
    Line chart: contextual obfuscation (direct → roleplay) vs UNSAFE rate and risk surface.
    Risk surface rises earlier (PARTIAL + UNSAFE) than UNSAFE-only rate.
    """
    unsafe_pct, risk_pct = _unsafe_and_risk_surface_pct()
    x = np.arange(len(CAT_ORDER), dtype=float)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=BG)
    ax.set_facecolor(BG)

    lw = 2.2
    ms = 9
    mew = 1.2

    ax.plot(
        x,
        unsafe_pct,
        color=UNSAFE_COLOR,
        linestyle="-",
        linewidth=lw,
        marker="o",
        markersize=ms,
        markerfacecolor=UNSAFE_COLOR,
        markeredgecolor=BG,
        markeredgewidth=mew,
        label="UNSAFE rate",
        zorder=3,
    )
    ax.plot(
        x,
        risk_pct,
        color=BAR_ORANGE,
        linestyle="--",
        linewidth=lw,
        marker="s",
        markersize=ms,
        markerfacecolor=BAR_ORANGE,
        markeredgecolor=BG,
        markeredgewidth=mew,
        label="Risk surface (PARTIAL + UNSAFE)",
        zorder=3,
    )

    ymax = max(float(np.max(unsafe_pct)), float(np.max(risk_pct)), 1.0)
    ax.set_ylim(0, min(100.0, ymax * 1.25))

    idx_escalation = CAT_ORDER.index("escalation")
    idx_roleplay = CAT_ORDER.index("roleplay")

    ax.annotate(
        "Escalation",
        xy=(idx_escalation, risk_pct[idx_escalation]),
        xytext=(0, 14),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        color=FG,
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9, shrinkA=0, shrinkB=4),
    )
    ax.annotate(
        "Roleplay",
        xy=(idx_roleplay, unsafe_pct[idx_roleplay]),
        xytext=(0, 14),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        color=FG,
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9, shrinkA=0, shrinkB=4),
    )

    ax.set_xticks(x)
    ax.set_xticklabels(CAT_ORDER, rotation=22, ha="right", color=FG, fontsize=10)
    ax.tick_params(axis="y", colors=FG)
    ax.set_ylabel("Percentage (%)", color=FG, fontsize=10)
    ax.set_title("CEP Progression: From Explicit to Contextual Harm", color=FG, fontsize=11, pad=12)

    leg = ax.legend(
        facecolor=BG,
        edgecolor=MUTED,
        labelcolor=FG,
        loc="upper left",
        framealpha=1.0,
        fontsize=9,
    )
    for t in leg.get_texts():
        t.set_color(FG)

    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.grid(axis="y", linestyle="--", alpha=0.35, color=MUTED)

    fig.tight_layout()
    fig.savefig(OUT_CEP, dpi=200, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {OUT_CEP}")


def generate_category_safety_sankey_figure() -> None:
    """
    Sankey: prompt category (left) → label outcome (right). Flow width = count.
    UNSAFE flows use red; stronger opacity for escalation & roleplay → UNSAFE.
    """
    try:
        import plotly.graph_objects as go  # type: ignore[import-untyped]
    except ImportError:
        print("plotly not installed; skipped Sankey (pip install plotly kaleido)")
        return

    counts = load_category_counts()
    n_left = len(CAT_ORDER)
    labels = list(CAT_ORDER) + OUTCOME_LABELS
    node_colors = [NODE_LEFT] * n_left + [SAFE_COLOR, PARTIAL_COLOR, UNSAFE_COLOR]

    label_hex = {"safe": SAFE_COLOR, "partial": PARTIAL_COLOR, "unsafe": UNSAFE_COLOR}

    source: list[int] = []
    target: list[int] = []
    value: list[int] = []
    link_color: list[str] = []

    for ci, cat in enumerate(CAT_ORDER):
        for oi, lab in enumerate(OUTCOME_ORDER):
            v = counts[cat][lab]
            if v <= 0:
                continue
            source.append(ci)
            target.append(n_left + oi)
            value.append(v)
            base = label_hex[lab]
            if lab == "unsafe" and cat in ("escalation", "roleplay"):
                alpha = 0.92
            elif lab == "unsafe":
                alpha = 0.58
            else:
                alpha = 0.48
            link_color.append(_hex_to_rgba_str(base, alpha))

    if not value:
        print("No labeled flows — skipped Sankey.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                valueformat=".0f",
                node=dict(
                    pad=20,
                    thickness=24,
                    line=dict(color=MUTED, width=0.9),
                    label=labels,
                    color=node_colors,
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value,
                    color=link_color,
                ),
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="Flow of Prompt Categories to Safety Outcomes",
            font=dict(color=FG, size=17, family="Arial, sans-serif"),
            x=0.5,
            xanchor="center",
        ),
        paper_bgcolor=BG,
        font=dict(color=FG, size=12),
        margin=dict(l=28, r=28, t=72, b=28),
        height=640,
        width=1100,
    )

    try:
        fig.write_image(str(OUT_SANKEY), width=1100, height=640, scale=2)
    except Exception as exc:  # noqa: BLE001 — surface kaleido/orca issues clearly
        print(f"Sankey PNG export failed ({exc}). Install kaleido: pip install kaleido")
        return

    print(f"Wrote {OUT_SANKEY}")


def main() -> None:
    global RESULTS_PATH
    parser = argparse.ArgumentParser(description="Build PNG figures from labeled results.json.")
    parser.add_argument(
        "--results",
        "-r",
        type=Path,
        default=PILOT_RESULTS_JSON,
        help="Labeled results JSON path (default: results/pilot/results.json)",
    )
    parser.add_argument(
        "--figures-dir",
        "-o",
        type=Path,
        default=ROOT / "figures",
        help="Directory for PNG outputs (default: figures/; use a subfolder per model to avoid overwrites)",
    )
    parser.add_argument(
        "--skip-sankey",
        action="store_true",
        help="Skip Plotly/Kaleido Sankey PNG (can be slow or hang on some systems)",
    )
    args = parser.parse_args()
    RESULTS_PATH = args.results.resolve()
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Missing results file: {RESULTS_PATH}")
    set_output_dir(args.figures_dir.resolve())
    print(f"Using results: {RESULTS_PATH}")
    print(f"Figure output directory: {OUT_DIR}")

    generate_unsafe_rate_figure()
    generate_unsafe_rate_wilson_ci_figure()
    generate_label_distribution_stacked_figure()
    generate_category_risk_profile_heatmap()
    generate_cep_progression_figure()
    if not args.skip_sankey:
        generate_category_safety_sankey_figure()
    else:
        print("Skipping Sankey PNG (--skip-sankey).")
    generate_failure_pattern_fingerprint_figure()
    generate_entropy_safety_figure()


if __name__ == "__main__":
    main()
