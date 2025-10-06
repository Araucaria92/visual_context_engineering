# VCER (Visual Context Engineering Router)

Windows-friendly Python CLI to analyze, visualize, optimize, and route prompts to local LLM backends (vLLM/sglang). Managed with `uv`.

## Quickstart (uv)
- Create env: `uv venv`
- Install deps: `uv sync`
- Run CLI: `uv run vcer --help`

## Windows (no make)
- Test routing to Ollama (default endpoint): `./scripts/test.ps1 -Send`
- Route to any endpoint: `./scripts/run.ps1 http://host:port/v1/chat/completions -Send`

If you prefer GNU Make on Windows, install one of:
- Git Bash/MSYS2 `make`
- Chocolatey: `choco install make`
- Scoop: `scoop install make`

## Core Commands
- `vcer analyze --in system.md [--user user.md] --out parts.json`
- `vcer visualize --parts parts.json --format mermaid --out prompt.mmd`
- `vcer optimize --parts parts.json --out system.opt.md`
- `vcer route --backend <id|kind> --system system.md --user user.md [--send]`
- `vcer dry-run --system system.md --user user.md`

See `AGENT.md` for full design and configuration.
