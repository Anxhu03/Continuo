"""
CONTINUO — End-to-End API Route Tests
Tests registration, authentication, project isolation, context capture, version diffing, and handoff generation.
"""

def test_full_api_workflow(client):
    # 1. Register User A
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "engineer_a@continuo.ai",
        "password": "SecurePassword123!",
        "full_name": "Elena Rostova"
    })
    assert reg_resp.status_code == 201
    token_a = reg_resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Check profile
    me_resp = client.get("/api/v1/auth/me", headers=headers_a)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "engineer_a@continuo.ai"

    # 3. Create Project
    proj_resp = client.post("/api/v1/projects", headers=headers_a, json={
        "name": "Nexora Autonomous Agent",
        "description": "Multi-agent context persistence orchestrator",
        "initial_objective": "Build high-throughput context continuity layer."
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]
    assert proj_resp.json()["current_version"] == "v1.0"

    # 4. List Projects
    list_resp = client.get("/api/v1/projects", headers=headers_a)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 5. Capture Context Dialogue
    capture_dialogue = """
    User: Let's refactor the authentication engine to support Google OAuth and JWT rotation.
    Requirement: Support Google and GitHub OAuth providers.
    Constraint: Never store plaintext secrets or refresh tokens in cookies without HttpOnly and Secure flags.
    Decision: Selected FastAPI with SQLAlchemy and PyJWT for stateless verification.
    Current State: OAuth callback handler working in test suite.
    Completed: Setup database migrations for refresh_tokens table.
    Pending: Implement token revocation endpoint.
    Next step: Connect frontend auth modal and verify cross-domain CORS tokens.
    """
    capture_resp = client.post("/api/v1/context/capture", headers=headers_a, json={
        "project_id": project_id,
        "provider": "chatgpt",
        "raw_transcript": capture_dialogue,
        "title": "Auth Refactor Session"
    })
    assert capture_resp.status_code == 201
    pkg = capture_resp.json()
    assert pkg["version"] == "v1.1"
    assert pkg["quality_score"] > 70.0

    # 6. Retrieve Project Context
    ctx_resp = client.get(f"/api/v1/context/projects/{project_id}/context", headers=headers_a)
    assert ctx_resp.status_code == 200
    assert ctx_resp.json()["version"] == "v1.1"

    # 7. Check Version History and Diff
    ver_resp = client.get(f"/api/v1/versions/projects/{project_id}", headers=headers_a)
    assert ver_resp.status_code == 200
    assert len(ver_resp.json()) >= 2 # v1.0 and v1.1

    diff_resp = client.get(
        f"/api/v1/versions/projects/{project_id}/diff?from_version=v1.0&to_version=v1.1",
        headers=headers_a
    )
    assert diff_resp.status_code == 200
    assert diff_resp.json()["from_version"] == "v1.0"
    assert diff_resp.json()["to_version"] == "v1.1"

    # 8. Generate Cross-AI Handoff for Claude
    handoff_resp = client.post("/api/v1/handoffs", headers=headers_a, json={
        "project_id": project_id,
        "source_provider": "chatgpt",
        "destination_provider": "claude",
        "custom_instructions": "Focus strictly on token revocation logic in auth/service.py."
    })
    assert handoff_resp.status_code == 201
    handoff_data = handoff_resp.json()
    assert "# Continue this project" in handoff_data["formatted_payload"]
    assert "## Instructions for continuing" in handoff_data["formatted_payload"]
    assert "https://claude.ai/new" in handoff_data["destination_url"]

    # 9. Verify Strict Security: User B cannot access User A's project, context, versions, or handoffs
    reg_b = client.post("/api/v1/auth/register", json={
        "email": "engineer_b@continuo.ai",
        "password": "Password456!",
        "full_name": "Marcus Vance"
    })
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B cannot read User A's project
    forbidden_proj = client.get(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert forbidden_proj.status_code == 403

    # User B cannot read User A's context
    forbidden_ctx = client.get(f"/api/v1/context/projects/{project_id}/context", headers=headers_b)
    assert forbidden_ctx.status_code == 403

    # User B cannot read User A's versions
    forbidden_ver = client.get(f"/api/v1/versions/projects/{project_id}", headers=headers_b)
    assert forbidden_ver.status_code == 403

    # User B cannot generate handoffs for User A's project
    forbidden_ho = client.post("/api/v1/handoffs", headers=headers_b, json={
        "project_id": project_id,
        "source_provider": "chatgpt",
        "destination_provider": "claude"
    })
    assert forbidden_ho.status_code == 403

def test_auth_rejection_and_context_patching(client):
    # Test invalid login rejection
    bad_login = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@continuo.ai",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401

    # Register user
    reg = client.post("/api/v1/auth/register", json={
        "email": "patcher@continuo.ai",
        "password": "StrongPassword789!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj = client.post("/api/v1/projects", headers=headers, json={
        "name": "State Machine Engine",
        "initial_objective": "Build deterministic actor model."
    }).json()
    project_id = proj["id"]

    # Get active context package
    ctx = client.get(f"/api/v1/context/projects/{project_id}/context", headers=headers).json()
    ctx_id = ctx["id"]

    # Patch context package with manual refinements
    patch_resp = client.patch(f"/api/v1/context/{ctx_id}", headers=headers, json={
        "objective": "Build high-throughput deterministic actor model with Raft consensus.",
        "requirements": ["Leader election in under 150ms", "Zero log corruption on network partition"],
        "constraints": ["No unbuffered channels", "Must run in single binary"]
    })
    assert patch_resp.status_code == 200
    patched = patch_resp.json()
    assert "Raft consensus" in patched["objective"]
    assert len(patched["requirements"]) == 2

    # Test multi-provider handoffs: Cursor and ChatGPT
    cursor_handoff = client.post("/api/v1/handoffs", headers=headers, json={
        "project_id": project_id,
        "source_provider": "claude",
        "destination_provider": "cursor"
    }).json()
    assert "CONTINUO CURSOR AGENT SPEC" in cursor_handoff["formatted_payload"]
    assert "cursor.com" in cursor_handoff["destination_url"]

    gpt_handoff = client.post("/api/v1/handoffs", headers=headers, json={
        "project_id": project_id,
        "source_provider": "cursor",
        "destination_provider": "chatgpt"
    }).json()
    assert "# Continue this project" in gpt_handoff["formatted_payload"]
    assert "https://chatgpt.com/" in gpt_handoff["destination_url"]


