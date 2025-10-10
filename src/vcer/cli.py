from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config.loader import load_config
from .core.analyzer import analyze_files, analyze_payload_semantically
from .core.optimizer import optimize_parts, render_markdown
from .visualize.mermaid import parts_to_mermaid, semantic_parts_to_mermaid
from .visualize.terminal import visualize_semantic_parts_in_terminal
from .adapters.router import build_request, load_backend


app = typer.Typer(help="Visual Context Engineering Router (analyze, visualize, optimize, route)")
console = Console()


@app.command()
def analyze(
    in_: Path = typer.Option(..., "--in", help="System prompt file (Markdown)"),
    user: Optional[Path] = typer.Option(None, "--user", help="User prompt file (Markdown)"),
    out: Path = typer.Option(Path("parts.json"), help="Output parts JSON path"),
) -> None:
    """Analyze prompt files and extract parts to JSON."""
    cfg = load_config(Path.cwd())
    results = analyze_files(in_, user, cfg)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"Wrote parts → {out}")


@app.command("analyze-semantic")
def analyze_semantic(
    payload_file: Path = typer.Option(
        ...,
        "--payload",
        "-p",
        help="Path to the LLM payload text file to analyze.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_file: Path = typer.Option(
        "payload_diagram.mmd",
        "--out",
        "-o",
        help="Path to save the resulting Mermaid (.mmd) file.",
    ),
):
    """
    Analyzes an LLM payload semantically and visualizes it.
    """
    console.print(f"[cyan]Analyzing file '{payload_file}' semantically...[/cyan]")
    
    try:
        payload_content = payload_file.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[bold red]File read error: {e}[/bold red]")
        raise typer.Exit(code=1)

    try:
        # Analyze with LLM
        classified_data = analyze_payload_semantically(payload_content)

        # Visualize in terminal
        visualize_semantic_parts_in_terminal(classified_data, console)

        # Generate and save Mermaid diagram
        mermaid_diagram = semantic_parts_to_mermaid(classified_data)
        output_file.write_text(mermaid_diagram, encoding="utf-8")
        console.print(f"\n[bold green]Mermaid diagram saved to '{output_file}'[/bold green]")

    except Exception as e:
        console.print(f"[bold red]An error occurred during semantic analysis: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def visualize(
    parts: Path = typer.Option(..., "--parts", help="Parts JSON from analyze"),
    format: str = typer.Option("mermaid", "--format", help="Visualization format"),
    out: Path = typer.Option(Path("prompt.mmd"), help="Output file (.mmd/.svg)"),
) -> None:
    """Visualize parts structure and ordering."""
    data = json.loads(parts.read_text(encoding="utf-8"))
    if format.lower() != "mermaid":
        raise typer.BadParameter("Only 'mermaid' is supported in this scaffold")
    mmd = parts_to_mermaid(data)
    out.write_text(mmd, encoding="utf-8")
    console.print(f"Wrote mermaid diagram → {out}")


@app.command()
def optimize(
    parts: Path = typer.Option(..., "--parts", help="Parts JSON from analyze"),
    out: Path = typer.Option(Path("system.opt.md"), help="Optimized system prompt Markdown output"),
) -> None:
    """Reorder and lightly rewrite parts based on heuristics."""
    cfg = load_config(Path.cwd())
    data = json.loads(parts.read_text(encoding="utf-8"))
    opt = optimize_parts(data, cfg)
    md = render_markdown(opt)
    out.write_text(md, encoding="utf-8")
    console.print(f"Wrote optimized system prompt → {out}")


@app.command()
def route(
    system: Path = typer.Option(..., "--system", help="System prompt file (Markdown)"),
    user: Path = typer.Option(..., "--user", help="User prompt file (Markdown)"),
    backend: str = typer.Option("local-vllm", "--backend", help="Backend id or kind"),
    send: bool = typer.Option(False, "--send", help="Actually send request (otherwise dry-run)"),
    stream: bool = typer.Option(False, "--stream", help="Enable streaming if supported"),
    max_tokens: int = typer.Option(1024, "--max-tokens", help="Max tokens for generation"),
    endpoint: Optional[str] = typer.Option(None, "--endpoint", help="Override backend endpoint URL"),
    model: Optional[str] = typer.Option(None, "--model", help="Override model name"),
    header: Optional[list[str]] = typer.Option(None, "--header", help="Extra HTTP headers 'Key: Value'", rich_help_panel="HTTP"),
) -> None:
    """Build request for selected backend and optionally send it."""
    cfg = load_config(Path.cwd())
    be = load_backend(cfg, backend)
    # apply overrides
    if endpoint:
        be["url"] = endpoint
    if model:
        be["model"] = model
    if header:
        be.setdefault("headers", {})
        for h in header:
            if ":" not in h:
                raise typer.BadParameter(f"Invalid header format: {h}. Use 'Key: Value'")
            k, v = h.split(":", 1)
            be["headers"][k.strip()] = v.strip()
    req = build_request(
        system=system.read_text(encoding="utf-8"),
        user=user.read_text(encoding="utf-8"),
        backend=be,
        stream=stream,
        max_tokens=max_tokens,
    )
    if not send:
        console.print("[bold cyan]Dry-run request payload:[/bold cyan]")
        console.print_json(data=req)
        return
    # Optionally send using httpx; network may be restricted
    try:
        import httpx  # lazy import

        url = be["url"]
        headers = be.get("headers", {})
        with httpx.Client(timeout=be.get("timeout", 60.0)) as client:
            resp = client.post(url, headers=headers, json=req)
            resp.raise_for_status()
            console.print_json(data=resp.json())
    except Exception as e:
        console.print(f"[red]Failed to send request:[/red] {e}")


@app.command("dry-run")
def dry_run(
    system: Path = typer.Option(..., "--system"),
    user: Path = typer.Option(..., "--user"),
) -> None:
    """Preview the pipeline without sending requests."""
    console.print("System prompt preview:\n" + system.read_text(encoding="utf-8")[:600])
    console.print("\nUser prompt preview:\n" + user.read_text(encoding="utf-8")[:600])
