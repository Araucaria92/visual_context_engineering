from __future__ import annotations

from enum import Enum
from typing import List, Optional, TypedDict


class PartName(str, Enum):
    title = "title"
    task = "task"
    description = "description"
    constraints = "constraints"
    tools = "tools"
    output_format = "output_format"
    few_shot = "few_shot"
    evaluation = "evaluation"
    guardrails = "guardrails"
    metadata = "metadata"
    retrieval = "retrieval"
    other = "other"


class Part(TypedDict, total=False):
    name: str
    content: str
    source: str
    start_line: int
    end_line: int


DEFAULT_ORDER: List[str] = [
    "title",
    "task",
    "constraints",
    "tools",
    "output_format",
    "few_shot",
    "evaluation",
    "guardrails",
    "metadata",
    "retrieval",
]

