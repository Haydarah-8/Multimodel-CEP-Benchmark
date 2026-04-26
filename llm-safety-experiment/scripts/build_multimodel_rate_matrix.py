"""
Build model × category rate matrices (unsafe or risk) from labeled multimodel JSON files.

Also computes normalization layer: baseline P(safe|direct), excess unsafe vs direct, verbosity summaries.

Usage (from llm-safety-experiment):
  python scripts/build_multimodel_rate_matrix.py
  python scripts/build_multimodel_rate_matrix.py --metric risk --tier cheap
  python scripts/build_multimodel_rate_matrix.py --root results/multimodel/mid --out figures/multimodel/signature_matrix.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compute_significance import CAT_ORDER  # noqa: E402
from paths import MULTIMODEL_DIR, artifact_relpath  # noqa: E402

TIER_ORDER = ("cheap", "mid", "expensive")
VALID = {"safe", "partial", "unsafe"}


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
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def response_log_len(response: str | None) -> float | None:
    if not response or not isinstance(response, str):
        return None
    if response.lstrip().upper().startswith("ERROR:"):
        return None
    return math.log(1 + len(response))


def model_sort_key(entry: dict[str, Any]) -> tuple[int, str, str, str]:
    tier = entry["tier"]
    try:
        ti = TIER_ORDER.index(tier)
    except ValueError:
        ti = 99
    return (ti, str(entry.get("provider", "")), str(entry.get("model", "")), str(entry.get("file_stem", "")))


def compute_file_block(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    tier = tier_from_path(path)
    provider = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
    model = next((str(r.get("model")) for r in rows if r.get("model")), "")
    file_stem = stem_from_path(path)

    labeled = [
        r
        for r in rows
        if str(r.get("label", "")).strip().lower() in VALID
    ]

    by_cat: dict[str, list[dict[str, Any]]] = {c: [] for c in CAT_ORDER}
    for r in labeled:
        cat = str(r.get("category", "")).strip().lower()
        if cat in by_cat:
            by_cat[cat].append(r)

    p_unsafe: list[float] = []
    p_risk: list[float] = []
    p_safe: list[float] = []
    n_per_cat: list[int] = []
    unsafe_per_cat: list[int] = []
    risk_per_cat: list[int] = []

    for c in CAT_ORDER:
        block = by_cat[c]
        n = len(block)
        n_per_cat.append(n)
        nu = sum(1 for r in block if str(r.get("label")).lower() == "unsafe")
        nr = sum(1 for r in block if str(r.get("label")).lower() in ("partial", "unsafe"))
        ns = sum(1 for r in block if str(r.get("label")).lower() == "safe")
        unsafe_per_cat.append(nu)
        risk_per_cat.append(nr)
        if n > 0:
            p_unsafe.append(nu / n)
            p_risk.append(nr / n)
            p_safe.append(ns / n)
        else:
            p_unsafe.append(float("nan"))
            p_risk.append(float("nan"))
            p_safe.append(float("nan"))

    # Baseline B_m = P(safe|direct)
    idx_direct = CAT_ORDER.index("direct")
    n_dir = n_per_cat[idx_direct]
    if n_dir > 0:
        baseline_refusal_direct = p_safe[idx_direct]
        p_unsafe_direct = p_unsafe[idx_direct]
    else:
        # fallback: global safe rate
        if labeled:
            baseline_refusal_direct = sum(
                1 for r in labeled if str(r.get("label")).lower() == "safe"
            ) / len(labeled)
            p_unsafe_direct = sum(
                1 for r in labeled if str(r.get("label")).lower() == "unsafe"
            ) / len(labeled)
        else:
            baseline_refusal_direct = float("nan")
            p_unsafe_direct = float("nan")

    excess_unsafe_vs_direct: list[float | None] = []
    for i in range(len(CAT_ORDER)):
        if n_per_cat[i] == 0 or math.isnan(p_unsafe[i]):
            excess_unsafe_vs_direct.append(None)
        elif math.isnan(p_unsafe_direct):
            excess_unsafe_vs_direct.append(None)
        else:
            excess_unsafe_vs_direct.append(p_unsafe[i] - p_unsafe_direct)

    log_lens: list[float] = []
    for r in labeled:
        ll = response_log_len(str(r.get("response") or ""))
        if ll is not None:
            log_lens.append(ll)
    log_lens.sort()
    n_ll = len(log_lens)
    if n_ll == 0:
        verbosity = {"median_log1p_len": None, "q25": None, "q75": None, "n_rows_with_length": 0}
    else:
        mid = n_ll // 2
        med = log_lens[mid] if n_ll % 2 else 0.5 * (log_lens[mid - 1] + log_lens[mid])
        q1i = n_ll // 4
        q3i = (3 * n_ll) // 4
        verbosity = {
            "median_log1p_len": med,
            "q25": log_lens[q1i],
            "q75": log_lens[min(q3i, n_ll - 1)],
            "n_rows_with_length": n_ll,
        }

    display_name = f"{provider} / {model}".strip(" /") if (provider or model) else file_stem

    return {
        "path": artifact_relpath(path),
        "tier": tier,
        "provider": provider,
        "model": model,
        "file_stem": file_stem,
        "display_name": display_name,
        "n_labeled_total": len(labeled),
        "n_per_category": n_per_cat,
        "unsafe_count_per_category": unsafe_per_cat,
        "risk_count_per_category": risk_per_cat,
        "p_unsafe_per_category": p_unsafe,
        "p_risk_per_category": p_risk,
        "p_safe_per_category": p_safe,
        "normalization": {
            "baseline_P_safe_given_direct": baseline_refusal_direct,
            "P_unsafe_given_direct": p_unsafe_direct,
            "excess_P_unsafe_vs_direct": excess_unsafe_vs_direct,
        },
        "verbosity_log1p_response_len": verbosity,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Build multimodel rate matrix + normalization JSON")
    ap.add_argument("--root", type=Path, default=MULTIMODEL_DIR)
    ap.add_argument("--include-archive", action="store_true", help="Include results under .../archive/...")
    ap.add_argument("--tier", choices=[*TIER_ORDER, "all"], default="all")
    ap.add_argument("--metric", choices=("unsafe", "risk"), default="unsafe")
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "signature_rate_matrix.json",
    )
    ap.add_argument(
        "--out-normalization",
        type=Path,
        default=None,
        help="Optional second file with normalization + verbosity only",
    )
    args = ap.parse_args()

    files = discover_files(args.root, args.include_archive)
    if args.tier != "all":
        files = [p for p in files if tier_from_path(p) == args.tier]

    if not files:
        print(f"No results_*.json under {args.root}", file=sys.stderr)
        sys.exit(1)

    per_file: list[dict[str, Any]] = []
    for fp in files:
        rows = load_rows(fp)
        per_file.append(compute_file_block(fp, rows))

    per_file.sort(key=model_sort_key)

    p_matrix: list[list[float | None]] = []
    n_matrix: list[list[int]] = []
    for e in per_file:
        ns = e["n_per_category"]
        if args.metric == "unsafe":
            src = e["p_unsafe_per_category"]
        else:
            src = e["p_risk_per_category"]
        row: list[float | None] = []
        for i, x in enumerate(src):
            if ns[i] == 0:
                row.append(None)
            elif isinstance(x, float) and math.isnan(x):
                row.append(None)
            else:
                row.append(float(x))
        p_matrix.append(row)
        n_matrix.append(list(ns))

    excess_matrix: list[list[float | None]] = []
    for e in per_file:
        excess_matrix.append(list(e["normalization"]["excess_P_unsafe_vs_direct"]))

    payload: dict[str, Any] = {
        "schema_version": 1,
        "metric": args.metric,
        "categories": list(CAT_ORDER),
        "tier_filter": args.tier,
        "root": artifact_relpath(args.root),
        "models": [
            {
                "display_name": e["display_name"],
                "tier": e["tier"],
                "provider": e["provider"],
                "model": e["model"],
                "file_stem": e["file_stem"],
                "path": e["path"],
            }
            for e in per_file
        ],
        "p_hat": p_matrix,
        "n": n_matrix,
        "excess_p_unsafe_vs_direct": excess_matrix,
        "per_file": per_file,
    }

    norm_only = {
        "schema_version": 1,
        "root": artifact_relpath(args.root),
        "tier_filter": args.tier,
        "models": [
            {
                "display_name": e["display_name"],
                "tier": e["tier"],
                "path": e["path"],
                "baseline_P_safe_given_direct": e["normalization"]["baseline_P_safe_given_direct"],
                "P_unsafe_given_direct": e["normalization"]["P_unsafe_given_direct"],
                "excess_P_unsafe_vs_direct": e["normalization"]["excess_P_unsafe_vs_direct"],
                "verbosity_log1p_response_len": e["verbosity_log1p_response_len"],
            }
            for e in per_file
        ],
    }

    def nan_to_none(obj: Any) -> Any:
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, list):
            return [nan_to_none(x) for x in obj]
        if isinstance(obj, dict):
            return {k: nan_to_none(v) for k, v in obj.items()}
        return obj

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(nan_to_none(payload), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}", file=sys.stderr)

    if args.out_normalization:
        args.out_normalization.parent.mkdir(parents=True, exist_ok=True)
        args.out_normalization.write_text(json.dumps(nan_to_none(norm_only), indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {args.out_normalization}", file=sys.stderr)


if __name__ == "__main__":
    main()
