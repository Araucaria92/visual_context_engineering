from __future__ import annotations

from typing import Any, Dict, List


def parts_to_mermaid(data: dict) -> str:
    parts = data.get("parts", [])
    if not parts:
        return "graph TD;\n    A(No parts found);"

    mmd = "graph TD;\n"
    for i, part in enumerate(parts):
        name = part.get("name", f"Part {i+1}")
        content_preview = part.get("content", "").strip()[:50].replace("\"", "#quot;")
        mmd += f'    {i}("**{name}**<br/>{content_preview}...");\n'
    return mmd


def semantic_parts_to_mermaid(classified_data: list[dict]) -> str:
    """Generates a Mermaid diagram from semantically classified data."""
    if not classified_data:
        return "graph TD;\n    A(No classified data found);"

    mermaid_string = "graph TD;\n"
    mermaid_string += "    A(LLM Payload) --> B{Static Context};\n"
    mermaid_string += "    A --> C{Dynamic Context};\n"
    mermaid_string += "    A --> D{Output Control};\n\n"

    node_counter = 0
    for item in classified_data:
        category = item.get("category", "기타").replace('"', "'")
        content = item.get("content", " ").strip().replace('"', "'")
        
        # Create node name
        node_id = f"N{node_counter}"
        node_counter += 1
        
        # Escape node text
        node_text = f'"{node_id}[\\"{category}\\"\\<br/>---\\<br/>{content[:80]}..."'
        
        if category.startswith("1."):
            mermaid_string += f"    B --> {node_text};\n"
        elif category.startswith("2."):
            mermaid_string += f"    C --> {node_text};\n"
        elif category.startswith("3."):
            mermaid_string += f"    D --> {node_text};\n"
        else:
             mermaid_string += f"    A --> {node_text};\n"
    
    return mermaid_string

