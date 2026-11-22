<div align="center">

<img src="media/icon-128.png" alt="DevFlow" width="96" height="96" />

# DevFlow

**Turn tickets into codebase-aware implementation runbooks — without leaving VS Code.**

[![VS Code](https://img.shields.io/badge/VS%20Code-%5E1.85-blue?logo=visualstudiocode)](https://marketplace.visualstudio.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

</div>

---

## The problem it solves

Every ticket starts the same loop:

1. Read the ticket on Jira / Azure DevOps / GitHub.
2. Switch to ChatGPT, paste the ticket, ask for a plan.
3. Switch to VS Code, look up which files the change touches.
4. Switch back, paste context into the AI, get a plan.
5. Switch back to VS Code, start coding.
6. Switch to a terminal for `git checkout -b …`.
7. Later: write the PR description by hand.

**DevFlow collapses all seven steps into one sidebar inside VS Code.** No tab-switching, no copy-paste, no re-explaining your repo to an AI every time.

---

## What it reduces

| Before DevFlow | With DevFlow |
|---|---|
| 4–6 tabs open per ticket (Jira, ChatGPT, docs, VS Code) | 1 — just VS Code |
| ~15–20 min to go from "ticket open" to "first commit" | ~2 min |
| AI plans that reference imaginary files | Plans grounded in **your actual repo** |
| Hand-written branch names and PR descriptions | Auto-generated, consistent, review-ready |
| Credentials pasted into chat windows | Stored locally in `.devflow/store.json`, never leaves your machine |

Nothing is sent anywhere unless you pick a cloud AI model. Choose **Ollama** and the whole workflow runs offline.

---

## Who it's for

- **Individual developers** who get handed Jira / ADO / GitHub tickets and want a faster start.
- **Team leads** who want their team to produce consistent branch names, PR templates and runbooks.
- **Agencies / consultancies** rotating across unfamiliar client codebases — DevFlow scans the repo so the AI isn't guessing.
- **Open-source maintainers** triaging GitHub issues — turn an issue into a plan without leaving the editor.
- **Students / juniors** learning a new codebase — the generated runbook is a readable map of where to start.

If you never read a ticket, DevFlow isn't for you. Anyone else: yes.

---

## The flow

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Paste ticket    │ -> │ Provider     │ -> │ Codebase     │ -> │ AI engine    │ -> │ Runbook +    │
│ URL in sidebar  │    │ fetch + auth │    │ scanner      │    │ (your choice)│    │ PR draft     │
│ (Jira/ADO/GH)   │    │              │    │ (your repo)  │    │              │    │              │
└─────────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
         1                   2                    3                   4                   5
```

**Step by step**

1. **You paste a ticket URL** into the DevFlow sidebar and hit *Generate*.
2. **The provider layer** (Jira / Azure DevOps / GitHub) fetches the ticket using credentials you entered once.
3. **The codebase scanner** walks the open workspace, detects languages and frameworks, and finds files whose names match the ticket's keywords.
4. **The AI engine** (OpenAI, Anthropic, Gemini, or local Ollama — you pick) receives *ticket + repo context* and returns a numbered implementation plan.
5. **DevFlow renders a runbook** with: setup branch command, AI-generated steps, test command, commit command, and a *Create PR* step that generates a PR description from the same context.

From there you can run any command in the integrated terminal with one click, copy steps to clipboard, or export the whole runbook to Markdown.

---

## Install

**From the VS Code Marketplace** (after publishing):
```
Search "DevFlow" → Install
```

**From source:**
```bash
git clone https://github.com/your-username/devflow
cd devflow
npm install
cd webview && npm install && npm run build && cd ..
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
```
Then press `F5` in VS Code to launch the Extension Development Host.

---

## Configuration

Every runtime value is a VS Code setting — nothing is hardcoded.

| Setting                    | Default       | Purpose                                      |
| -------------------------- | ------------- | -------------------------------------------- |
| `devflow.pythonPath`       | `python3`     | Python interpreter for the backend           |
| `devflow.backendHost`      | `127.0.0.1`   | Bind host for the local backend              |
| `devflow.backendPort`      | `9120`        | Bind port                                    |
| `devflow.startupTimeoutMs` | `10000`       | Max ms to wait for backend `/health`         |
| `devflow.logLevel`         | `warning`     | `debug` \| `info` \| `warning` \| `error`    |

Provider credentials (Jira / ADO / GitHub) and AI API keys are entered inside the panel and stored locally in `.devflow/store.json` under the extension's install directory. **They never leave your machine.**

---

## What each action does

### Sidebar panel actions

| Action | What happens when you click it |
|---|---|
| **Paste ticket URL + Generate** | Fetches the ticket from Jira / ADO / GitHub, scans the open workspace for files whose names match the ticket's keywords, sends ticket + repo context to your chosen AI engine, and renders a numbered implementation runbook in the sidebar. |
| **Validate provider** | Sends a single authenticated request to the provider's `/myself` or `/user` endpoint to confirm your API token works. No ticket is fetched. |
| **Validate AI** | Pings the configured AI engine (`openai`, `anthropic`, `gemini`, or local `ollama`) to confirm the key is accepted and the model is reachable. Returns `valid: true/false`. |
| **Run step command** (▶ next to any step) | Opens (or reuses) the integrated **DevFlow** terminal and runs that step's shell command — e.g. `git checkout -b feature/T-123-fix-login`. Nothing runs without your click. |
| **Copy step** | Puts the step's title + commands on your system clipboard. |
| **Mark step done** | Flags the step as complete locally; feeds into your streak and the "fastest ticket" record. |
| **Generate PR description** | Takes the runbook + ticket metadata and asks the AI to write a review-ready PR body (summary, test plan, screenshots-placeholder). |
| **Export runbook** | Opens VS Code's Save dialog and writes the full runbook (ticket, steps, commands, PR draft) as a single Markdown file. |
| **Complete ticket** | Records how long you spent on the ticket, updates your streak, rotates the "fastest ticket" trophy if applicable. |
| **Clear all data** | Wipes `.devflow/store.json` — configs, cached runbooks, records. Irreversible. |

### Command Palette commands (`Cmd/Ctrl+Shift+P`)

| Command | What it does |
|---|---|
| `DevFlow: Open Panel` | Reveals the DevFlow sidebar if it was hidden or minimized. |
| `DevFlow: Clear All Data` | Same as the *Clear all data* button in the panel — wipes the local store. |

### Status bar

| Item | What it does |
|---|---|
| `$(rocket) DevFlow` | Click to reveal the DevFlow sidebar (same as `DevFlow: Open Panel`). |

### Backend endpoints (for the curious — the webview calls these, you don't)

| Endpoint | What it does |
|---|---|
| `GET /health` | Returns `{status: "ok"}` — used by the extension to know the backend finished starting. |
| `GET /ollama/models` | Checks whether a local Ollama daemon is running and lists installed models. |
| `POST /provider/validate` | Tests Jira / ADO / GitHub credentials against the provider's identity endpoint. |
| `POST /ai/validate` | Tests the configured AI engine is reachable. |
| `POST /fetch` | The main action: provider fetch + repo scan + AI generation → runbook JSON. |
| `POST /pr/generate` | Returns an AI-written PR description for a given runbook. |
| `POST /export/markdown` | Renders a runbook as Markdown text. |
| `POST /ticket/complete` | Records completion time + updates stats. |
| `GET /records` | Returns your completion records and streak. |
| `POST /clear` | Wipes the local store. |

---

## Architecture

```
devflow/
├── extension/        # Thin VS Code shell (JavaScript)
│   └── src/
│       ├── extension.js        — activation entrypoint (DevFlowExtension class)
│       ├── config.js           — typed accessor over VS Code settings
│       ├── backend_manager.js  — spawns & monitors the Python process
│       ├── sidebar_provider.js — webview host + message bridge
│       └── commands.js         — all registered commands
├── backend/          # FastAPI + business logic (Python)
│   ├── server.py
│   ├── providers/   — Jira / Azure DevOps / GitHub ticket fetchers
│   ├── ai/          — OpenAI / Anthropic / Gemini / Ollama engines
│   ├── analyzer/    — repo scanner (languages, frameworks, keyword files)
│   ├── runbook/     — runbook generator
│   ├── export/      — Markdown + PR description writers
│   └── storage/     — local JSON store
├── webview/          # React UI (bundled to webview/build/)
└── media/            — brand assets (icon.svg, icon.png)
```

The extension side is intentionally thin: only VS Code APIs. Every piece of logic that could run outside VS Code lives in Python, so each layer can be swapped or extended cleanly.

---

## Deploying to the Marketplace

See [MARKETPLACE.md](./MARKETPLACE.md) for the full step-by-step publishing guide.

---

## License

MIT. See [LICENSE](./LICENSE).
