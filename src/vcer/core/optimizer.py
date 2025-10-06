from __future__ import annotations

from typing import Any, Dict, List

from .parts import DEFAULT_ORDER, Part


def optimize_parts(data: Dict[str, Any], cfg: Dict[str, Any]) -> List[Part]:
    parts: List[Part] = data.get("parts", [])
    order = cfg.get("optimize", {}).get("order", DEFAULT_ORDER)
    priority = {name: i for i, name in enumerate(order)}

    def key(p: Part) -> tuple[int, int]:
        name = p.get("name", "other")
        return (priority.get(name, 999), p.get("start_line", 10**9))

    parts_sorted = sorted(parts, key=key)
    return parts_sorted


DISPLAY_NAME = {
    "title": "Title",
    "task": "Task",
    "description": "Description",
    "constraints": "Constraints",
    "tools": "Tools",
    "output_format": "Output Format",
    "few_shot": "Few-Shot Examples",
    "evaluation": "Evaluation Criteria",
    "guardrails": "Guardrails / Policy",
    "metadata": "Metadata",
    "retrieval": "Retrieval / Context",
    "other": "Other",
}


def render_markdown(parts: List[Part]) -> str:
    sections = []
    for p in parts:
        name = p.get("name", "other")
        title = DISPLAY_NAME.get(name, name.title())
        body = p.get("content", "").strip()
        sections.append(f"## {title}\n\n{body}\n")
    return "\n".join(sections).strip() + "\n"

