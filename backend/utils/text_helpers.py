"""Text utility functions."""

from __future__ import annotations

import re


def slugify(text: str) -> str:
    """Convert text to a URL/branch-friendly slug."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from ticket text for codebase search."""
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "and",
        "but", "or", "not", "no", "so", "if", "then", "than",
        "that", "this", "these", "those", "it", "its", "i", "we",
        "you", "they", "he", "she", "user", "should", "must",
        "want", "need", "able",
    }

    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [w for w in words if w not in stop_words]
