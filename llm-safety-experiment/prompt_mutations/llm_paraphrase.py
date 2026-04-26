"""Gated LLM paraphrase for mutation waves (Phase B)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from provider_clients import ProviderName, complete

from prompt_mutations.wave import MUTATION_SCHEMA_VERSION


def load_paraphrase_instruction(registry: dict[str, Any]) -> str:
    block = registry.get("llm_paraphrase") or {}
    return str(block.get("instruction") or "").strip()


def paraphrase_one(
    user_request: str,
    *,
    provider: ProviderName,
    model: str,
    instruction: str,
) -> tuple[str | None, str]:
    """
    Returns (rewritten_text_or_none, raw_model_output).
    """
    payload = json.dumps({"user_request": user_request}, ensure_ascii=False)
    user_text = f"{instruction}\n\nUSER_REQUEST_JSON:\n{payload}\n\nReply with JSON only: {{\"text\": \"...\"}}"
    raw = complete(provider, model, user_text)
    if raw.upper().startswith("ERROR:"):
        return None, raw
    text = _parse_json_text(raw)
    if not text or not text.strip():
        return None, raw
    return text.strip(), raw


def _parse_json_text(raw: str) -> str | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw).strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and "text" in obj:
            return str(obj["text"])
    except json.JSONDecodeError:
        pass
    i, j = raw.find("{"), raw.rfind("}")
    if i >= 0 and j > i:
        try:
            obj = json.loads(raw[i : j + 1])
            if isinstance(obj, dict) and "text" in obj:
                return str(obj["text"])
        except json.JSONDecodeError:
            pass
    return None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return re.sub(r"_+", "_", s).strip("_")[:80] or "x"


def append_llm_paraphrase_rows(
    seed_rows: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    provider: ProviderName,
    model: str,
    max_parents: int,
    variant_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    One paraphrase per seed row (up to max_parents). Returns (new_rows, audit_log).
    """
    instruction = load_paraphrase_instruction(registry)
    if not instruction:
        return [], []

    new_rows: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    n = 0
    for seed in seed_rows:
        if max_parents and n >= max_parents:
            break
        pid = seed.get("id")
        cat = str(seed.get("category") or "")
        text = str(seed.get("text") or "")
        new_text, raw = paraphrase_one(text, provider=provider, model=model, instruction=instruction)
        n += 1
        wid = f"{_slug(str(pid))}_m_llm_paraphrase_{variant_id}"
        mut = {
            "kind": "llm_paraphrase",
            "variant": variant_id,
            "rung": 0,
            "schema_version": MUTATION_SCHEMA_VERSION,
            "llm_provider": provider,
            "llm_model": model,
            "source_sha256": _sha256_text(text),
        }
        audit.append(
            {
                "parent_id": pid,
                "wave_id": wid,
                "ok": new_text is not None,
                "raw_excerpt": (raw[:500] + "…") if len(raw) > 500 else raw,
            }
        )
        if new_text is None:
            continue
        new_rows.append(
            {
                "id": wid,
                "parent_id": pid,
                "category": cat,
                "text": new_text,
                "mutation": mut,
            }
        )
    return new_rows, audit
