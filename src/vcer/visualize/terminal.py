
from __future__ import annotations

from typing import Any, List

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


def visualize_semantic_parts_in_terminal(classified_data: List[Dict[str, Any]], console: Console):
    """Visualizes the analyzed data in the terminal."""
    console.print("\n[bold green]--- LLM Payload Semantic Analysis Results ---[/bold green]\n")
    for item in classified_data:
        category = item.get("category", "N/A")
        content = item.get("content", "").strip()
        
        syntax = Syntax(content, "python", theme="monokai", line_numbers=True, word_wrap=True)
        
        panel = Panel(
            syntax,
            title=f"[bold yellow]{category}[/bold yellow]",
            border_style="cyan",
            expand=True
        )
        console.print(panel)

