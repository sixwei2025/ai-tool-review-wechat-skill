"""Load v2/rules.yaml (single source of numeric rules)."""
from __future__ import annotations
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]  # skill root (skills/公众号封面skill)

def load_rules(path: str | None = None) -> dict:
    p = Path(path) if path else ROOT / "rules.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))
