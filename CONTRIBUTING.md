# Contributing to Continuo

Thank you for your interest in contributing to **Continuo**! We welcome contributions to the Context OS Engine, provider adapters, REST APIs, visual context pipelines, and browser companions.

---

## Code of Conduct & Open Source Philosophy

- **Genuine Software Engineering**: All contributions must represent authentic, tested code or meaningful documentation improvements.
- **Provider Neutrality**: Continuo acts as an impartial memory layer between AI platforms (ChatGPT, Claude, Gemini, etc.). Features should remain provider-agnostic.
- **Privacy & Security by Default**: Never bypass encryption, tenant isolation, or secret sanitization.

---

## Development Environment Setup

### Prerequisites
- **Python**: 3.12 or higher
- **Node.js**: 18.x or higher (for browser extension adapter testing)
- **Git**

### Step 1: Clone and Branch
```bash
git clone https://github.com/Anxhu03/Continuo.git
cd Continuo
git checkout -b feat/your-feature-name
```

### Step 2: Virtual Environment Setup

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

### Step 3: Environment Configuration
Create a `.env` file in the root directory (based on `.env.example`):
```env
DATABASE_URL=sqlite:///./continuo.db
ENCRYPTION_KEY=MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDE=
ENVIRONMENT=development
PORT=8000
```

### Step 4: Run the Local Development Server
```bash
uvicorn backend.main:app --reload --port 8000
```
Visit `http://localhost:8000/docs` to explore the interactive OpenAPI / Swagger UI.

---

## Comprehensive Test Suite

Before opening a pull request, all test suites must pass 100%:

```bash
# 1. Run full backend pytest suite (121+ tests)
pytest -v

# 2. Run critical task action (CTA) verification
python verify_cta.py

# 3. Run browser extension provider adapter test suite (Node.js)
node scripts/test-adapters.js
```

---

## Coding Standards & Architectural Guidelines

### 1. Python & FastAPI Backend
- **Type Annotations**: All function signatures, router dependencies, and models must include strict typing.
- **Validation**: Use Pydantic schemas in `backend/schemas/__init__.py` for all request/response validation.
- **Tenant Isolation**: Every database query on project-scoped entities (`ContextGoal`, `ContextDecision`, `ContextTask`, `ContextTechnicalState`, `ContextImage`) **must filter by both `project_id` and the authenticated `user_id`**.
- **Security & Redaction**: Any user-provided prompt or extracted text must pass through `backend.services.handoff_generator.sanitize_secrets()` before persistence or handoff generation.

### 2. Browser Extension (Chrome MV3)
- Located under `extension/`.
- Must follow Manifest V3 standards (service workers, content scripts, popup UI).
- Adapters under `extension/adapters/` must handle dynamic DOM updates gracefully without polling endlessly.

### 3. Commit Convention
Follow Conventional Commits:
- `feat: add visual asset tag filtering`
- `fix: correct markdown prompt handoff formatting for Claude`
- `test: add edge cases for decision superseding lifecycle`
- `docs: update API reference for Context OS tasks`
- `refactor: clean up deprecated Starlette status codes`

---

## Submitting Pull Requests

1. **Keep PRs Focused**: Aim for small, reviewable pull requests addressing one bug or feature.
2. **Include Tests**: Add unit or integration tests in `tests/` covering new behavior or edge cases.
3. **Fill Out the PR Template**: Detail the changes made, tests executed, and architectural impact.
4. **Clean Git History**: Rebase against the latest `main` before submitting.
