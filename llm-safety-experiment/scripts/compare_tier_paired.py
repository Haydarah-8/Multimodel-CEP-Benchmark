"""
Paired McNemar-style analysis for the same prompt ids across two labeled result files
(e.g. cheap vs expensive tier for one provider).

Outcome binaries:
  - unsafe: label == unsafe
  - risk:   label in {partial, unsafe}

Uses exact two-sided binomial test on discordant pairs (min(b,c) vs Binomial(b+c, 0.5)).
Reports discordant counts, paired odds ratio n01/n10 (second file "more outcome" vs first),
and approximate CI via binomial on log ratio if n large enough (optional).

Usage (from llm-safety-experiment):
  python scripts/compare_tier_paired.py --a results/multimodel/cheap/results_openai_gpt-4o-mini.json \\
      --b results/multimodel/expensive/results_openai_gpt-4.1.json
  python scripts/compare_tier_paired.py --a ... --b ... --out tier_pair_openai_cheap_exp.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from paths import artifact_relpath  # noqa: E402

Outcome = Literal["unsafe", "risk"]


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def row_binary(row: dict[str, Any], outcome: Outcome) -> int:
    lab = (row.get("label") or "").strip().lower()
    if outcome == "unsafe":
        return 1 if lab == "unsafe" else 0
    return 1 if lab in ("partial", "unsafe") else 0


def mcnemar_binomial(
    ids: list[Any], rows_a: dict[Any, dict], rows_b: dict[Any, dict], outcome: Outcome
) -> dict[str, Any]:
    """
    n10: first=1 second=0 (A has outcome, B not)
    n01: first=0 second=1
    Paired OR (B vs A for higher outcome) = n01/n10 when n10>0.
    """
    n10 = n01 = 0
    for pid in ids:
        ya = row_binary(rows_a[pid], outcome)
        yb = row_binary(rows_b[pid], outcome)
        if ya == 1 and yb == 0:
            n10 += 1
        elif ya == 0 and yb == 1:
            n01 += 1
    n_disc = n10 + n01
    if n_disc == 0:
        p_val = 1.0
        or_pair: float | None = None
    else:
        k = min(n10, n01)
        p_val = float(binomtest(k, n_disc, 0.5, alternative="two-sided").pvalue)
        if n10 > 0:
            or_pair = n01 / n10
        elif n01 > 0:
            or_pair = None
        else:
            or_pair = None
    return {
        "outcome": outcome,
        "n_discordant": n_disc,
        "n_first_yes_second_no": n10,
        "n_first_no_second_yes": n01,
        "paired_odds_ratio_B_vs_A": or_pair,
        "mcnemar_exact_binomial_p_two_sided": p_val,
    }


def compare_pair(path_a: Path, path_b: Path) -> dict[str, Any]:
    ra = {r["id"]: r for r in load_rows(path_a)}
    rb = {r["id"]: r for r in load_rows(path_b)}
    common = sorted(set(ra) & set(rb), key=lambda x: (str(x),))
    warnings: list[str] = []
    if len(ra) != len(rb) or set(ra) != set(rb):
        only_a = sorted(set(ra) - set(rb))[:8]
        only_b = sorted(set(rb) - set(ra))[:8]
        warnings.append(
            f"id sets differ (n_A={len(ra)} n_B={len(rb)}); using intersection n={len(common)}. "
            f"only_A_sample={only_a} only_B_sample={only_b}"
        )
    if len(common) == 0:
        raise ValueError("No overlapping prompt ids between files.")
    out: dict[str, Any] = {
        "file_a": artifact_relpath(path_a),
        "file_b": artifact_relpath(path_b),
        "n_paired": len(common),
        "warnings": warnings,
        "unsafe": mcnemar_binomial(common, ra, rb, "unsafe"),
        "risk": mcnemar_binomial(common, ra, rb, "risk"),
        "mcnemar_note": "Exact binomial on min(discordant); SciPy two-sided p can be 1.0 for nearly balanced splits.",
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Paired tier comparison (McNemar exact)")
    ap.add_argument("--a", type=Path, required=True, help="First results JSON (e.g. cheap)")
    ap.add_argument("--b", type=Path, required=True, help="Second results JSON (e.g. expensive)")
    ap.add_argument("--out", type=Path, default=None, help="Optional JSON output path")
    args = ap.parse_args()

    if not args.a.is_file() or not args.b.is_file():
        print("Missing --a or --b file", file=sys.stderr)
        sys.exit(1)
    if args.a.resolve() == args.b.resolve():
        print("Refusing: --a and --b are the same file.", file=sys.stderr)
        sys.exit(1)

    payload = compare_pair(args.a, args.b)
    print(json.dumps(payload, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
