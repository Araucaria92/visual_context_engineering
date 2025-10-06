from __future__ import annotations

from typing import Any, Dict


def load_backend(cfg: Dict[str, Any], backend: str) -> Dict[str, Any]:
    # find by id first
    for be in cfg.get("backends", []):
        if be.get("id") == backend:
            return _normalize_backend(be)
    # else find first by kind
    for be in cfg.get("backends", []):
        if be.get("kind") == backend:
            return _normalize_backend(be)
    # default vllm style if nothing found
    return {
        "kind": "vllm",
        "url": "http://localhost:8000/v1/chat/completions",
        "model": "local-model",
        "timeout": 60.0,
    }


def _normalize_backend(be: Dict[str, Any]) -> Dict[str, Any]:
    kind = be.get("kind", "vllm")
    base = be.get("base_url", "http://localhost:8000")
    url = base
    if kind in ("vllm", "openai"):
        url = base.rstrip("/") + "/v1/chat/completions"
    elif kind == "sglang":
        # heuristic endpoint; adjust per your deployment
        url = base.rstrip("/") + "/generate"
    elif kind == "ollama":
        # Ollama chat endpoint
        url = base.rstrip("/") + "/api/chat"
    return {
        "kind": kind,
        "url": url,
        "model": be.get("model", "local-model"),
        "timeout": float(be.get("timeout_ms", 60000)) / 1000.0,
        "headers": be.get("headers", {}),
    }


def build_request(
    *,
    system: str,
    user: str,
    backend: Dict[str, Any],
    stream: bool = False,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    kind = backend.get("kind")
    if kind in ("vllm", "openai"):
        return _build_openai_chat_completions(system, user, backend, stream, max_tokens)
    if kind == "sglang":
        return _build_sglang_generate(system, user, backend, stream, max_tokens)
    if kind == "ollama":
        return _build_ollama_chat(system, user, backend, stream, max_tokens)
    # fallback OpenAI style
    return _build_openai_chat_completions(system, user, backend, stream, max_tokens)


def _build_openai_chat_completions(system: str, user: str, backend: Dict[str, Any], stream: bool, max_tokens: int) -> Dict[str, Any]:
    return {
        "model": backend.get("model"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": stream,
        "max_tokens": max_tokens,
    }


def _build_sglang_generate(system: str, user: str, backend: Dict[str, Any], stream: bool, max_tokens: int) -> Dict[str, Any]:
    prompt = system + "\n\n" + user
    return {
        "model": backend.get("model"),
        "prompt": prompt,
        "stream": stream,
        "max_new_tokens": max_tokens,
    }


def _build_ollama_chat(system: str, user: str, backend: Dict[str, Any], stream: bool, max_tokens: int) -> Dict[str, Any]:
    # Ollama chat API
    return {
        "model": backend.get("model"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": stream,
        "options": {
            "num_predict": max_tokens,
        },
    }
