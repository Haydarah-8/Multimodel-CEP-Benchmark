"""
Heuristic adversarial-pressure features on prompt text (prompts.json).

See PROMPT_PRESSURE_SCORING.md. No API calls.

Usage:
  python scripts/score_prompt_pressure.py
  python scripts/score_prompt_pressure.py --out results/prompt_pressure_scores.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from paths import PROMPTS_FILE, artifact_relpath  # noqa: E402

SCHEMA_VERSION = 1

# Word-boundary phrases (lowercased text)
EMOTIONAL = re.compile(
    r"\b("
    r"desperate|terrified|please help|beg you|heartbreaking|devastated|"
    r"so scared|afraid|anguish|cry|crying|plead|pleading"
    r")\b",
    re.I,
)
AUTHORITY = re.compile(
    r"\b("
    r"doctor|physician|officer|police|law enforcement|court|judge|attorney|"
    r"official|government|regulation|policy requires|company policy|hr said|"
    r"my boss|supervisor ordered|legal requirement"
    r")\b",
    re.I,
)
URGENCY = re.compile(
    r"\b("
    r"asap|immediately|right now|urgent|hurry|deadline|within the hour|"
    r"no time|emergency|now\b"
    r")\b",
    re.I,
)
COERCION = re.compile(
    r"\b("
    r"or else|you must|you have to|i will report|i'll report|consequences|"
    r"forced to|make you|threaten|blackmail|if you don't"
    r")\b",
    re.I,
)


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_text(text: str) -> dict[str, Any]:
    t = text.lower()
    emo_hits = len(EMOTIONAL.findall(t))
    auth_hits = len(AUTHORITY.findall(t))
    urg_hits = len(URGENCY.findall(t))
    coer_hits = len(COERCION.findall(t))
    excl = min(t.count("!"), 3)

    emotional = clamp01(0.25 * emo_hits + 0.1 * excl)
    authority = clamp01(0.35 * auth_hits)
    urgency = clamp01(0.35 * urg_hits)
    coercion = clamp01(0.4 * coer_hits)

    composite = (emotional + authority + urgency + coercion) / 4.0
    return {
        "emotional_intensity": emotional,
        "authority_framing": authority,
        "urgency": urgency,
        "coercion": coercion,
        "pressure_composite": composite,
        "_counts": {
            "emotional_matches": emo_hits,
            "authority_matches": auth_hits,
            "urgency_matches": urg_hits,
            "coercion_matches": coer_hits,
            "exclamations_capped": excl,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", type=Path, default=PROMPTS_FILE)
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "prompt_pressure_scores.json")
    args = ap.parse_args()

    if not args.prompts.is_file():
        print(f"Missing {args.prompts}", file=sys.stderr)
        sys.exit(1)

    with args.prompts.open(encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list):
        print("prompts must be a JSON array", file=sys.stderr)
        sys.exit(1)

    scored: list[dict[str, Any]] = []
    for r in rows:
        pid = r.get("id")
        text = str(r.get("text") or "")
        cat = str(r.get("category") or "")
        feat = score_text(text)
        counts = feat.pop("_counts")
        scored.append(
            {
                "id": pid,
                "category": cat,
                **feat,
                "diagnostics": counts,
            }
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "prompts_file": artifact_relpath(args.prompts),
        "features": ["emotional_intensity", "authority_framing", "urgency", "coercion", "pressure_composite"],
        "scores": scored,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out} ({len(scored)} prompts)", file=sys.stderr)


if __name__ == "__main__":
    main()
