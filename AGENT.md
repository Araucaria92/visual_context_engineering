# Visual Context Engineering Router (VCER)

사용자 프롬프트와 로컬 LLM(vLLM, sglang 등) 사이에서 “컨텍스트 엔지니어링”을 지원하는 라우터/도구입니다. 시스템 프롬프트를 파트별로 분석(예: task, description, few-shot, output format 등), 시각화하고, 경험적/규칙 기반 최적 순서를 제안하며, 필요 시 재배치 및 최적화한 뒤 로컬 모델로 라우팅합니다.

## 핵심 목표
- 정확한 파트 추출: 시스템/유저 프롬프트를 파트 단위로 구조화.
- 시각화: 파트 간 계층과 순서를 직관적으로 확인(머메이드/HTML 등).
- 최적 순서 제안: 안전성·명확성·출력 일관성을 높이는 정렬 규칙 제공.
- 라우팅: vLLM/sglang 등 로컬 백엔드로 요청 전달, 결과 수집/로그.
- 반복 최적화: 결과 기반으로 재배치/가중치 변경 및 버전 관리.

## 파트 정의(권장 스키마)
- Task: 모델이 수행해야 할 일의 핵심 지시.
- Description(Background): 문제 맥락/배경/도메인 제약.
- Constraints: 금지/필수 조건, 안전/정확성 요구사항.
- Tools/Resources: 사용 가능한 도구, 외부 리소스, 함수 서명 등.
- Few-Shot Examples: 입력/출력 예시 쌍 또는 부분 예시.
- Output Format(Schema): 출력 구조, 키/타입, 포맷(JSON/Markdown 등).
- Evaluation Criteria: 정답성/형식/스타일 채점 기준, 셀프체크 규칙.
- Guardrails/Policy: 민감정보/안전/윤리 가드레일, 금지 항목.
- Metadata: 대상 사용자/톤/언어/길이/온도 범위 등 메타 파라미터.
- Retrieval/Context: 추가 문서/지식 컨텍스트(선택), 인용 규칙.

## 파트 표기 규약(권장)
다음 중 하나를 일관되게 사용하세요.
- Markdown 헤더: `## Task`, `## Constraints`, `## Output Format` 등.
- 태그 블록: `[part:task] ... [/part]`, `[part:few_shot] ... [/part]`.
- YAML 프론트매터(메타데이터):
  ```yaml
  ---
  language: ko
  audience: developers
  style: concise
  ---
  ```

## 권장 정렬(Heuristic Ordering)
1) Title/Role → 2) Task → 3) Constraints → 4) Tools/Resources → 5) Output Format → 6) Few-Shot Examples → 7) Evaluation Criteria → 8) Guardrails/Policy → 9) Metadata → 10) Retrieval/Context

- 이유: 지시(Task)와 제약을 먼저 고정해 모델 행동공간을 좁히고, 도구/출력 형식을 명시해 일관성과 채점 용이성을 확보. 예시는 과적합/편향을 줄이기 위해 형식 뒤에 배치. 가드레일·메타·추가 컨텍스트는 필요 시 후행.

## 명령줄(초안)
- `vcer analyze --in system.md [--user user.md] [--lang ko|en] --out parts.json`
  - 시스템/유저 프롬프트에서 파트를 탐지해 JSON으로 출력.
- `vcer visualize --parts parts.json --format mermaid|html --out prompt.svg`
  - 파트 구조/순서 시각화(머메이드 다이어그램/HTML 의사 UI).
- `vcer optimize --parts parts.json --strategy heuristic|llm --out system.opt.md [--weights config]`
  - 규칙/모델 보조로 파트 순서·문구 최적화.
- `vcer route --backend vllm|sglang --endpoint http://localhost:8000 --model <name> --system system.md --user user.md [--stream] [--max-tokens 1024]`
  - 로컬 백엔드로 추론 요청. 스트리밍/토큰 제한 선택.
- `vcer dry-run --system system.md --user user.md`
  - 실제 호출 없이 파이프라인 점검.
- `vcer serve --port 3999`
  - 간단한 HTTP API 제공(`/analyze`, `/optimize`, `/route`).

