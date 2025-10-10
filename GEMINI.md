# GEMINI.md: Visual Context Engineering Router (vcer)

## Project Overview

This project is a Python CLI tool named `vcer` (Visual Context Engineering Router). Its purpose is to analyze, visualize, optimize, and route prompts to local Large Language Model (LLM) backends such as vLLM and sglang. It is designed to bring structure and engineering principles to the process of prompt design and execution.

The core idea is to break down a prompt into distinct "parts" (e.g., task, constraints, output format, few-shot examples). `vcer` can then analyze these parts, visualize their relationships, optimize their order and content for better performance, and finally route the engineered prompt to a specified LLM backend.

The project is managed with `uv` for dependency and environment management. The main logic is written in Python, utilizing libraries like `typer` for the CLI, `pydantic` for data validation, and `httpx` for making requests to LLM backends.

## Building and Running

### Setup

1.  **Create a virtual environment:**
    ```bash
    uv venv
    ```
2.  **Install dependencies:**
    ```bash
    uv sync
    ```

### Core Commands

The main entry point for the tool is `vcer`. You can run it via `uv run`.

*   **Analyze a prompt:**
    ```bash
    uv run vcer analyze --in examples/system.md --user examples/user.md --out parts.json
    ```
*   **Visualize the prompt structure:**
    ```bash
    uv run vcer visualize --parts parts.json --format mermaid --out prompt.mmd
    ```
*   **Optimize the prompt:**
    ```bash
    uv run vcer optimize --parts parts.json --out system.opt.md
    ```
*   **Route the prompt to a backend:**
    ```bash
    uv run vcer route --backend <backend_id> --system examples/system.md --user examples/user.md --send
    ```
*   **Test with a local Ollama instance:**
    ```bash
    make test
    ```
    This is a shortcut for:
    ```bash
    make run http://localhost:11434/v1/chat/completions
    ```

## Development Conventions

*   **Testing:** The project uses `pytest` for unit and integration tests.
*   **Linting:** `ruff` is used for code linting and formatting.
*   **Configuration:** Project and backend configurations are managed through a `.vcer.yml` file. The `AGENT.md` file contains the detailed specification for this file and the project's overall design.
*   **Modularity:** The codebase is organized into distinct modules:
    *   `src/vcer/core`: Core logic for analysis and optimization.
    *   `src/vcer/adapters`: Connectors for different LLM backends.
    *   `src/vcer/visualize`: Code for generating visualizations.
    *   `src/vcer/config`: Configuration loading.
    *   `src/vcer/cli.py`: The command-line interface definition.
