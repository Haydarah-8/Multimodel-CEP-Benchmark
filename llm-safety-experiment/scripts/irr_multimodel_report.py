"""
Multimodel inter-rater report: Cohen's κ and disagreement by file (model), tier, and category.

Pairs primary `label` with `--compare-field` (default label_rater2; use label_model_proxy for exploratory proxy).

Usage (from llm-safety-experiment):
  python scripts/irr_multimodel_report.py
  python scripts/irr_multimodel_report.py --compare-field label_model_proxy --root results/multimodel/cheap
  python scripts/irr_multimodel_report.py --bootstrap 1000
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compute_significance import CAT_ORDER  # noqa: E402
from irr_utils import (  # noqa: E402
    MIN_PAIRS_CATEGORY_KAPPA,
    bootstrap_kappa,
    normalize_label,
    summarize_pairs,
)
from paths import MULTIMODEL_DIR, artifact_relpath  # noqa: E402

TIER_ORDER = ("cheap", "mid", "expensive")


def _resolve_stored_path(stored: str) -> Path:
    """Support repo-relative paths in JSON (and legacy absolute paths)."""
    p = Path(stored)
    if p.is_file():
        return p
    cand = ROOT / stored
    if cand.is_file():
        return cand
    return p


def discover_files(root: Path, include_archive: bool) -> list[Path]:
    if not root.is_dir():
        return []
    files = sorted(root.rglob("results_*.json"))
    if not include_archive:
        files = [p for p in files if "archive" not in p.parts]
    return files


def tier_from_path(p: Path) -> str:
    parts = {x.lower() for x in p.parts}
    for t in TIER_ORDER:
        if t in parts:
            return t
    return "unknown"


def stem_from_path(p: Path) -> str:
    return p.stem


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "rows" in data:
        inner = data["rows"]
        if isinstance(inner, list):
            return inner
    if isinstance(data, list):
        return data
    raise ValueError(f"{path}: expected JSON array or object with 'rows' list")


def extract_pairs(
    rows: list[dict[str, Any]],
    compare_field: str,
) -> tuple[list[str], list[str], dict[str, tuple[list[str], list[str]]], int]:
    """Return r1, r2, by_category (lowercase cat keys), skipped count."""
    r1: list[str] = []
    r2: list[str] = []
    by_cat: dict[str, tuple[list[str], list[str]]] = defaultdict(lambda: ([], []))
    skipped = 0
    for row in rows:
        a = normalize_label(row.get("label"))
        b = normalize_label(row.get(compare_field))
        if a is None or b is None:
            skipped += 1
            continue
        r1.append(a)
        r2.append(b)
        cat = str(row.get("category") or "unknown").strip().lower()
        by_cat[cat][0].append(a)
        by_cat[cat][1].append(b)
    return r1, r2, dict(by_cat), skipped


def category_block(
    xs: list[str],
    ys: list[str],
) -> dict[str, Any] | None:
    n = len(xs)
    if n < MIN_PAIRS_CATEGORY_KAPPA:
        return {"n_pairs": n, "kappa": None, "p_o": None, "p_e": None, "disagreement_rate": None, "note": f"n<{MIN_PAIRS_CATEGORY_KAPPA}"}
    s = summarize_pairs(xs, ys)
    return {
        "n_pairs": s["n_pairs"],
        "kappa": s["kappa"],
        "p_o": s["p_o"],
        "p_e": s["p_e"],
        "disagreement_rate": s["disagreement_rate"],
        "confusion_matrix": s["confusion_matrix"],
    }


def pool_summarize(r1: list[str], r2: list[str], bootstrap: int | None, seed: int) -> dict[str, Any]:
    if not r1:
        return {"n_pairs": 0, "kappa": None, "note": "no_pairs"}
    s = summarize_pairs(r1, r2)
    out: dict[str, Any] = {
        "n_pairs": s["n_pairs"],
        "kappa": s["kappa"],
        "p_o": s["p_o"],
        "p_e": s["p_e"],
        "disagreement_rate": s["disagreement_rate"],
        "confusion_matrix": s["confusion_matrix"],
        "p_compare_given_primary": s["p_compare_given_primary"],
    }
    if bootstrap and bootstrap > 0 and len(r1) >= 2:
        out["bootstrap_kappa"] = bootstrap_kappa(r1, r2, bootstrap, seed)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Multimodel IRR JSON report (Cohen kappa, disagreement)")
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument("--include-archive", action="store_true")
    ap.add_argument("--compare-field", type=str, default="label_rater2")
    ap.add_argument("--primary-field", type=str, default="label")
    ap.add_argument("--bootstrap", type=int, default=0, help="If >0, bootstrap paired rows this many times (per file + tier + global)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "multimodel" / "irr_multimodel_report.json",
    )
    args = ap.parse_args()

    files = discover_files(args.root, args.include_archive)
    if not files:
        print(f"No results_*.json under {args.root}", file=sys.stderr)
        sys.exit(1)

    per_file_out: list[dict[str, Any]] = []
    tier_r1: dict[str, list[str]] = defaultdict(list)
    tier_r2: dict[str, list[str]] = defaultdict(list)
    global_r1: list[str] = []
    global_r2: list[str] = []

    for fp in files:
        rows = load_rows(fp)
        tier = tier_from_path(fp)
        r1, r2, by_cat, skipped = extract_pairs(rows, args.compare_field)
        if len(r1) == 0:
            continue

        provider = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
        model = next((str(r.get("model")) for r in rows if r.get("model")), "")
        stem = stem_from_path(fp)
        display = f"{provider} / {model}".strip(" /") if (provider or model) else stem

        overall = summarize_pairs(r1, r2)
        file_entry: dict[str, Any] = {
            "path": artifact_relpath(fp),
            "tier": tier,
            "provider": provider,
            "model": model,
            "file_stem": stem,
            "display_name": display,
            "n_pairs": overall["n_pairs"],
            "skipped_missing_pair": skipped,
            "overall": {k: overall[k] for k in ("kappa", "p_o", "p_e", "disagreement_rate", "confusion_matrix", "p_compare_given_primary")},
        }
        if args.bootstrap > 0:
            file_entry["overall"]["bootstrap_kappa"] = bootstrap_kappa(r1, r2, args.bootstrap, args.seed)

        by_cat_out: dict[str, Any] = {}
        for cat in CAT_ORDER:
            if cat in by_cat:
                xs, ys = by_cat[cat]
                by_cat_out[cat] = category_block(xs, ys)
            else:
                by_cat_out[cat] = {"n_pairs": 0, "kappa": None, "note": "no_rows"}
        for cat in sorted(by_cat.keys()):
            if cat not in by_cat_out:
                xs, ys = by_cat[cat]
                by_cat_out[cat] = category_block(xs, ys)

        file_entry["by_category"] = by_cat_out
        per_file_out.append(file_entry)

        global_r1.extend(r1)
        global_r2.extend(r2)
        tier_r1[tier].extend(r1)
        tier_r2[tier].extend(r2)

    if not per_file_out:
        print(
            f"No files with paired {args.primary_field} + {args.compare_field}. Merge second labels first.",
            file=sys.stderr,
        )
        sys.exit(2)

    per_tier: dict[str, Any] = {}
    for t in TIER_ORDER:
        if t in tier_r1 and tier_r1[t]:
            block = pool_summarize(tier_r1[t], tier_r2[t], args.bootstrap if args.bootstrap > 0 else None, args.seed)
            byc: dict[str, Any] = {}
            # pool by category within tier
            cat_map: dict[str, tuple[list[str], list[str]]] = defaultdict(lambda: ([], []))
            for fe in per_file_out:
                if fe["tier"] != t:
                    continue
                fp = _resolve_stored_path(fe["path"])
                rows = load_rows(fp)
                r1, r2, bc, _ = extract_pairs(rows, args.compare_field)
                for cat in CAT_ORDER:
                    if cat in bc:
                        xs, ys = bc[cat]
                        cat_map[cat][0].extend(xs)
                        cat_map[cat][1].extend(ys)
            for cat in CAT_ORDER:
                xs, ys = cat_map[cat]
                byc[cat] = category_block(xs, ys)
            block["by_category"] = byc
            per_tier[t] = block

    global_block = pool_summarize(global_r1, global_r2, args.bootstrap if args.bootstrap > 0 else None, args.seed)
    cat_map_g: dict[str, tuple[list[str], list[str]]] = defaultdict(lambda: ([], []))
    for fe in per_file_out:
        fp = _resolve_stored_path(fe["path"])
        rows = load_rows(fp)
        _, _, bc, _ = extract_pairs(rows, args.compare_field)
        for cat in CAT_ORDER:
            if cat in bc:
                xs, ys = bc[cat]
                cat_map_g[cat][0].extend(xs)
                cat_map_g[cat][1].extend(ys)
    global_block["by_category"] = {cat: category_block(*cat_map_g[cat]) for cat in CAT_ORDER}

    is_proxy = args.compare_field == "label_model_proxy"
    per_file_sorted = sorted(
        per_file_out,
        key=lambda x: (
            TIER_ORDER.index(x["tier"]) if x["tier"] in TIER_ORDER else 99,
            x["display_name"],
        ),
    )
    payload = {
        "schema_version": 1,
        "primary_field": args.primary_field,
        "compare_field": args.compare_field,
        "note_compare": "proxy rater (not human IRR)" if is_proxy else "human second rater",
        "root": artifact_relpath(args.root),
        "categories_axis": list(CAT_ORDER),
        "per_file": per_file_sorted,
        "per_tier": per_tier,
        "global": global_block,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} ({len(per_file_out)} files with pairs)", file=sys.stderr)


if __name__ == "__main__":
    main()
