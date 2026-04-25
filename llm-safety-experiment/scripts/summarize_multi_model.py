"""
Print a compact per-model summary from multiple results_*.json files.

Usage (from llm-safety-experiment):
  python scripts/summarize_multi_model.py
  python scripts/summarize_multi_model.py results.json results_openai_gpt-4o-mini.json

Defaults: `results/pilot/results.json` plus every `results_*.json` under `results/multimodel/` (recursive) and `results/archive/legacy_flat/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import LEGACY_FLAT_ARCHIVE, MULTIMODEL_DIR, PILOT_RESULTS_JSON  # noqa: E402

VALID = {"safe", "partial", "unsafe"}


def summarize_file(path: Path) -> dict[str, float | int | str]:
    with path.open(encoding="utf-8") as f:
        rows: list[dict] = json.load(f)
    n = len(rows)
    labeled = [r for r in rows if str(r.get("label", "")).lower() in VALID]
    nl = len(labeled)
    if nl == 0:
        return {"file": path.name, "n": n, "labeled": 0, "error": "no labels"}

    u = sum(1 for r in labeled if str(r.get("label")).lower() == "unsafe")
    rsk = sum(1 for r in labeled if str(r.get("label")).lower() in ("partial", "unsafe"))

    out: dict[str, float | int | str] = {
        "file": path.name,
        "n": n,
        "labeled": nl,
        "pct_unsafe": 100.0 * u / nl,
        "pct_risk_R1": 100.0 * rsk / nl,
    }
    provider = next((str(r.get("provider")) for r in rows if r.get("provider")), "")
    if provider:
        out["provider"] = provider
    model = next((str(r.get("model")) for r in rows if r.get("model")), "")
    if model:
        out["model"] = model
    return out


def default_paths() -> list[Path]:
    """Pilot JSON + all results_*.json under results/multimodel/ and legacy archive."""
    out: list[Path] = []
    if PILOT_RESULTS_JSON.exists():
        out.append(PILOT_RESULTS_JSON)
    out.extend(sorted(MULTIMODEL_DIR.rglob("results_*.json")))
    if LEGACY_FLAT_ARCHIVE.is_dir():
        out.extend(sorted(LEGACY_FLAT_ARCHIVE.glob("results_*.json")))
    # de-dupe by resolve
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in out:
        r = p.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize labeled multi-model result files.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Results JSON files (default: pilot + results/multimodel/**/results_*.json)",
    )
    args = parser.parse_args()
    paths = [p.resolve() for p in args.paths] if args.paths else default_paths()
    if not paths:
        print("No results files found (pilot or multimodel).", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        if not p.exists():
            print(f"Skip missing: {p}", file=sys.stderr)
            continue
        s = summarize_file(p)
        print(f"\n== {s.get('file')} ==")
        if "error" in s:
            print(s["error"])
            continue
        print(f"n={s['n']}, labeled={s['labeled']}")
        if "provider" in s:
            print(f"provider={s['provider']!r}")
        if "model" in s:
            print(f"model={s['model']!r}")
        print(f"aggregate UNSAFE %: {s['pct_unsafe']:.1f}")
        print(f"aggregate R=1 (risk) %: {s['pct_risk_R1']:.1f}")


if __name__ == "__main__":
    main()
