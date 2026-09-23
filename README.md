# Continuo

<div align="center">

<img src="assets/logo.webp" alt="Continuo Logo" width="96" height="96" />

### Keep your context. Continue anywhere.

**Persistent Context OS & AI Conversation Continuity Engine.**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![Chrome MV3](https://img.shields.io/badge/Extension-Chrome%20MV3-4285F4.svg)](https://developer.chrome.com/docs/extensions/mv3/)
[![License](https://img.shields.io/badge/License-Apache%202.0-black.svg)](LICENSE)
[![Security Policy](https://img.shields.io/badge/Security-Policy-brightgreen.svg)](SECURITY.md)
[![Tests](https://img.shields.io/badge/Tests-121%20Passing-brightgreen.svg)](tests/)

</div>

---

## 1. What Continuo Does

Modern AI software engineering is fragmented across multiple foundation models and assistants:
- You brainstorm and architect in **ChatGPT**.
- You perform nuanced refactoring and deep reasoning in **Claude**.
- You run multimodal search and large-context analysis in **Gemini**.
- You implement code within editor companions like **Cursor**.

Every time you switch models, your context fractures. You spend 30–60 minutes copying outdated notes, re-explaining architectural decisions, and fighting hallucinated drift.

**Continuo transforms fragmented dialogue into a Persistent Context OS.**

```
Conversation Continuity  ───►  Project Continuity  ───►  Persistent Context OS
 (Cross-Model Handoffs)        (Versioned Memory)         (Normalized Entities & Visual Assets)
```

Continuo captures conversations, extracts normalized project entities (Goals, Decisions, Tasks, Technical State, Visual Assets), detects contradictions, and generates instant continuation prompts formatted for target AI providers.

```
User works in ChatGPT / Claude / Gemini
        ↓
Reaches milestone or stopping point
        ↓
Clicks Continuo extension companion
        ↓
Continuo extracts structured context (Goals, Decisions, Tasks, Visuals)
        ↓
Stores in Persistent Context OS (User & Project Isolated)
        ↓
Selects destination model (Claude, ChatGPT, Gemini)
        ↓
Continuo formats prompt & copies to clipboard with zero secret leakage
        ↓
Destination AI opens; user pastes and continues immediately
```

---

## 2. Context OS Architecture

Continuo maintains a strict separation of concerns, providing provider neutrality, cryptographic credential security, and multi-tenant isolation:

```
                    ┌─────────────────────────┐
                    │          USER           │
                    └────────────┬────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
                   ▼                           ▼
            CONTINUO WEB APP            CHROME EXTENSION
            (Workspace & UI)           (1-Click MV3 Companion)
                   │                           │
                   └─────────────┬─────────────┘
                                 ▼
                         FASTAPI GATEWAY
                    (REST API v1 / OpenAPI)
                                 │
         ┌───────────────┬───────┴───────┬───────────────┐
         ▼               ▼               ▼               ▼
     AUTH & JWT    CONTEXT OS      VISUAL ASSET     AI HANDOFF
    (Argon2 / AES)  ENGINE         STORAGE LAYER     GENERATOR
                         │               │
                         ▼               ▼
                 NORMALIZED ENTITIES  METADATA & BINARY
                 - Goals             (PNG, WEBP, JPEG)
                 - Decisions
                 - Tasks
                 - Technical State
                         │
                         ▼
                   DATABASE LAYER
              (PostgreSQL / SQLite)
```

### Context OS Normalized Entities

1. **Context Goals (`ContextGoal`)**: Tracks core project objectives, milestones, constraints, and target delivery dates with explicit priority levels (`critical`, `high`, `normal`, `low`).
2. **Context Decisions (`ContextDecision`)**: Retains architectural decisions, rationale, status (`accepted`, `under_review`, `superseded`), and links superseding decisions over time.
3. **Context Tasks (`ContextTask`)**: Tracks tasks and issues through an automated lifecycle (`todo` ➔ `in_progress` ➔ `completed` with automated `completed_at` population).
4. **Context Technical State (`ContextTechnicalState`)**: Tracks key-value configurations across frameworks, databases, renderers, runtime versions, and styling systems.
5. **Visual Context Assets (`ContextImage`)**: First-class visual references (UI screenshots, design references, Blender 3D renders, architectural diagrams) with deterministic metadata extraction and entity association.
6. **Contradiction Detection**: Cross-references prospective decisions against existing technology stacks to flag conflicting architectural paradigms (e.g. Three.js vs Babylon.js).

---

## 3. Key Features

- **Chrome Extension Companion (Manifest V3)**: Deterministic 7-state popup (`UNAUTHENTICATED`, `NO_AI_DETECTED`, `EMPTY_CONVERSATION`, `AI_DETECTED`, `CAPTURING`, `SUCCESS`, `ERROR`).
- **Live Tab DOM Extraction**: Safely extracts message turns directly from the active tab on `chatgpt.com`, `claude.ai`, and `gemini.google.com`.
- **Intelligent Context Extraction (`/context/extract-os`)**: Heuristic parser that classifies goals, tasks, accepted vs tentative decisions, technical state, and visual assets without mandatory cloud vision APIs.
- **Visual Reference Management**: Local project-scoped storage with SHA-256 integrity, MIME validation, dimension extraction, and cross-entity linking.
- **Universal Provider Handoffs**: Formats structured prompt packages tailored to Claude, ChatGPT, and Gemini with automated secret redaction (`[REDACTED_SECRET]`).
- **Cryptographic Security**: Sensitive provider API keys encrypted using Fernet AES-128-CBC; passwords hashed using Argon2id.
- **Strict Multi-Tenant Isolation**: Every project resource strictly validates ownership; cross-tenant access attempts return `403 Forbidden`.
- **Automated Test Coverage**: 121+ unit and integration tests passing with 100% CTA verification.

---

## 4. Repository Structure

```
Continuo/
├── .github/
│   ├── workflows/ci.yml          # GitHub Actions CI matrix (Python 3.12, 3.13, Node 20)
│   ├── ISSUE_TEMPLATE/           # Structured bug report and feature request forms
│   └── PULL_REQUEST_TEMPLATE.md  # Standard pull request verification template
├── backend/
│   ├── config.py                 # Pydantic settings & CORS configurations
│   ├── database.py               # SQLAlchemy engine & session factory
│   ├── main.py                   # FastAPI application gateway
│   ├── models/                   # Database models (User, Project, Context OS entities)
│   ├── routers/                  # Modular REST routers (auth, projects, goals, decisions, etc.)
│   ├── schemas/                  # Pydantic v2 schemas for all requests/responses
│   └── services/                 # Business logic, extraction engine, validators, encryption
├── extension/
│   ├── manifest.json             # Chrome Manifest V3 configuration
│   ├── popup.html / popup.js     # Companion popup state machine
│   ├── content.js                # Content script extracting ChatGPT / Claude / Gemini DOM turns
│   └── adapters/                 # Model-specific DOM extraction adapters
├── docs/
│   ├── api-reference.md          # Comprehensive REST API reference
│   ├── context-os-architecture.md# Deep Context OS architectural design document
│   ├── CHROME_STORE_SUBMISSION.md# Chrome Web Store listing copy & justifications
│   └── PRIVACY.md                # Data governance & privacy commitments
├── scripts/
│   ├── package-extension.py      # Deterministic extension ZIP packager
│   └── test-adapters.js          # Provider DOM adapter test suite
├── tests/                        # 121+ Pytest unit & integration tests
├── CONTRIBUTING.md               # Cross-platform contributor guidelines
├── SECURITY.md                   # Security disclosure policy & architecture
├── LICENSE                       # Apache License 2.0
├── requirements.txt              # Backend dependencies
└── verify_cta.py                 # Critical task action validation script
```

---

## 5. Quick Start & Local Setup

### Prerequisites
- **Python**: 3.12 or newer
- **Node.js**: 18.x or newer
- **Google Chrome** (or Chromium-based browser: Brave, Edge)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/Anxhu03/Continuo.git
cd Continuo
```

### 2. Environment Configuration
```bash
cp .env.example .env
```
Ensure `.env` contains:
```env
DATABASE_URL=sqlite:///./continuo.db
ENCRYPTION_KEY=MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=
ENVIRONMENT=development
PORT=8000
```

### 3. Backend Setup

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt pytest httpx
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt pytest httpx
```

Start the FastAPI development server:
```bash
uvicorn backend.main:app --reload --port 8000
```
Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 4. Chrome Extension Installation

1. In Google Chrome, navigate to `chrome://extensions`.
2. Toggle **Developer mode** to ON (top right corner).
3. Click **Load unpacked**.
4. Select the `extension/` directory from this repository.
5. Pin Continuo to your Chrome toolbar.

---

## 6. Automated Testing & Verification

All contributions must pass the verification suites:

```bash
# 1. Run full backend pytest suite (121 tests)
pytest -v

# 2. Run critical task action (CTA) verification
python verify_cta.py

# 3. Run browser provider adapter tests (Node.js)
node scripts/test-adapters.js
```

---

## 7. Universal Handoff Prompt Schema

Continuo formats cross-AI continuation packages into a concise, token-efficient schema that downstream models ingest without confusion:

```markdown
You are continuing an existing project.

PROJECT:
Continuo Context Engine (v1.2)

OBJECTIVE:
Build high-throughput context continuity layer across multiple AI models.

CURRENT STATE:
Persistent Context OS entities extracted and normalized.

IMPORTANT DECISIONS:
- Selected FastAPI with SQLAlchemy and PyJWT for stateless verification
- Fernet AES-128-CBC for sensitive credential encryption at rest

CONSTRAINTS:
- Never store plaintext secrets or refresh tokens in insecure cookies
- Enforce strict tenant isolation across all endpoints

NEXT STEPS:
1. Connect frontend auth modal and verify cross-domain CORS tokens
2. Run end-to-end multi-provider browser handoff verification

CONTINUE FROM HERE:
Continue from the current state. Do not restart the project. Preserve existing decisions.
```

---

## 8. Documentation

- [REST API Reference](docs/api-reference.md)
- [Context OS Architecture](docs/context-os-architecture.md)
- [Security Policy](SECURITY.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Chrome Web Store Submission](docs/CHROME_STORE_SUBMISSION.md)
- [Privacy Policy](docs/PRIVACY.md)

---

## 9. License

Distributed under the **Apache License, Version 2.0**. See [`LICENSE`](LICENSE) for details.
