"""DevFlow backend server — FastAPI app that the VS Code extension talks to."""

from __future__ import annotations

import os
from pathlib import Path
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .providers import get_provider
from .ai import get_engine
from .analyzer.codebase_scanner import CodebaseScanner
from .runbook.generator import RunbookGenerator
from .export.markdown_export import MarkdownExporter
from .export.pr_description import PRDescriptionGenerator
from .storage.session_store import SessionStore
from .utils.text_helpers import extract_keywords

app = FastAPI(title="DevFlow", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage lives in the workspace or user data directory
_default_store = Path(__file__).resolve().parent.parent / ".devflow" / "store.json"
_store_path = os.environ.get(
    "DEVFLOW_STORAGE",
    str(_default_store),
)
store = SessionStore(_store_path)


# --- Request/Response models ---

class ProviderConfig(BaseModel):
    provider: str  # jira | azure | github

    # Jira
    jira_url: str | None = None
    jira_email: str | None = None
    jira_token: str | None = None

    # Azure DevOps
    azure_org_url: str | None = None
    azure_project: str | None = None
    azure_pat: str | None = None

    # GitHub
    github_token: str | None = None
    github_owner: str | None = None
    github_repo: str | None = None


class AIConfig(BaseModel):
    ai_provider: str = "ollama"  # openai | anthropic | ollama | gemini
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    ollama_model: str = "llama3.1"
    ollama_host: str = "http://127.0.0.1:11434"


class FetchRequest(BaseModel):
    ticket_id: str
    provider_config: ProviderConfig
    ai_config: AIConfig = AIConfig()
    workspace_path: str | None = None  # for codebase scanning


class StepUpdate(BaseModel):
    ticket_id: str
    steps: list[dict]


class CompletionRequest(BaseModel):
    ticket_id: str
    title: str
    total_time: float
    steps_count: int


class PRRequest(BaseModel):
    ticket_id: str
    ticket_title: str
    ticket_type: str = "Task"
    steps: list[dict]
    ai_config: AIConfig = AIConfig()


# --- Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/ollama/models")
async def get_ollama_models(host: str = "http://127.0.0.1:11434"):
    """Check if local Ollama is online and return installed models."""
    hosts = [host, "http://127.0.0.1:11434", "http://localhost:11434"]
    for target in dict.fromkeys(hosts):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{target.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {"online": True, "models": models}
        except Exception:
            continue
    return {"online": False, "models": []}


@app.post("/ticket/fetch")
async def fetch_ticket(req: FetchRequest):
    """Fetch a ticket and generate its runbook."""
    try:
        # 1. Get ticket from provider
        provider = get_provider(req.provider_config.model_dump())
        ticket = await provider.fetch_ticket(req.ticket_id)

        # 2. Check for saved runbook
        saved = store.load_runbook(req.ticket_id)
        if saved and "steps" in saved:
            return {
                "ticket": {
                    "id": ticket.id, "provider": ticket.provider,
                    "title": ticket.title, "type": ticket.ticket_type,
                    "status": ticket.status, "points": ticket.story_points,
                    "assignedTo": ticket.assigned_to, "url": ticket.url,
                },
                "steps": saved["steps"],
                "restored": True,
            }

        # 3. Scan codebase if workspace path provided
        codebase = None
        if req.workspace_path and os.path.isdir(req.workspace_path):
            keywords = extract_keywords(ticket.full_text)
            scanner = CodebaseScanner(req.workspace_path)
            codebase = scanner.scan(ticket_keywords=keywords)

        # 4. Generate runbook
        try:
            engine = get_engine(req.ai_config.model_dump())
            generator = RunbookGenerator(ai_engine=engine)
        except Exception:
            generator = RunbookGenerator()  # no AI, fallback only

        runbook = await generator.generate(ticket, codebase)

        # 5. Save and return
        store.save_runbook(req.ticket_id, runbook.to_dict())

        return {
            "ticket": {
                "id": ticket.id, "provider": ticket.provider,
                "title": ticket.title, "type": ticket.ticket_type,
                "status": ticket.status, "points": ticket.story_points,
                "assignedTo": ticket.assigned_to, "url": ticket.url,
            },
            "steps": [s.to_dict() for s in runbook.steps],
            "aiProvider": runbook.ai_provider,
            "codebaseAware": runbook.codebase_aware,
            "restored": False,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ticket/save")
async def save_steps(req: StepUpdate):
    """Save step progress."""
    store.save_runbook(req.ticket_id, {"steps": req.steps})
    return {"saved": True}


@app.post("/ticket/complete")
async def complete_ticket(req: CompletionRequest):
    """Record ticket completion."""
    records = store.record_completion(
        req.ticket_id, req.title, req.total_time, req.steps_count,
    )
    return {"records": records}


@app.post("/export/markdown")
async def export_markdown(req: StepUpdate):
    """Export runbook as Markdown."""
    from .runbook.models import Runbook, Step

    steps = [Step(id=s["id"], title=s["title"], is_completed=s.get("isCompleted", False),
                  time_spent_seconds=s.get("timeSpentSeconds", 0),
                  is_git_step=s.get("isGitStep", False))
             for s in req.steps]
    runbook = Runbook(ticket_id=req.ticket_id, ticket_title="", steps=steps)
    md = MarkdownExporter.export(runbook)
    return {"markdown": md}


@app.post("/export/pr")
async def generate_pr(req: PRRequest):
    """Generate AI-powered PR description."""
    from .runbook.models import Runbook, Step

    steps = [Step(id=s["id"], title=s["title"], is_completed=s.get("isCompleted", False),
                  is_git_step=s.get("isGitStep", False))
             for s in req.steps]
    runbook = Runbook(ticket_id=req.ticket_id, ticket_title=req.ticket_title, steps=steps)

    try:
        engine = get_engine(req.ai_config.model_dump())
        generator = PRDescriptionGenerator(ai_engine=engine)
    except Exception:
        generator = PRDescriptionGenerator()

    pr_text = await generator.generate(runbook, req.ticket_type)
    return {"description": pr_text}


@app.post("/provider/validate")
async def validate_provider(config: ProviderConfig):
    """Test if provider credentials work."""
    try:
        provider = get_provider(config.model_dump())
        ok = await provider.validate_connection()
        return {"valid": ok}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@app.post("/ai/validate")
async def validate_ai(config: AIConfig):
    """Test if the configured AI engine is reachable."""
    try:
        engine = get_engine(config.model_dump())
        ok = await engine.is_available()
        return {"valid": ok, "engine": engine.name}
    except Exception as e:
        return {"valid": False, "error": str(e)}


@app.get("/records")
async def get_records():
    """Get completion records and stats."""
    return store.get_records()


@app.post("/clear")
async def clear_all():
    """Clear all stored data."""
    store.clear_all()
    return {"cleared": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("DEVFLOW_HOST", "127.0.0.1"),
        port=int(os.environ.get("DEVFLOW_PORT", "9120")),
    )
