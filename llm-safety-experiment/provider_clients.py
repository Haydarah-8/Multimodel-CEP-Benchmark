"""
Multi-provider completions for the same user prompt text.

Used by run_experiment.py and run_multi_model.py. All providers return plain text
or an "ERROR: ..." string on failure (never raise into the result row).
"""

from __future__ import annotations

import os
from typing import Literal

MAX_TOKENS = 200

# Gemini needs a higher ceiling than OpenAI/Anthropic: Pro can use budget before visible text;
# Flash truncates mid-sentence if this is too low. Override with GEMINI_MAX_OUTPUT_TOKENS.
_DEFAULT_GEMINI_MAX_OUTPUT = 4096
_GEMINI_MAX_OUTPUT_CAP = 8192

ProviderName = Literal["openai", "anthropic", "gemini"]


def gemini_api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def gemini_max_output_tokens() -> int:
    """Max output tokens for Gemini only (not shared with MAX_TOKENS for other providers)."""
    raw = (os.getenv("GEMINI_MAX_OUTPUT_TOKENS") or "").strip()
    if not raw:
        return _DEFAULT_GEMINI_MAX_OUTPUT
    try:
        n = int(raw, 10)
    except ValueError:
        return _DEFAULT_GEMINI_MAX_OUTPUT
    if n < 1:
        return _DEFAULT_GEMINI_MAX_OUTPUT
    return min(n, _GEMINI_MAX_OUTPUT_CAP)


def _gemini_finish_reason_label(fr: object) -> str:
    """Map API finish_reason (int or enum) to a readable name."""
    if fr is None:
        return "unknown"
    try:
        from google.generativeai import protos

        enum_val = protos.Candidate.FinishReason(fr) if isinstance(fr, int) else fr
        return str(enum_val.name)
    except (ValueError, TypeError, AttributeError):
        return str(fr)


def complete(provider: ProviderName, model: str, user_text: str) -> str:
    """Dispatch to OpenAI, Anthropic, or Gemini."""
    if provider == "openai":
        return _complete_openai(model, user_text)
    if provider == "anthropic":
        return _complete_anthropic(model, user_text)
    if provider == "gemini":
        return _complete_gemini(model, user_text)
    raise ValueError(f"Unknown provider: {provider!r}")


def _complete_openai(model: str, user_text: str) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "ERROR: Missing OPENAI_API_KEY"
    try:
        client = OpenAI(api_key=api_key)
        # Reasoning models (o1/o3/o4 families) use max_completion_tokens; standard chat uses max_tokens.
        if model.startswith(("o1", "o3", "o4")):
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_text}],
                max_completion_tokens=MAX_TOKENS,
            )
        else:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_text}],
                max_tokens=MAX_TOKENS,
            )
        choice = completion.choices[0].message
        content = choice.content if choice else None
        return (content or "").strip()
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {type(exc).__name__}: {exc}"


def _complete_anthropic(model: str, user_text: str) -> str:
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "ERROR: Missing ANTHROPIC_API_KEY"
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": user_text}],
        )
        parts: list[str] = []
        for block in message.content:
            if hasattr(block, "text") and block.text:
                parts.append(block.text)
        return "".join(parts).strip()
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {type(exc).__name__}: {exc}"


def _gemini_text_from_candidates(resp: object) -> str:
    """Collect text from candidates; never use ``response.text`` (it raises if no Parts)."""
    parts: list[str] = []
    for c in getattr(resp, "candidates", None) or []:
        content = getattr(c, "content", None)
        for part in getattr(content, "parts", []) or []:
            t = getattr(part, "text", None)
            if t:
                parts.append(t)
    return "".join(parts).strip()


def _gemini_no_text_message(resp: object) -> str:
    """Stable string when the model returns no user-visible text; not an API failure."""
    pb = getattr(resp, "prompt_feedback", None)
    br = getattr(pb, "block_reason", None) if pb else None
    if br is not None:
        return f"[No model text: prompt blocked; block_reason={br}]"
    candidates = getattr(resp, "candidates", None) or []
    if not candidates:
        return "[No model text: no candidates]"
    fr = getattr(candidates[0], "finish_reason", None)
    fr_label = _gemini_finish_reason_label(fr)
    return f"[No model text: empty output; {fr_label}]"


def _complete_gemini(model: str, user_text: str) -> str:
    import google.generativeai as genai

    key = gemini_api_key()
    if not key:
        return "ERROR: Missing GEMINI_API_KEY or GOOGLE_API_KEY"
    try:
        genai.configure(api_key=key)
        generative = genai.GenerativeModel(model)
        max_out = gemini_max_output_tokens()
        resp = generative.generate_content(
            user_text,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_out,
            ),
        )
        text = _gemini_text_from_candidates(resp)
        if text:
            return text
        return _gemini_no_text_message(resp)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {type(exc).__name__}: {exc}"
