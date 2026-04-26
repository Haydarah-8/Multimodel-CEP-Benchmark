"""
Cross-model decision-boundary audit: ordinal discordance on the same prompt id + pairwise label pairs.

See DECISION_BOUNDARY_AUDIT.md. No logits — descriptive only.

Usage:
  python scripts/decision_boundary_audit.py
  python scripts/decision_boundary_audit.py --multimodel-root results/multimodel/cheap
  python scripts/decision_boundary_audit.py --paired-csv results/multimodel/paired_labels_wide.csv \\
      --out-json boundary_audit.json --out-csv-discord high_discord.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compute_significance import CAT_ORDER  # noqa: E402
from paths import PILOT_RESULTS_JSON  # noqa: E402

LABELS = ("safe", "partial", "unsafe")
ORD: dict[str, int] = {"safe": 0, "partial": 1, "unsafe": 2}


def discover_multimodel_results(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("results_*.json"))


def stem_from_path(p: Path) -> str:
    return p.stem


def load_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def build_wide_from_files(files: list[Path]) -> tuple[dict[Any, str], dict[Any, dict[str, str]], list[str]]:
    category_by_id: dict[Any, str] = {}
    labels_by_id: dict[Any, dict[str, str]] = defaultdict(dict)
    for fp in files:
        stem = "pilot_results" if fp.resolve() == PILOT_RESULTS_JSON.resolve() else stem_from_path(fp)
        rows = load_rows(fp)
        for r in rows:
            rid = r.get("id")
            cat = str(r.get("category") or "")
            lab = (r.get("label") or "").strip().lower()
            if rid not in category_by_id and cat:
                category_by_id[rid] = cat
            if lab and lab in ORD:
                labels_by_id[rid][stem] = lab
    stems = sorted({s for d in labels_by_id.values() for s in d})
    return category_by_id, labels_by_id, stems


def build_wide_from_csv(path: Path) -> tuple[dict[Any, str], dict[Any, dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise ValueError("Empty CSV")
        fieldnames = list(r.fieldnames)
        stems = [h for h in fieldnames if h not in ("id", "category")]
        category_by_id: dict[Any, str] = {}
        labels_by_id: dict[Any, dict[str, str]] = defaultdict(dict)
        for row in r:
            rid = row.get("id")
            category_by_id[rid] = str(row.get("category") or "")
            for s in stems:
                lab = (row.get(s) or "").strip().lower()
                if lab in ORD:
                    labels_by_id[rid][s] = lab
        return category_by_id, labels_by_id, stems


def fleiss_kappa(counts_matrix: np.ndarray) -> float | None:
    """
    counts_matrix: shape (N_items, k_categories), each row sums to n_raters (constant).
    """
    if counts_matrix.size == 0:
        return None
    N, k = counts_matrix.shape
    n = float(counts_matrix[0].sum())
    if n <= 1 or abs(counts_matrix.sum(axis=1) - n).max() > 1e-6:
        return None
    P_i = np.sum(counts_matrix * (counts_matrix - 1), axis=1) / (n * (n - 1))
    P_bar = float(np.mean(P_i))
    p_j = np.sum(counts_matrix, axis=0) / (N * n)
    P_e = float(np.sum(p_j**2))
    if abs(1.0 - P_e) < 1e-12:
        return None
    return (P_bar - P_e) / (1.0 - P_e)


def majority_label(scores: list[int], label_seq: list[str]) -> str:
    labs = [label_seq[s] for s in scores]
    c = Counter(labs)
    best = max(c.values())
    candidates = sorted([lab for lab, v in c.items() if v == best])
    tie_order = ["partial", "safe", "unsafe"]
    for pref in tie_order:
        if pref in candidates:
            return pref
    return candidates[0]


def marginal_shifts_for_stem(
    category_by_id: dict[Any, str],
    labels_by_id: dict[Any, dict[str, str]],
    stem: str,
) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, int]] = {c: {lab: 0 for lab in LABELS} for c in CAT_ORDER}
    for rid, labs in labels_by_id.items():
        if stem not in labs:
            continue
        cat = str(category_by_id.get(rid, "")).strip().lower()
        if cat not in counts:
            continue
        lab = labs[stem]
        counts[cat][lab] += 1
    out: list[dict[str, Any]] = []
    for i in range(len(CAT_ORDER) - 1):
        c0, c1 = CAT_ORDER[i], CAT_ORDER[i + 1]
        n0 = sum(counts[c0][l] for l in LABELS)
        n1 = sum(counts[c1][l] for l in LABELS)
        p0p = counts[c0]["partial"] / n0 if n0 else 0.0
        p1p = counts[c1]["partial"] / n1 if n1 else 0.0
        p0u = counts[c0]["unsafe"] / n0 if n0 else 0.0
        p1u = counts[c1]["unsafe"] / n1 if n1 else 0.0
        out.append(
            {
                "from_category": c0,
                "to_category": c1,
                "delta_p_partial": p1p - p0p,
                "delta_p_unsafe": p1u - p0u,
            }
        )
    return out


def run_audit(
    category_by_id: dict[Any, str],
    labels_by_id: dict[Any, dict[str, str]],
    stems: list[str],
) -> dict[str, Any]:
    complete_ids: list[Any] = []
    per_id: list[dict[str, Any]] = []
    counts_for_fleiss: list[list[int]] = []

    n_ge1 = 0
    n_eq2 = 0
    maj_fracs: list[float] = []

    pairwise: dict[str, dict[str, Counter[tuple[str, str]]]] = defaultdict(lambda: defaultdict(Counter))

    for rid, labs in sorted(labels_by_id.items(), key=lambda x: (str(category_by_id.get(x[0], "")), str(x[0]))):
        if any(s not in labs for s in stems):
            continue
        scores = [ORD[labs[s]] for s in stems]
        rng = max(scores) - min(scores)
        var = float(np.var(scores, ddof=0))
        maj = majority_label(scores, list(LABELS))
        maj_count = sum(1 for s in stems if labs[s] == maj)
        maj_fracs.append(maj_count / len(stems))

        row_counts = [0, 0, 0]
        for s in stems:
            row_counts[ORD[labs[s]]] += 1
        counts_for_fleiss.append(row_counts)

        if rng >= 1:
            n_ge1 += 1
        if rng == 2:
            n_eq2 += 1

        per_id.append(
            {
                "id": rid,
                "category": category_by_id.get(rid, ""),
                "range": rng,
                "variance": var,
                "majority_label": maj,
                "labels": {s: labs[s] for s in stems},
            }
        )
        complete_ids.append(rid)

        for a, b in permutations(stems, 2):
            pairwise[a][b][(labs[a], labs[b])] += 1

    mat = np.array(counts_for_fleiss, dtype=float) if counts_for_fleiss else np.zeros((0, 3))
    kappa = fleiss_kappa(mat) if mat.shape[0] else None

    pairwise_out: dict[str, Any] = {}
    for a in stems:
        pairwise_out[a] = {}
        for b in stems:
            if a == b:
                continue
            cdict = {f"{x[0]}|{x[1]}": v for x, v in sorted(pairwise[a][b].items())}
            pairwise_out[a][b] = cdict

    marginal: dict[str, list[dict[str, Any]]] = {}
    for s in stems:
        marginal[s] = marginal_shifts_for_stem(category_by_id, labels_by_id, s)

    return {
        "n_models": len(stems),
        "model_stems": stems,
        "n_prompts_any_label": len(labels_by_id),
        "n_prompts_complete_across_models": len(complete_ids),
        "boundary_prompts_range_ge_1": n_ge1,
        "boundary_prompts_range_eq_2_polar": n_eq2,
        "mean_majority_fraction": float(np.mean(maj_fracs)) if maj_fracs else None,
        "fleiss_kappa_ordinal_categories": kappa,
        "per_prompt_complete": per_id,
        "pairwise_directed_label_counts": pairwise_out,
        "marginal_shift_adjacent_by_model": marginal,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Cross-model boundary audit (ordinal labels)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--paired-csv",
        type=Path,
        default=None,
        help="Wide paired table (id, category, <model stems>...)",
    )
    g.add_argument(
        "--multimodel-root",
        type=Path,
        default=None,
        help="Discover results_*.json under this tree (default: results/multimodel)",
    )
    ap.add_argument("--also-pilot", action="store_true", help=f"Prepend {PILOT_RESULTS_JSON.name} when using --multimodel-root")
    ap.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "results" / "multimodel" / "boundary_audit.json",
    )
    ap.add_argument(
        "--out-csv-discord",
        type=Path,
        default=None,
        help="Optional CSV: ids with range>=1 for qualitative follow-up",
    )
    ap.add_argument("--min-range", type=int, default=1, help="Include ids with range >= this (default 1)")
    args = ap.parse_args()

    if args.paired_csv:
        category_by_id, labels_by_id, stems = build_wide_from_csv(args.paired_csv)
        src = str(args.paired_csv)
    else:
        root = args.multimodel_root or (ROOT / "results" / "multimodel")
        files = discover_multimodel_results(root)
        if args.also_pilot and PILOT_RESULTS_JSON.is_file():
            files = [PILOT_RESULTS_JSON] + files
        if not files:
            print("No inputs: use --paired-csv or place results_*.json under multimodel root.", file=sys.stderr)
            sys.exit(1)
        category_by_id, labels_by_id, stems = build_wide_from_files(files)
        src = str(root)

    if len(stems) < 2:
        print("Need at least two model columns for cross-model audit.", file=sys.stderr)
        sys.exit(1)

    payload = run_audit(category_by_id, labels_by_id, stems)
    payload["source"] = src
    payload["ordinal_map"] = dict(ORD)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    # Slim JSON: omit full per_prompt by default? Plan says boundary_audit.json + optional CSV
    slim = {k: v for k, v in payload.items() if k != "per_prompt_complete"}
    slim["per_prompt_complete_n"] = len(payload["per_prompt_complete"])
    args.out_json.write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out_json}", file=sys.stderr)

    full_path = args.out_json.with_name(args.out_json.stem + "_full.json")
    full_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {full_path} (includes per_prompt_complete)", file=sys.stderr)

    if args.out_csv_discord:
        min_r = max(0, args.min_range)
        rows = [p for p in payload["per_prompt_complete"] if p["range"] >= min_r]
        args.out_csv_discord.parent.mkdir(parents=True, exist_ok=True)
        with args.out_csv_discord.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["id", "category", "range", "variance", "majority_label"]
                + [f"label_{s}" for s in stems],
            )
            w.writeheader()
            for p in rows:
                row = {
                    "id": p["id"],
                    "category": p["category"],
                    "range": p["range"],
                    "variance": p["variance"],
                    "majority_label": p["majority_label"],
                }
                for s in stems:
                    row[f"label_{s}"] = p["labels"].get(s, "")
                w.writerow(row)
        print(f"Wrote {args.out_csv_discord} ({len(rows)} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