## 설정 파일(.vcer.yml) 스펙
```yaml
version: 0.1
language: ko

backends:
  - id: local-vllm
    kind: vllm
    base_url: http://localhost:8000
    model: Qwen2-7B-Instruct
    timeout_ms: 60000
    headers: {}
  - id: local-sglang
    kind: sglang
    base_url: http://localhost:30000
    model: Llama-3-8B-Instruct
    timeout_ms: 60000

router:
  strategy: round_robin   # round_robin|latency|weighted|canary
  health_check_interval_ms: 5000
  weights:
    local-vllm: 1.0
    local-sglang: 1.0

analyze:
  detectors:
    headers:
      task: ["^##\\s*Task$", "^###\\s*Task$"]
      constraints: ["^##\\s*Constraints$", "^###\\s*Constraints$"]
      output_format: ["^##\\s*Output\\s*Format$"]
      few_shot: ["^##\\s*(Few[- ]?Shot|Examples)$"]
    tags:
      open: "\\[part:(?P<name>[a-z_]+)\\]"
      close: "\\[/part\\]"
  merge_adjacent: true
  tolerate_overlap: false

optimize:
  order: [title, task, constraints, tools, output_format, few_shot, evaluation, guardrails, metadata, retrieval]
  weights:
    task_specificity: 0.4
    constraint_clarity: 0.25
    format_strictness: 0.2
    example_relevance: 0.15
  rewrite:
    preserve_style: true
    max_diff_ratio: 0.25   # 25% 이내로만 문구 변경

visualize:
  theme: dark
  mermaid:
    direction: LR  # LR|TB
    wrap: 60

limits:
  max_context_tokens: 120000
  max_examples: 8
```

## 백엔드 어댑터(요청/응답 형식)
- vLLM(OpenAI 호환): `POST /v1/chat/completions` 형태 권장. `model`, `messages`, `temperature`, `max_tokens`, `stream` 지원.
- sglang: `POST /generate` 또는 환경에 맞는 엔드포인트. 파라미터 키를 어댑터에서 매핑.
- 공통: 요청/응답은 내부 표준 스키마로 변환해 라우팅/로그 일관성 확보.

## 시각화 산출물
- Mermaid: 파트 노드와 간선으로 순서·의존성 표현, `prompt.mmd`/`prompt.svg`.
- HTML 요약: 섹션 카드 UI, 재배치 드래그&드롭(향후) 스펙 고려.

## 품질/안전 가드
- 금지/필수 제약을 상단에 고정하는 정렬 규칙.
- 출력 스키마 엄수(최소 JSON 유효성 체크 옵션 제공).
- 민감정보/안전 정책 섹션 자동 탐지 및 강조.
- 토큰 초과 대비: 섹션별 축약/우선순위 기반 트리밍.

## 파일 구조(예정)
```
/cli            # Typer/Click 기반 CLI
/core           # 파트 탐지, 정렬, 최적화 로직
/adapters       # vllm/sglang 등 백엔드 어댑터
/visualize      # mermaid/html 렌더러
/tests          # 단위 테스트
AGENT.md        # 이 문서
.vcer.yml       # 기본 설정(프로젝트 루트)
```

## 초기 구현 언어/라이브러리 제안
- Python 3.10+: `typer`(CLI), `pydantic`(스키마), `httpx`(HTTP), `rich`(출력), `jinja2`(템플릿), `ruamel.yaml`(설정).

## 사용 워크플로(예시)
1) 시스템/유저 프롬프트 작성(권장 표기 규약 사용).
2) `vcer analyze`로 JSON 파트 추출.
3) `vcer visualize`로 구조 확인, 필요 시 수동 수정.
4) `vcer optimize`로 순서/문구 최적화.
5) `vcer route`로 로컬 LLM에 요청, 결과 검토.
6) 결과 기반 재배치/가중치 조정, 버전 관리.

## 다음 단계
- CLI 스캐폴딩(`vcer analyze/visualize/optimize/route` 골격) 추가.
- `.vcer.yml` 기본 템플릿 생성 및 로드 로직.
- vLLM/sglang 어댑터 초안 구현.
- Mermaid/HTML 시각화 초안 구현.

---
본 문서는 프로그램 옵션/구조/설정의 기준점입니다. 실제 구현 시 본 스펙을 준수하되, 현장 요구에 따라 최소 변경으로 진화시키는 것을 권장합니다.

