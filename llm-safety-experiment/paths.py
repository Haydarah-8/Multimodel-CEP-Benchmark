"""
Central paths for the LLM safety experiment package.

- Pilot (single-model, frozen): results/pilot/results.json
- Multi-model tier runs: results/multimodel/<cheap|mid|expensive>/
- Legacy flat files from older layouts: results/archive/legacy_flat/
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

RESULTS_ROOT = ROOT / "results"
PILOT_DIR = RESULTS_ROOT / "pilot"
PILOT_RESULTS_JSON = PILOT_DIR / "results.json"

MULTIMODEL_DIR = RESULTS_ROOT / "multimodel"
TIER_DIRS = {
    "cheap": MULTIMODEL_DIR / "cheap",
    "mid": MULTIMODEL_DIR / "mid",
    "expensive": MULTIMODEL_DIR / "expensive",
}

UNSORTED_MULTIMODEL_DIR = MULTIMODEL_DIR / "unsorted"
LEGACY_FLAT_ARCHIVE = RESULTS_ROOT / "archive" / "legacy_flat"

PROMPTS_FILE = ROOT / "prompts.json"
TIER_MODELS_CONFIG = ROOT / "configs" / "tier_models.json"
