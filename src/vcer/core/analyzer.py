from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .parts import Part


HEADER_PATTERNS = {
    "task": re.compile(r"^#{2,3}\s*Task\s*$", re.IGNORECASE),
    "constraints": re.compile(r"^#{2,3}\s*Constraints\s*$", re.IGNORECASE),
    "output_format": re.compile(r"^#{2,3}\s*Output\s*Format\s*$", re.IGNORECASE),
    "few_shot": re.compile(r"^#{2,3}\s*(Few[- ]?Shot|Examples)\s*$", re.IGNORECASE),
}

TAG_OPEN = re.compile(r"\[part:(?P<name>[a-z_]+)\]", re.IGNORECASE)
TAG_CLOSE = re.compile(r"\[/part\]", re.IGNORECASE)


def _read(path: Optional[Path]) -> str:
    return path.read_text(encoding="utf-8") if path else ""


def analyze_files(system_path: Path, user_path: Optional[Path], cfg: Dict[str, Any]) -> Dict[str, Any]:
    system_text = _read(system_path)
    user_text = _read(user_path)
    parts = _extract_parts(system_text)
    return {
        "system_file": str(system_path),
        "user_file": str(user_path) if user_path else None,
        "parts": parts,
    }


def _extract_parts(text: str) -> List[Part]:
    # 1) tag blocks take precedence
    tagged = _extract_tag_blocks(text)
    consumed_ranges = [(p["start_line"], p["end_line"]) for p in tagged]

    # 2) headings-based extraction for remaining regions
    heading_parts = _extract_heading_sections(text, consumed_ranges)

    return tagged + heading_parts


def _extract_tag_blocks(text: str) -> List[Part]:
    lines = text.splitlines()
    parts: List[Part] = []
    i = 0
    while i < len(lines):
        m = TAG_OPEN.search(lines[i])
        if not m:
            i += 1
            continue
        name = m.group("name").lower()
        start = i + 1
        # find close
        j = start
        while j < len(lines) and not TAG_CLOSE.search(lines[j]):
            j += 1
        content = "\n".join(lines[start:j]).strip()
        parts.append({
            "name": name,
            "content": content,
            "source": "tag",
            "start_line": start,
            "end_line": j,
        })
        i = j + 1
    return parts


def _extract_heading_sections(text: str, consumed: List[tuple[int, int]]) -> List[Part]:
    lines = text.splitlines()
    parts: List[Part] = []
    # find all headers and their ranges until next same/lower-level header
    headers: List[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        for name, pat in HEADER_PATTERNS.items():
            if pat.match(line):
                headers.append((idx, name))
                break
    headers.append((len(lines), "__eof__"))
    for k in range(len(headers) - 1):
        start_idx, name = headers[k]
        end_idx, _ = headers[k + 1]
        body_start = start_idx + 1
        body = "\n".join(lines[body_start:end_idx]).strip()
        if not body:
            continue
        # skip if overlaps consumed ranges
        if _overlaps((body_start, end_idx), consumed):
            continue
        parts.append({
            "name": name,
            "content": body,
            "source": "header",
            "start_line": body_start,
            "end_line": end_idx,
        })
    return parts


def _overlaps(a: tuple[int, int], ranges: List[tuple[int, int]]) -> bool:
    for b in ranges:
        if not (a[1] <= b[0] or a[0] >= b[1]):
            return True
    return False

