# Continuo

<div align="center">

<img src="assets/logo.webp" alt="Continuo Logo" width="96" height="96" />

### Keep your context. Continue anywhere.

**An AI-agnostic context continuity and persistent project memory layer.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![Chrome MV3](https://img.shields.io/badge/Extension-Chrome%20MV3-4285F4.svg)](https://developer.chrome.com/docs/extensions/mv3/)
[![License](https://img.shields.io/badge/License-Apache%202.0-black.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen.svg)](tests/)

</div>

---

## 1. Executive Summary

When building modern software with AI models, developers spend hours establishing architecture, refining requirements, rejecting failed approaches, and shaping constraints.

However, hitting token limits, switching from ChatGPT to Claude, or moving to an IDE agent like Cursor causes immediate **context fracture**. The developer is forced to waste 30–60 minutes manually re-explaining the project, pasting outdated logs, and risking catastrophic architectural drift.

**Continuo is the universal context continuity bridge.**

It extracts a structured, deterministic **Context Package** from your conversation, eliminates conversational noise, calculates a real-time **Context Quality Score**, guards against architectural contradictions, and maintains a persistent, versioned **Project Memory**.

When you are ready to continue with another model, Continuo generates a tailored, model-optimized handoff payload with zero prompt hallucination.

```
       [ ChatGPT ]  ──►  [ Claude 3.7 ]  ──►  [ Cursor Agent ]
            │                  ▲                     ▲
            ▼                  │                     │
      ┌───────────────────────────────────────────────────┐
      │             CONTINUO CONTEXT ENGINE               │
      │   • Objective & Specs    • Locked Decisions       │
      │   • Hard Constraints     • Failed Attempts / Bugs │
      │   • Dynamic Quality      • Contradiction Guard    │
      └───────────────────────────────────────────────────┘
                               │
                               ▼
               [ PERSISTENT PROJECT MEMORY (v1.X) ]
```

---

## 2. Core Architectural Components

### I. iOS 26 Glassmorphism Interface System
A floating translucent glass UI (`GlassNav`, `GlassButton`, `GlassModal`) inspired by next-generation glass design languages:
- **Translucent Layering**: Controlled backdrop blurs (`backdrop-filter: blur(32px)`) with specular edge highlights.
- **Living Ambient Atmosphere**: Continuous canvas node-flow particle system that adapts its color frequency dynamically to the active section.
- **Accessible & High-Contrast**: Strictly tested against WCAG contrast guidelines; all critical controls remain legible with visible focus rings.

### II. Core Context Engine (`backend/services/context_engine.py`)
Continuo's guiding philosophy:
> **Don't transfer the conversation transcript. Transfer what the next AI actually needs to continue.**

The extraction pipeline heuristically decomposes noisy threads into:
1. **Objective**: High-level technical goal.
2. **Requirements**: Functional deliverables and specifications.
3. **Constraints**: Non-negotiable technical limits (e.g. "Do not store plaintext passwords").
4. **Decisions**: Locked architectural choices (e.g. "Migrated to FastAPI with SQLAlchemy").
5. **Current State**: Verified active operational milestone.
6. **Completed Work**: Finished tasks and applied migrations.
7. **Pending Work**: Queued items awaiting execution.
8. **Failed Approaches & Dead Ends**: Permanently recorded discarded paths so downstream models never repeat them.
9. **Files & Code in Scope**: Monitored repository artifacts.
10. **Immediate Next Steps**: Concrete instructions for the target model.

### III. Dynamic Context Quality Scorer (`backend/services/quality_scorer.py`)
A mathematical evaluator (0–100%) that measures context fidelity across four weighted dimensions:
- **Completeness (30 pts)**: Objective depth, requirement density, and constraint specifications.
- **Clarity & Depth (25 pts)**: File context grounding and dependency tracking.
- **Actionability & Readiness (25 pts)**: Immediate next steps and logged failed attempts.
- **Consistency & Contradiction Risk (20 pts)**: Real-time conflict deductions.

### IV. Contradiction Detection Service (`backend/services/contradiction.py`)
Detects mutually exclusive architectural decisions (e.g. choosing PostgreSQL earlier, then switching to MongoDB without formal reconciliation) and polar constraint violations (e.g. constraints strictly prohibiting NoSQL while a requirement specifies it).

### V. Semantic Memory Versioning & Diff Engine (`backend/services/version_diff.py`)
Maintains historical project context states (`v1.0`, `v1.1`, `v1.2`...). The visual diff engine compares any two milestones to display:
- **Added Elements**: Green glass pills.
- **Modified State**: Blue glass pills.
- **Removed / Retired Paths**: Red glass pills.

### VI. Tailored AI Handoff Generator (`backend/services/handoff_generator.py`)
Formats the Context Package into the optimal dialect for the destination model:
- **Claude (Anthropic)**: Formatted in structured XML tags (`<project_context>`, `<constraints>`, `<immediate_action_items>`) for highest adherence.
- **ChatGPT (OpenAI)**: Formatted in dense Markdown with executive guidelines.
- **Gemini (Google)**: Optimized structured prompt with direct goal grounding.
- **Cursor / VS Code**: Formatted as an autonomous `.cursorrules` / agent specification.

### VII. Chrome Extension Companion (Manifest V3)
A native browser companion located in `extension/` that parses conversation bubbles in ChatGPT (`chatgpt.com`), Claude (`claude.ai`), and Gemini (`gemini.google.com`), relaying context directly into project memory with one click.

---

## 3. Technology Stack

- **Frontend**: Vanilla HTML5, Modern CSS (Design Tokens, Glassmorphism), ES6+ JavaScript.
- **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic v2.
- **Database**: SQLAlchemy ORM with SQLite (development) and PostgreSQL / Supabase (production).
- **Authentication**: Stateless JWT with secure HMAC-SHA256 password hashing.
- **Browser Extension**: Chrome Manifest V3 (Service Worker, Content Scripts).
- **Testing**: Pytest, HTTPX, AnyIO test client.

---

## 4. Local Setup & Quickstart

### Prerequisites
- Python 3.12 or newer
- Node.js or modern browser (for serving static frontend)

### 1. Clone the Repository
```bash
git clone https://github.com/Anxhu03/continuo.git
cd continuo
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Setup Python Virtual Environment & Install Dependencies
```bash
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Start the FastAPI Backend Server
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8008 --reload
```
The interactive API documentation is available at:
- **Swagger UI**: [http://127.0.0.1:8008/docs](http://127.0.0.1:8008/docs)
- **ReDoc**: [http://127.0.0.1:8008/redoc](http://127.0.0.1:8008/redoc)

### 5. Serve the Web Interface
In another terminal, serve the frontend:
```bash
# Using Python HTTP Server:
python -m http.server 3000
```
Open your browser at **[http://localhost:3000/](http://localhost:3000/)**.

---

## 5. Running the Test Suite

Execute the complete end-to-end test suite:
```bash
pytest -v
```

Test coverage includes:
- `tests/test_api_endpoints.py`: Registration, authentication, user isolation, project creation, context capture, and multi-provider handoff generation.
- `tests/test_context_engine.py`: Raw dialogue extraction of goals, decisions, constraints, and files.
- `tests/test_quality_and_contradiction.py`: Dynamic mathematical scoring calibration and contradiction detection.
- `tests/test_version_diff.py`: Multi-version context delta calculations.

---

## 6. Installing the Chrome Extension

1. Open `chrome://extensions/` in Chrome, Brave, or Edge.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked**.
4. Select the `extension/` folder in this repository.
5. Pin Continuo to your toolbar.

---

## 7. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create a new user account |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT bearer token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |
| `GET` | `/api/v1/projects` | List all user-owned projects |
| `POST` | `/api/v1/projects` | Initialize a new persistent project memory |
| `GET` | `/api/v1/projects/{id}` | Retrieve project metadata and active version |
| `POST` | `/api/v1/context/capture` | Ingest raw dialogue, extract Context Package & bump version |
| `POST` | `/api/v1/context/analyze` | Stateless extraction & quality scoring preview |
| `GET` | `/api/v1/context/projects/{id}/context` | Fetch active Context Package |
| `PATCH` | `/api/v1/context/{id}` | Manually edit and curate context (bumps milestone version) |
| `GET` | `/api/v1/versions/projects/{id}` | List project version history |
| `GET` | `/api/v1/versions/projects/{id}/diff` | Calculate semantic diff between two versions |
| `POST` | `/api/v1/handoffs` | Generate model-tailored cross-AI handoff payload |

---

## 8. License & Privacy

Distributed under the Apache 2.0 License. See `LICENSE` for details.

Continuo enforces **Zero Training Data Retention**: Conversations and context packages captured through Continuo are never used to train, evaluate, or tune any third-party AI models.
