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


# --- Semantic Analysis using LLM ---

CLASSIFICATION_SCHEMA = """
1.  **정적 컨텍스트 (Static Context): 에이전트의 "DNA"**
    *   **1.1. 정체성 및 페르소나 (Identity & Persona):** 에이전트의 역할, 이름, 성격 등.
    *   **1.2. 핵심 임무 및 목표 (Core Mission & Goals):** 최상위 목표, 성공/평가 기준.
    *   **1.3. 운영 정책 및 가드레일 (Operational Policies & Guardrails):** 제약 조건, 안전/윤리 정책, 다른 에이전트와의 상호작용 규칙.

2.  **동적 컨텍스트 (Dynamic Context): 에이전트의 "작업 기억"**
    *   **2.1. 즉각적인 과제 및 입력 (Immediate Task & Input):** 현재 수행할 구체적인 작업, 사용자의 최근 메시지.
    *   **2.2. 상황 인식 및 기억 (Situational Awareness & Memory):** 대화/도구 사용 기록, 스크래치패드, 임시 변수.
    *   **2.3. 외부 지식 (External Knowledge - RAG):** RAG를 통해 검색된 문서, 외부 데이터.

3.  **출력 형식 및 생성 제어 (Output Formatting & Generation Control)**
    *   **3.1. 출력 스키마 (Output Schema):** 원하는 출력 형식(JSON, XML 등)에 대한 엄격한 정의.
    *   **3.2. 응답 가이드라인 (Response Guidelines):** 응답의 어조, 스타일, 언어, "모른다" 정책 등.
"""

PROMPT_TEMPLATE = f"""
당신은 LLM 컨텍스트 페이로드를 분석하는 전문가입니다.
주어진 페이로드의 각 부분을 아래 분류 스키마에 따라 분석하고, 어떤 카테고리에 속하는지 분류해주세요.
분석 결과는 반드시 JSON 배열 형식으로만 반환해야 합니다. 각 JSON 객체는 "category"와 "content" 키를 가져야 합니다.
스키마에 없는 내용으로 판단되면 "category"를 "기타 (Miscellaneous)"로 설정하세요.

---
[분류 스키마]
{CLASSIFICATION_SCHEMA}
---

---
[분석할 페이로드]
{{payload}}
---

[분석 결과 (JSON 형식)]
"""

def analyze_with_gemini(payload: str) -> List[Dict[str, Any]]:
    """Analyzes and classifies the payload using the Gemini API."""
    import os
    import json
    import google.generativeai as genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = PROMPT_TEMPLATE.format(payload=payload)
    response = model.generate_content(prompt)

    # Extract JSON part from the response text
    cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
    
    return json.loads(cleaned_response)

def analyze_with_custom_llm(payload: str, url: str, model_name: str) -> List[Dict[str, Any]]:
    """Analyzes the payload using a custom OpenAI-compatible endpoint."""
    import json
    import httpx

    prompt = PROMPT_TEMPLATE.format(payload=payload)
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(url, headers=headers, json=data)
        response.raise_for_status() # Raise an exception for bad status codes
        
        result = response.json()
        content_str = result['choices'][0]['message']['content']
        
        # The response content is expected to be a JSON string
        cleaned_response = content_str.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)

