"""
Build expanded prompt waves from canonical seed rows + registry (rule-based mutations).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from paths import artifact_relpath  # noqa: E402

MUTATION_SCHEMA_VERSION = 1

KindFn = Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], list[dict[str, Any]]]


def load_registry(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("registry must be a JSON object")
    return data


def load_ladder_map(path: Path) -> dict[str, list[str]]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries") or {}
    if not isinstance(entries, dict):
        raise ValueError("ladder map needs entries object")
    out: dict[str, list[str]] = {}
    for k, v in entries.items():
        key = str(k)
        if isinstance(v, list):
            out[key] = [str(x) for x in v]
    return out


def _norm_id(x: Any) -> str:
    return str(x).strip()


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return re.sub(r"_+", "_", s).strip("_")[:80] or "x"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _mutation_obj(kind: str, variant: str, rung: int = 0, **extra: Any) -> dict[str, Any]:
    m: dict[str, Any] = {
        "kind": kind,
        "variant": variant,
        "rung": rung,
        "schema_version": MUTATION_SCHEMA_VERSION,
    }
    m.update(extra)
    return m


def _row(
    wave_id: str,
    parent_id: Any,
    category: str,
    text: str,
    mutation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": wave_id,
        "parent_id": parent_id,
        "category": category,
        "text": text,
        "mutation": mutation,
    }


def _find_ladder(registry: dict[str, Any], lid: str) -> dict[str, Any] | None:
    for item in registry.get("directness_ladder") or []:
        if isinstance(item, dict) and item.get("id") == lid:
            return item
    return None


def expand_baseline(seed: dict[str, Any]) -> dict[str, Any]:
    pid = seed.get("id")
    cat = str(seed.get("category") or "")
    text = str(seed.get("text") or "")
    wid = f"{_slug(_norm_id(pid))}_baseline"
    return _row(
        wid,
        pid,
        cat,
        text,
        _mutation_obj("baseline", "canonical", 0),
    )


def expand_role_shift(seed: dict[str, Any], registry: dict[str, Any], max_variants: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pid = seed.get("id")
    cat = str(seed.get("category") or "")
    text = str(seed.get("text") or "")
    variants = list(registry.get("role_shift") or [])[:max_variants]
    for v in variants:
        if not isinstance(v, dict):
            continue
        vid = str(v.get("id") or "variant")
        tpl = str(v.get("template") or "{text}")
        new_text = tpl.replace("{text}", text)
        wid = f"{_slug(_norm_id(pid))}_m_role_shift_{_slug(vid)}"
        out.append(
            _row(
                wid,
                pid,
                cat,
                new_text,
                _mutation_obj("role_shift", vid, 0, intensity=v.get("intensity")),
            )
        )
    return out


def expand_emotional(seed: dict[str, Any], registry: dict[str, Any], max_variants: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pid = seed.get("id")
    cat = str(seed.get("category") or "")
    text = str(seed.get("text") or "")
    variants = list(registry.get("emotional_escalation") or [])[:max_variants]
    for v in variants:
        if not isinstance(v, dict):
            continue
        vid = str(v.get("id") or "variant")
        prefix = str(v.get("prefix") or "")
        suffix = str(v.get("suffix") or "")
        new_text = f"{prefix}{text}{suffix}"
        wid = f"{_slug(_norm_id(pid))}_m_emotional_{_slug(vid)}"
        out.append(
            _row(
                wid,
                pid,
                cat,
                new_text,
                _mutation_obj(
                    "emotional_escalation",
                    vid,
                    0,
                    intensity=v.get("intensity"),
                ),
            )
        )
    return out


def expand_framing(seed: dict[str, Any], registry: dict[str, Any], max_variants: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pid = seed.get("id")
    cat = str(seed.get("category") or "")
    text = str(seed.get("text") or "")
    variants = list(registry.get("framing_pattern") or [])[:max_variants]
    for v in variants:
        if not isinstance(v, dict):
            continue
        vid = str(v.get("id") or "variant")
        prefix = str(v.get("prefix") or "")
        suffix = str(v.get("suffix") or "")
        new_text = f"{prefix}{text}{suffix}"
        wid = f"{_slug(_norm_id(pid))}_m_framing_{_slug(vid)}"
        out.append(
            _row(
                wid,
                pid,
                cat,
                new_text,
                _mutation_obj("framing_pattern", vid, 0, intensity=v.get("intensity")),
            )
        )
    return out


def expand_directness_ladder(
    seed: dict[str, Any],
    registry: dict[str, Any],
    ladder_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pid = seed.get("id")
    pid_s = _norm_id(pid)
    cat = str(seed.get("category") or "").strip().lower()
    if cat != "indirect":
        return out
    text = str(seed.get("text") or "")
    ladder_ids = ladder_map.get(pid_s) or ladder_map.get(str(int(pid_s)) if pid_s.isdigit() else pid_s)
    if not ladder_ids:
        return out
    for lid in ladder_ids:
        spec = _find_ladder(registry, lid)
        if not spec:
            continue
        suffix = str(spec.get("suffix") or "")
        rung = int(spec.get("rung") or 0)
        new_text = f"{text}{suffix}"
        wid = f"{_slug(pid_s)}_m_ladder_{_slug(lid)}_r{rung}"
        out.append(
            _row(
                wid,
                pid,
                cat,
                new_text,
                _mutation_obj("directness_ladder", lid, rung),
            )
        )
    return out


def expand_wave(
    seed_rows: list[dict[str, Any]],
    registry: dict[str, Any],
    kinds: set[str],
    ladder_map: dict[str, list[str]],
    *,
    max_variants_per_kind: int = 3,
    include_baseline: bool = True,
) -> list[dict[str, Any]]:
    """
    kinds: subset of baseline, role_shift, emotional_escalation, framing_pattern, directness_ladder
    """
    rows: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    def add_unique(r: dict[str, Any]) -> None:
        h = _sha256_text(r["text"])
        if h in seen_hashes:
            return
        seen_hashes.add(h)
        rows.append(r)

    for seed in seed_rows:
        if include_baseline and "baseline" in kinds:
            add_unique(expand_baseline(seed))
        if "role_shift" in kinds:
            for r in expand_role_shift(seed, registry, max_variants_per_kind):
                add_unique(r)
        if "emotional_escalation" in kinds:
            for r in expand_emotional(seed, registry, max_variants_per_kind):
                add_unique(r)
        if "framing_pattern" in kinds:
            for r in expand_framing(seed, registry, max_variants_per_kind):
                add_unique(r)
        if "directness_ladder" in kinds:
            for r in expand_directness_ladder(seed, registry, ladder_map):
                add_unique(r)

    return rows


def build_manifest(
    wave_name: str,
    seed_path: Path,
    registry_path: Path,
    ladder_path: Path | None,
    expanded: list[dict[str, Any]],
    kinds: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for r in expanded:
        k = (r.get("mutation") or {}).get("kind") or "unknown"
        counts[k] = counts.get(k, 0) + 1
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "wave_name": wave_name,
        "seed_file": artifact_relpath(seed_path),
        "registry_file": artifact_relpath(registry_path),
        "ladder_map_file": artifact_relpath(ladder_path) if ladder_path else None,
        "kinds_requested": kinds,
        "counts_by_kind": counts,
        "n_rows": len(expanded),
        "rows": [{"id": r["id"], "content_sha256": _sha256_text(r["text"])} for r in expanded],
    }
    if extra:
        manifest["extra"] = extra
    return manifest
