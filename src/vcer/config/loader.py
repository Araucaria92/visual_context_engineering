from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from ruamel.yaml import YAML


def load_config(root: Path) -> Dict[str, Any]:
    path = root / ".vcer.yml"
    yaml = YAML(typ="safe")
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.load(f) or {}

