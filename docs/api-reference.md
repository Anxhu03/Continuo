# Continuo REST API Reference

Continuo provides a RESTful API built on **FastAPI** for cross-model AI context continuity and persistent project memory management.

Interactive Swagger/OpenAPI documentation is available locally at:
```
http://localhost:8000/docs
```

---

## Authentication

All protected endpoints require a valid JWT bearer token in the `Authorization` header:

```http
Authorization: Bearer <jwt_access_token>
```

### 1. Register User
`POST /api/v1/auth/register`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "Ada Lovelace"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "id": "usr_94f8a1...",
    "email": "user@example.com",
    "full_name": "Ada Lovelace",
    "created_at": "2026-09-23T20:00:00Z"
  }
  ```

### 2. Login
`POST /api/v1/auth/login`
- **Request Body** (`application/x-www-form-urlencoded` or JSON):
  ```json
  {
    "username": "user@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer"
  }
  ```

---

## Projects Management

### List Projects
`GET /api/v1/projects`
- **Response** (`200 OK`): Array of `ProjectResponse` objects.

### Create Project
`POST /api/v1/projects`
- **Request Body**:
  ```json
  {
    "name": "Continuo Engine",
    "description": "Cross-provider context continuity system"
  }
  ```

---

## Context OS Entities

All Context OS endpoints are project-scoped and isolated to the authenticated user.

### 1. Context Goals
Endpoint: `/api/v1/projects/{project_id}/goals`

- **Create Goal** (`POST /api/v1/projects/{project_id}/goals`):
  ```json
  {
    "title": "Enable zero-data-loss context transfer",
    "description": "Support transferring active prompt and state across ChatGPT, Claude, and Gemini",
    "category": "milestone",
    "priority": "critical",
    "target_date": "2026-10-01T00:00:00Z"
  }
  ```
- **List Goals** (`GET /api/v1/projects/{project_id}/goals?status=active&priority=critical`)
- **Update Goal** (`PATCH /api/v1/projects/{project_id}/goals/{goal_id}`)
- **Delete Goal** (`DELETE /api/v1/projects/{project_id}/goals/{goal_id}`)

### 2. Context Decisions
Endpoint: `/api/v1/projects/{project_id}/decisions`

- **Create Decision** (`POST /api/v1/projects/{project_id}/decisions`):
  ```json
  {
    "title": "Adopt Fernet AES-128-CBC for API Key Encryption",
    "description": "Encrypt sensitive LLM keys at rest with HMAC-SHA256 authentication",
    "rationale": "Symmetric, authenticated encryption with no key leakage",
    "category": "security",
    "status": "accepted"
  }
  ```
- **Supersede Decision** (`POST /api/v1/projects/{project_id}/decisions/{decision_id}/supersede`):
  Automatically archives the old decision (`status="superseded"`), creates the new decision, and links `superseded_by_id`.

### 3. Context Tasks
Endpoint: `/api/v1/projects/{project_id}/tasks`

- **Create Task** (`POST /api/v1/projects/{project_id}/tasks`):
  ```json
  {
    "title": "Implement WebP image metadata extractor",
    "description": "Parse width, height, and channels deterministically from binary headers",
    "priority": "high",
    "status": "todo"
  }
  ```
- **Status Lifecycle Transitions**:
  `todo` ➔ `in_progress` ➔ `completed` (automatically sets `completed_at`). Transitioning back out of `completed` resets `completed_at = null`.

### 4. Context Technical State
Endpoint: `/api/v1/projects/{project_id}/technical-state`

- **Set / Update State** (`PUT /api/v1/projects/{project_id}/technical-state`):
  ```json
  {
    "category": "framework",
    "key": "backend",
    "value": "FastAPI",
    "confidence": 1.0,
    "source": "explicit"
  }
  ```
- **List Technical State** (`GET /api/v1/projects/{project_id}/technical-state`)

---

## Visual Context & Image Storage

Continuo supports secure, project-scoped visual references (screenshots, UI designs, 3D renders, diagrams).

### 1. Upload Visual Asset
`POST /api/v1/projects/{project_id}/images`
- **Request**: `multipart/form-data` with `file`, optional `description`, `image_type` (`ui_screenshot`, `design_reference`, `blender_render`, `diagram`, `moodboard`), and JSON `visual_tags`.
- **Validation**: Enforces supported MIME types (`png`, `jpeg`, `webp`, `gif`, `svg`), max size (10 MB), and extracts dimensions deterministically.

### 2. Download Image Binary
`GET /api/v1/projects/{project_id}/images/{image_id}/file`
- Streams image binary with sanitized content headers and cache control.

### 3. Associate Image With Decisions / Goals / Tasks
`PATCH /api/v1/projects/{project_id}/images/{image_id}`
- Update associations (`associated_decision_ids`, `associated_context_ids`, `visual_tags`).
- Automatically verifies all linked entities belong to the same project and user.

---

## Context Extraction Intelligence

### Structured Context OS Extraction
`POST /context/extract-os`
`POST /api/v1/projects/{project_id}/context-extract`

Analyzes raw AI conversation transcripts and extracts normalized candidates for goals, decisions, tasks, technical state, and visual image references.

- **Request Body**:
  ```json
  {
    "project_id": "proj_a1b2c3",
    "raw_transcript": "Decision: We will use Three.js for 3D visuals. Todo: Fix character animation lag. Goal: Launch beta by next Friday.",
    "auto_persist": true
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "extracted": {
      "goals": [
        {
          "title": "Launch beta by next Friday",
          "category": "milestone",
          "priority": "normal",
          "confidence": 0.95,
          "explicit": true
        }
      ],
      "decisions": [
        {
          "title": "We will use Three.js for 3D visuals",
          "category": "architecture",
          "status": "accepted",
          "confidence": 0.95,
          "explicit": true
        }
      ],
      "tasks": [
        {
          "title": "Fix character animation lag",
          "status": "todo",
          "priority": "normal",
          "confidence": 0.95,
          "explicit": true
        }
      ],
      "technical_states": [
        {
          "category": "framework",
          "key": "three.js",
          "value": "Three.js",
          "confidence": 0.90,
          "explicit": true
        }
      ],
      "visual_references": [],
      "contradictions": []
    },
    "persisted_count": {
      "goals": 1,
      "decisions": 1,
      "tasks": 1,
      "technical_states": 1
    }
  }
  ```

---

## Legacy Context Capture & Handoffs

### 1. Capture Context
`POST /context/capture`
- Captures active provider context, generates a standardized `ContextPackage`, and automatically extracts and persists Context OS entities for the active project.

### 2. Generate Provider Handoff
`POST /context/generate-handoff`
- Transforms stored context into formatted prompt prompts tailored for ChatGPT, Claude, or Gemini. Redacts any embedded secrets automatically.
