from __future__ import annotations

from typing import Any, Dict, List


def parts_to_mermaid(data: Dict[str, Any]) -> str:
    parts: List[Dict[str, Any]] = data.get("parts", [])
    lines: List[str] = ["flowchart LR"]
    # nodes
    for i, p in enumerate(parts):
        label = p.get("name", "other")
        safe = label.replace("_", " ").title()
        lines.append(f"  p{i}[\"{i+1}. {safe}\"]")
    # edges
    for i in range(len(parts) - 1):
        lines.append(f"  p{i} --> p{i+1}")
    return "\n".join(lines) + "\n"

