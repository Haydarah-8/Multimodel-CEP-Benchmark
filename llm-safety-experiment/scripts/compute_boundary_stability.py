"""
Boundary consistency under perturbation (ordinal safe / partial / unsafe).

- cross-model: same align_key across model stems → variance / Fleiss κ (wave-aware).
- cross-variant: same parent intent + model → variance across mutation variants.

See BOUNDARY_STABILITY.md. Run from llm-safety-experiment:

  python scripts/compute_boundary_stability.py cross-model --multimodel-root results/multimodel/cheap
  python scripts/compute_boundary_stability.py cross-model --multimodel-root results/multimodel/cheap --mutation-wave my_wave
  python scripts/compute_boundary_stability.py cross-variant --results path/to/labeled.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in (ROOT, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from decision_boundary_audit import (  # noqa: E402
    LABELS,
    ORD,
    discover_multimodel_results,
    load_rows,
    majority_label,
    run_audit,
    stem_from_path,
)
from paths import PILOT_RESULTS_JSON, artifact_relpath  # noqa: E402

SCHEMA_VERSION = 1


def align_key_from_row(row: dict[str, Any]) -> str:
    """Wave rows: (parent_prompt_id, mutation_kind, mutation_variant). Else canonical (id,)."""
    pid = row.get("parent_prompt_id")
    if pid is None and "parent_id" in row:
        pid = row.get("parent_id")
    mk = row.get("mutation_kind")
    mv = row.get("mutation_variant")
    if pid is not None and mk is not None and mv is not None:
        return json.dumps({"parent_prompt_id": pid, "mutation_kind": mk, "mutation_variant": mv}, sort_keys=True)
    return json.dumps({"id": row.get("id")}, sort_keys=True)


def variant_key_from_row(row: dict[str, Any]) -> str:
    mk = row.get("mutation_kind")
    mv = row.get("mutation_variant")
    if mk is not None and mv is not None:
        return json.dumps({"mutation_kind": mk, "mutation_variant": mv}, sort_keys=True)
    return json.dumps({"id": row.get("id")}, sort_keys=True)


def parent_group_key(row: dict[str, Any]) -> Any:
    if row.get("parent_prompt_id") is not None:
        return row.get("parent_prompt_id")
    if row.get("parent_id") is not None:
        return row.get("parent_id")
    return row.get("id")


def row_matches_wave(row: dict[str, Any], wave: str | None) -> bool:
    if not wave:
        return True
    return str(row.get("mutation_wave") or "") == wave


def build_wide_by_align_key(
    files: list[Path],
    *,
    mutation_wave: str | None,
) -> tuple[dict[str, str], dict[str, dict[str, str]], list[str]]:
    category_by_align: dict[str, str] = {}
    labels_by_align: dict[str, dict[str, str]] = defaultdict(dict)
    for fp in files:
        stem = "pilot_results" if fp.resolve() == PILOT_RESULTS_JSON.resolve() else stem_from_path(fp)
        for r in load_rows(fp):
            if not row_matches_wave(r, mutation_wave):
                continue
            ak = align_key_from_row(r)
            cat = str(r.get("category") or "")
            if ak not in category_by_align and cat:
                category_by_align[ak] = cat
            lab = (r.get("label") or "").strip().lower()
            if lab in ORD:
                labels_by_align[ak][stem] = lab
    stems = sorted({s for d in labels_by_align.values() for s in d})
    return category_by_align, labels_by_align, stems


def run_cross_variant(
    paths: list[Path],
    *,
    mutation_wave: str | None,
    full: bool,
) -> dict[str, Any]:
    per_group: list[dict[str, Any]] = []
    for fp in paths:
        rows = load_rows(fp)
        provider = str(next((r.get("provider") or "" for r in rows if r.get("provider")), ""))
        model = str(next((r.get("model") or "" for r in rows if r.get("model")), ""))
        by_parent: dict[Any, dict[str, tuple[str, dict[str, Any]]]] = defaultdict(dict)
        for r in rows:
            if not row_matches_wave(r, mutation_wave):
                continue
            lab = (r.get("label") or "").strip().lower()
            if lab not in ORD:
                continue
            pk = parent_group_key(r)
            vk = variant_key_from_row(r)
            by_parent[pk][vk] = (lab, r)

        for pk, variants in sorted(by_parent.items(), key=lambda x: (str(type(x[0])), str(x[0]))):
            if len(variants) < 2:
                continue
            scores = [ORD[v[0]] for v in variants.values()]
            labs_only = [v[0] for v in variants.values()]
            rng = max(scores) - min(scores)
            var = float(np.var(scores, ddof=0))
            maj = majority_label(scores, list(LABELS))
            sample_r = next(iter(variants.values()))[1]
            cat = str(sample_r.get("category") or "")
            entry: dict[str, Any] = {
                "parent_prompt_id": pk,
                "provider": provider,
                "model": model,
                "category": cat,
                "n_variants": len(variants),
                "range": rng,
                "variance": var,
                "majority_label": maj,
                "labels_by_variant": {vk: variants[vk][0] for vk in variants},
            }
            if full:
                entry["source_file"] = artifact_relpath(fp)
            per_group.append(entry)

    variances = [g["variance"] for g in per_group]
    ranges = [g["range"] for g in per_group]
    summary = {
        "n_parent_model_groups_eligible": len(per_group),
        "mean_variance": float(np.mean(variances)) if variances else None,
        "median_variance": float(np.median(variances)) if variances else None,
        "fraction_range_ge_1": float(sum(1 for r in ranges if r >= 1) / len(ranges)) if ranges else None,
        "fraction_range_eq_2_polar": float(sum(1 for r in ranges if r == 2) / len(ranges)) if ranges else None,
    }
    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mode": "cross_variant",
        "ordinal_map": dict(ORD),
        "mutation_wave_filter": mutation_wave,
        "summary": summary,
    }
    if full:
        out["per_parent_model"] = per_group
    else:
        out["per_parent_model_n"] = len(per_group)
    return out


def cmd_cross_model(args: argparse.Namespace) -> None:
    root = args.multimodel_root or (ROOT / "results" / "multimodel")
    files = discover_multimodel_results(root)
    if args.also_pilot and PILOT_RESULTS_JSON.is_file():
        files = [PILOT_RESULTS_JSON] + files
    if not files:
        print("No results_*.json under multimodel root.", file=sys.stderr)
        sys.exit(1)
    category_by_align, labels_by_align, stems = build_wide_by_align_key(
        files, mutation_wave=args.mutation_wave
    )
    if len(stems) < 2:
        print("Need at least two model files (stems) for cross-model stability.", file=sys.stderr)
        sys.exit(1)
    payload = run_audit(category_by_align, labels_by_align, stems)
    payload["schema_version"] = SCHEMA_VERSION
    payload["mode"] = "cross_model"
    payload["ordinal_map"] = dict(ORD)
    payload["align_key_rule"] = (
        "parent_prompt_id+mutation_kind+mutation_variant if all present; else id-only JSON key"
    )
    payload["mutation_wave_filter"] = args.mutation_wave
    payload["source_root"] = artifact_relpath(root)

    out_path: Path = args.out_json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    slim = {k: v for k, v in payload.items() if k != "per_prompt_complete"}
    slim["per_prompt_complete_n"] = len(payload["per_prompt_complete"])
    out_path.write_text(json.dumps(slim, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)
    if args.full:
        full_path = out_path.with_name(out_path.stem + "_full.json")
        full_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {full_path}", file=sys.stderr)


def cmd_cross_variant(args: argparse.Namespace) -> None:
    paths = [p.resolve() for p in args.results]
    for p in paths:
        if not p.is_file():
            print(f"Missing {p}", file=sys.stderr)
            sys.exit(1)
    payload = run_cross_variant(paths, mutation_wave=args.mutation_wave, full=args.full)
    out_path: Path = args.out_json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description="Boundary stability: cross-model and cross-variant ordinal dispersion")
    sub = ap.add_subparsers(dest="command", required=True)

    m = sub.add_parser("cross-model", help="Align rows by wave-aware key; variance across models")
    m.add_argument("--multimodel-root", type=Path, default=None)
    m.add_argument("--also-pilot", action="store_true")
    m.add_argument("--mutation-wave", default=None, metavar="NAME", help="Only rows with this mutation_wave")
    m.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "results" / "multimodel" / "boundary_stability_cross_model.json",
    )
    m.add_argument("--full", action="store_true", help="Also write *_full.json with per_prompt_complete")
    m.set_defaults(func=cmd_cross_model)

    v = sub.add_parser("cross-variant", help="Per parent + model: variance across mutation variants")
    v.add_argument("--results", type=Path, nargs="+", required=True, help="Labeled results JSON file(s)")
    v.add_argument("--mutation-wave", default=None, metavar="NAME")
    v.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "results" / "multimodel" / "boundary_stability_cross_variant.json",
    )
    v.add_argument("--full", action="store_true", help="Include per_parent_model list")
    v.set_defaults(func=cmd_cross_variant)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
