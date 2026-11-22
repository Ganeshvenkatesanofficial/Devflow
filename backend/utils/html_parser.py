"""HTML to plain text conversion for ticket descriptions."""

from __future__ import annotations

import re
from typing import Any


def html_to_text(content: Any) -> str:
    """Convert HTML or Atlassian Document Format to plain text."""
    if not content:
        return ""

    # Atlassian Document Format (ADF) — used by Jira Cloud
    if isinstance(content, dict):
        return _extract_atlassian_doc(content)

    if not isinstance(content, str):
        return str(content)

    # HTML cleanup
    text = content
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')

    # Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _extract_atlassian_doc(doc: dict) -> str:
    """Walk an Atlassian Document Format tree and extract text."""
    if not doc or "content" not in doc:
        return ""

    lines: list[str] = []

    def walk(nodes: list[dict]) -> None:
        for node in nodes or []:
            node_type = node.get("type", "")

            if node_type == "text":
                lines.append(node.get("text", ""))
            elif node_type == "hardBreak":
                lines.append("\n")
            elif node_type == "paragraph":
                walk(node.get("content", []))
                lines.append("\n")
            elif node_type == "listItem":
                lines.append("• ")
                walk(node.get("content", []))
            elif "content" in node:
                walk(node["content"])

    walk(doc["content"])
    return re.sub(r"\n{3,}", "\n\n", "".join(lines)).strip()
