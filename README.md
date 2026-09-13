# Continuo

<div align="center">

<img src="assets/logo.webp" alt="Continuo Logo" width="96" height="96" />

### Keep your context. Continue anywhere.

**An AI context continuity browser extension and persistent project memory layer.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![Chrome MV3](https://img.shields.io/badge/Extension-Chrome%20MV3-4285F4.svg)](https://developer.chrome.com/docs/extensions/mv3/)
[![License](https://img.shields.io/badge/License-Apache%202.0-black.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen.svg)](tests/)

</div>

---

## 1. What Continuo Does

Modern engineering work is fragmented across multiple AI systems:
- You brainstorm and architect in **ChatGPT**.
- You hit limits or need nuanced refactoring, so you switch to **Claude**.
- You need deep documentation search and reasoning in **Gemini**.
- You move to an editor agent like **Cursor**.

Every time you switch models, your context fractures. You spend 30–60 minutes copying outdated notes, re-explaining architectural constraints, and risking critical hallucinated drift.

**Continuo turns your context into a persistent, portable project memory.**

Instead of managing an overwhelming dashboard, Continuo is an **extension-first companion utility**:
1. You work naturally in ChatGPT, Claude, or Gemini.
2. When you reach a stopping point, click the Continuo Chrome Extension.
3. Continuo detects the AI conversation, extracts technical decisions, goals, and constraints, and saves it to **Project Memory**.
4. Click **Continue with Claude** (or ChatGPT/Gemini). Continuo copies a clean continuation prompt to your clipboard and opens the destination AI.
5. You paste and continue immediately—no re-explaining required.

```
User works in ChatGPT
        ↓
Reaches stopping point
        ↓
Clicks Continuo extension
        ↓
Continuo understands project context
        ↓
User clicks "Save Context"
        ↓
Context stored as Project Memory
        ↓
User chooses another AI (e.g. Claude)
        ↓
Continuo generates structured handoff & copies to clipboard
        ↓
Claude opens, user pastes, and continues working
```

---

## 2. Production Architecture

Continuo maintains a strict separation of concerns, ensuring provider neutrality and data isolation:

```
                    ┌───────────────┐
                    │     USER      │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
          CONTINUO WEBSITE      CHROME EXTENSION
          (Project Memory UI)    (1-Click Companion)
                 │                     │
                 └──────────┬──────────┘
                            ▼
                     FASTAPI GATEWAY
                     (REST API v1)
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
           AUTH SERVICE  CONTEXT     PROJECT
           (JWT / Hash)   ENGINE      MEMORY
                            │           │
                            └─────┬─────┘
                                  ▼
                              DATABASE
                         (SQLite / Postgres)
                                  │
                                  ▼
                             AI HANDOFF
                       (Universal Markdown)
```

---

## 3. Key Features

- **Extension-First Experience**: 6 deterministic popup states (`NO_AI_DETECTED`, `AI_DETECTED`, `CAPTURING`, `PROCESSING`, `SUCCESS`, `ERROR`).
- **Live Active Tab Scraping**: Safely extracts message turns directly from the DOM on `chatgpt.com`, `claude.ai`, and `gemini.google.com`.
- **Inline Project Creation**: Create and associate new projects directly in the popup with zero context switching.
- **Universal Markdown Handoffs**: Formats structured continuation packages using an explicit, AI-readable schema without brittle proprietary markup.
- **Strict User Isolation**: Every endpoint verifies JWT token identity against resource ownership; no user can access another user's projects, memory, versions, or handoffs.
- **Dynamic Quality Scorer**: Mathematical 0–100% evaluation measuring Completeness, Clarity, Actionability, and Contradiction risk.
- **Contradiction Guard**: Detects opposing architectural choices and incompatible constraints before they propagate to downstream models.
- **Granular Version Diffs**: Snapshot project memory versioning (`v1.0`, `v1.1`, `v1.2`) with visual additions, modifications, and removals.
- **Honest Handoff UX**: No fake automated keystroke injection—generates verified payload, copies directly to clipboard, and opens the destination AI with immediate visual feedback (`✓ Context copied. Ready to continue in Claude.`).

---

## 4. Project Structure

```
Continuo/
├── backend/
│   ├── config.py                 # Pydantic environment configuration & CORS origins
│   ├── database.py               # SQLAlchemy engine & session factory
│   ├── main.py                   # FastAPI application gateway & middleware
│   ├── models/                   # SQLAlchemy DB models (User, Project, ContextPackage, Versions, Handoffs)
│   ├── routers/
│   │   ├── auth.py               # /auth (register, login, logout, me)
│   │   ├── projects.py           # /projects (CRUD with ownership enforcement)
│   │   ├── context.py            # /context (capture, analyze, patch)
│   │   ├── versions.py           # /versions (history & semantic diff)
│   │   └── handoffs.py           # /handoffs (cross-model continuation generation)
│   ├── schemas/                  # Pydantic v2 validation models
│   └── services/
│       ├── auth.py               # PBKDF2 password hashing & JWT signing
│       ├── context_engine.py     # Deterministic heuristic extraction engine
│       ├── quality_scorer.py     # Weighted 4-factor quality algorithm
│       ├── contradiction.py      # Architectural decision conflict detector
│       ├── version_diff.py       # JSON memory diff calculator
│       └── handoff_generator.py  # Section 8 Universal Handoff Formatter
├── extension/
│   ├── manifest.json             # Chrome Manifest V3 configuration (minimal permissions)
│   ├── popup.html                # 6-state popup companion interface
│   ├── popup.css                 # Glassmorphic dark companion styling
│   ├── popup.js                  # Extension popup state machine & controller
│   └── content.js                # Content script extracting ChatGPT / Claude / Gemini DOM turns
├── assets/                       # Branding, emblems, and visual assets
├── index.html                    # Continuous landing page & Project Workspace UI
├── styles.css                    # Design tokens, glassmorphism, and responsive styling
├── main.js                       # Frontend workspace controller & ambient motion engine
├── tests/                        # Pytest automated test suite
├── .env.example                  # Environment configuration template
├── requirements.txt              # Python production dependencies
└── continuo.db                   # Local SQLite database (zero-setup development)
```

---

## 5. Local Development Setup

### Prerequisites
- Python 3.12 or newer
- Google Chrome (or Chromium-based browser: Brave, Edge)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Anxhu03/Continuo.git
cd Continuo
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Edit `.env` to configure your `SECRET_KEY`, `DATABASE_URL`, and `CORS_ORIGINS`.

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Or activate on macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Start the FastAPI development server:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8008 --reload
```
Interactive API documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8008/docs](http://127.0.0.1:8008/docs)
- **ReDoc**: [http://127.0.0.1:8008/redoc](http://127.0.0.1:8008/redoc)

### 4. Frontend Setup
In a separate terminal:
```bash
python -m http.server 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

### 5. Database Setup
- **Default (SQLite)**: Automatically initializes `continuo.db` in the repository root on startup with zero configuration.
- **Production (PostgreSQL / Supabase)**: Update your `DATABASE_URL` in `.env`:
  ```ini
  DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/[DATABASE]
  ```
  SQLAlchemy models will create and migrate all tables automatically on server initialization.

---

## 6. Chrome Extension Installation

Continuo operates as an unpacked Manifest V3 Chrome Extension during the developer preview:

1. Clone or download this repository to your local computer.
2. Open Google Chrome and enter `chrome://extensions` in the address bar.
3. Toggle the **Developer mode** switch in the top-right corner to **ON**.
4. Click the **Load unpacked** button in the top-left toolbar.
5. In the file dialog, select the `Continuo/extension` directory.
6. Continuo will appear in your extensions list. Click the puzzle icon in Chrome and **pin Continuo** to your toolbar.
7. Open **ChatGPT** (`chatgpt.com`), **Claude** (`claude.ai`), or **Google Gemini** (`gemini.google.com`).
8. Click the Continuo extension icon, select or create your project, and click **Save Context**.

---

## 7. Universal Handoff Prompt Schema

Continuo formats cross-AI continuation packages into a clean, universal Markdown schema that downstream models ingest without conversational confusion:

```markdown
# Continue this project

## Project
Nexora Autonomous Agent (v1.1)

## Goal
Build high-throughput context continuity layer across multiple AI models.

## Current state
Working context captured by Continuo and formatted for continuation.

## Important requirements
- Support Google and GitHub OAuth providers
- [Constraint] Never store plaintext secrets or refresh tokens in insecure cookies

## Decisions already made
- Selected FastAPI with SQLAlchemy and PyJWT for stateless verification
- Implemented Section 8 clean Markdown handoff schema

## Completed work
- Setup database migrations for refresh_tokens table
- Verified password hashing with PBKDF2

## Problems / unresolved issues
- [Do Not Repeat] Avoid asyncpg raw connection pool conflicts with sub-task loops

## Important files or code context
- `backend/routers/auth.py`
- `backend/services/context_engine.py`

## Next step
1. Connect frontend auth modal and verify cross-domain CORS tokens

## Instructions for continuing
You are continuing this project directly from the CURRENT STATE above.
Do not restart from scratch, do not ask the user to re-explain, and do not repeat completed work or failed attempts.
Acknowledge receipt and proceed directly with Next Step 1.
```

---

## 8. REST API Reference

All protected routes require an `Authorization: Bearer <token>` header.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Register a new user account |
| `POST` | `/api/v1/auth/login` | Public | Authenticate with email/password; returns JWT token |
| `POST` | `/api/v1/auth/logout` | Required | Invalidate user session |
| `GET` | `/api/v1/auth/me` | Required | Retrieve active user profile |
| `GET` | `/api/v1/projects` | Required | List all projects owned by the authenticated user |
| `POST` | `/api/v1/projects` | Required | Create a new project and initialize baseline memory (`v1.0`) |
| `GET` | `/api/v1/projects/{id}` | Required | Fetch project metadata (enforces ownership) |
| `PATCH` | `/api/v1/projects/{id}` | Required | Update project title or description |
| `POST` | `/api/v1/context/capture` | Required | Ingest raw dialogue, extract memory facts, bump version |
| `POST` | `/api/v1/context/analyze` | Public | Stateless context extraction and quality preview |
| `GET` | `/api/v1/context/projects/{id}/context` | Required | Retrieve active or versioned project context |
| `PATCH` | `/api/v1/context/{id}` | Required | Manually curate project memory fields |
| `GET` | `/api/v1/versions/projects/{id}` | Required | List snapshot version history |
| `GET` | `/api/v1/versions/projects/{id}/diff` | Required | Calculate delta additions/modifications between two versions |
| `POST` | `/api/v1/handoffs` | Required | Generate cross-AI continuation package & destination URL |
| `GET` | `/api/v1/health` | Public | Backend connectivity & service status check |

---

## 9. Security & Privacy

- **User Isolation**: Protected endpoints verify `project.user_id == current_user.id`. Requests targeting foreign projects immediately return HTTP 403 Forbidden.
- **Zero Training Data Retention**: Captured context, conversation snippets, and project memories are never used to train or tune AI models.
- **Minimal Browser Permissions**: The Chrome Extension Manifest V3 requests only `activeTab`, `storage`, and `scripting`. Host permissions are restricted strictly to `chatgpt.com`, `claude.ai`, `gemini.google.com`, and the Continuo backend API. Broad permissions like `<all_urls>` are strictly avoided.
- **Explicit CORS Origins**: Configured via `CORS_ORIGINS` environment variable. Production disallows wildcard `*` for authenticated endpoints.

---

## 10. Automated Testing

Run the full pytest suite:
```bash
.\.venv\Scripts\python -m pytest -v
```

Test coverage includes:
- `tests/test_api_endpoints.py`: Registration, authentication, user resource isolation (403 verification), project creation, context capture, versioning diff, and handoffs.
- `tests/test_context_engine.py`: Structured fact extraction from raw conversational turns.
- `tests/test_quality_and_contradiction.py`: 4-dimension quality scoring and architectural contradiction detection.
- `tests/test_version_diff.py`: Multi-version context delta calculations.

---

## 11. Roadmap

- [x] Phase 1: High-fidelity visual polish & responsive landing page.
- [x] Phase 2: Context Engine heuristic extraction & quality scoring.
- [x] Phase 3: Project persistence, user authentication, and version diffing.
- [x] Phase 4: Extension-first productization, 6 popup states, universal Markdown handoffs.
- [ ] Phase 5: Chrome Web Store public listing.
- [ ] Phase 6: Hosted Supabase PostgreSQL migration & team workspace collaboration.

---

## 12. Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for local development guidelines, coding conventions, and pull request procedures.

---

## 13. License

Distributed under the **Apache License, Version 2.0**. See `LICENSE` for the complete license text.
