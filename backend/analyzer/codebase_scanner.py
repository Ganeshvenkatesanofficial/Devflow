"""Scans the workspace to give AI context about the actual codebase."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# Directories to skip during scanning
IGNORE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".idea",
    ".vscode", "vendor", "target", "bin", "obj",
}

# Framework detection patterns
FRAMEWORK_SIGNATURES = {
    "react": ["package.json:react", "src/App.jsx", "src/App.tsx"],
    "nextjs": ["next.config.js", "next.config.ts", "pages/", "app/"],
    "vue": ["package.json:vue", "src/App.vue"],
    "angular": ["angular.json", "src/app/app.module.ts"],
    "django": ["manage.py", "settings.py", "urls.py"],
    "flask": ["app.py:Flask", "wsgi.py"],
    "fastapi": ["main.py:FastAPI", "app.py:FastAPI"],
    "spring-boot": ["pom.xml:spring-boot", "build.gradle:spring-boot"],
    "express": ["package.json:express", "app.js:express"],
    "rails": ["Gemfile:rails", "config/routes.rb"],
    "dotnet": ["*.csproj", "Program.cs", "Startup.cs"],
}


@dataclass
class CodebaseContext:
    """What we know about the developer's project."""

    root_path: str
    frameworks: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)  # language -> file count
    file_tree: list[str] = field(default_factory=list)  # top-level structure
    relevant_files: list[str] = field(default_factory=list)  # files matching ticket keywords
    sample_patterns: list[str] = field(default_factory=list)  # existing code patterns

    def to_prompt_context(self) -> str:
        """Format codebase info for inclusion in AI prompts."""
        parts = [f"Project root: {self.root_path}"]

        if self.frameworks:
            parts.append(f"Frameworks: {', '.join(self.frameworks)}")

        if self.languages:
            lang_summary = ", ".join(
                f"{lang} ({count} files)" for lang, count in
                sorted(self.languages.items(), key=lambda x: -x[1])[:5]
            )
            parts.append(f"Languages: {lang_summary}")

        if self.file_tree:
            parts.append("Project structure:\n" + "\n".join(f"  {f}" for f in self.file_tree[:30]))

        if self.relevant_files:
            parts.append("Possibly relevant files:\n" + "\n".join(f"  {f}" for f in self.relevant_files[:15]))

        if self.sample_patterns:
            parts.append("Existing code patterns:\n" + "\n".join(self.sample_patterns[:5]))

        return "\n\n".join(parts)


class CodebaseScanner:
    """Scans a project directory and extracts context for AI prompts."""

    # Map extensions to language names
    LANG_MAP = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript (React)", ".jsx": "JavaScript (React)",
        ".java": "Java", ".kt": "Kotlin", ".cs": "C#",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
        ".php": "PHP", ".swift": "Swift", ".dart": "Dart",
        ".vue": "Vue", ".svelte": "Svelte",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    }

    def __init__(self, workspace_path: str):
        self._root = Path(workspace_path)

    def scan(self, ticket_keywords: list[str] | None = None) -> CodebaseContext:
        """Perform a full scan of the workspace."""
        ctx = CodebaseContext(root_path=str(self._root))

        ctx.file_tree = self._get_file_tree()
        ctx.languages = self._detect_languages()
        ctx.frameworks = self._detect_frameworks()

        if ticket_keywords:
            ctx.relevant_files = self._find_relevant_files(ticket_keywords)

        return ctx

    def _get_file_tree(self, max_depth: int = 3) -> list[str]:
        """Get the directory structure up to max_depth levels."""
        tree = []
        for root, dirs, files in os.walk(self._root):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            depth = str(root).replace(str(self._root), "").count(os.sep)
            if depth >= max_depth:
                dirs.clear()
                continue

            rel = os.path.relpath(root, self._root)
            indent = "  " * depth
            if rel != ".":
                tree.append(f"{indent}{rel}/")

            for f in sorted(files)[:10]:  # limit files per directory
                tree.append(f"{indent}  {f}")

        return tree[:50]  # cap total lines

    def _detect_languages(self) -> dict[str, int]:
        """Count files by programming language."""
        counts: dict[str, int] = {}
        for root, dirs, files in os.walk(self._root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                ext = Path(f).suffix.lower()
                lang = self.LANG_MAP.get(ext)
                if lang:
                    counts[lang] = counts.get(lang, 0) + 1
        return counts

    def _detect_frameworks(self) -> list[str]:
        """Detect which frameworks the project uses."""
        detected = []
        for framework, signatures in FRAMEWORK_SIGNATURES.items():
            for sig in signatures:
                if ":" in sig:
                    # Check file content for keyword
                    filename, keyword = sig.split(":", 1)
                    filepath = self._root / filename
                    if filepath.exists():
                        try:
                            content = filepath.read_text(errors="ignore")[:5000]
                            if keyword in content:
                                detected.append(framework)
                                break
                        except Exception:
                            continue
                else:
                    # Check if file/dir exists
                    if (self._root / sig).exists():
                        detected.append(framework)
                        break
        return detected

    def _find_relevant_files(self, keywords: list[str]) -> list[str]:
        """Find files whose names or content match ticket keywords."""
        matches = []
        lower_keywords = [k.lower() for k in keywords if len(k) > 2]

        for root, dirs, files in os.walk(self._root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                f_lower = f.lower()
                # Check filename
                if any(kw in f_lower for kw in lower_keywords):
                    rel = os.path.relpath(os.path.join(root, f), self._root)
                    matches.append(rel)

        return sorted(set(matches))[:15]
