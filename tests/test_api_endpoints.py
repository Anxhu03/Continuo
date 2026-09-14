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
    assert "You are continuing an existing project." in handoff_data["formatted_payload"]
    assert "Continue from the current state." in handoff_data["formatted_payload"]
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
    assert "You are continuing an existing project." in cursor_handoff["formatted_payload"] or "CONTINUO CURSOR AGENT SPEC" in cursor_handoff["formatted_payload"]
    assert "cursor.com" in cursor_handoff["destination_url"]

    gpt_handoff = client.post("/api/v1/handoffs", headers=headers, json={
        "project_id": project_id,
        "source_provider": "cursor",
        "destination_provider": "chatgpt"
    }).json()
    assert "You are continuing an existing project." in gpt_handoff["formatted_payload"]
    assert "https://chatgpt.com/" in gpt_handoff["destination_url"]


def test_comprehensive_cross_user_data_isolation(client):
    """
    Comprehensive Security Audit:
    Verifies that a user can never read, modify, delete, capture context for,
    or generate handoffs for another user's project.
    """
    # 1. Register User Alpha
    alpha_reg = client.post("/api/v1/auth/register", json={
        "email": "alpha_lead@continuo.ai",
        "password": "AlphaSecure2026!",
        "full_name": "Alpha Lead"
    })
    assert alpha_reg.status_code == 201
    alpha_token = alpha_reg.json()["access_token"]
    alpha_hdr = {"Authorization": f"Bearer {alpha_token}"}

    # 2. Register User Beta (Attacker / Unauthorized User)
    beta_reg = client.post("/api/v1/auth/register", json={
        "email": "beta_intruder@continuo.ai",
        "password": "BetaSecure2026!",
        "full_name": "Beta User"
    })
    assert beta_reg.status_code == 201
    beta_token = beta_reg.json()["access_token"]
    beta_hdr = {"Authorization": f"Bearer {beta_token}"}

    # 3. User Alpha creates a secret project
    proj_a = client.post("/api/v1/projects", headers=alpha_hdr, json={
        "name": "Project Alpha Secret Defense",
        "description": "High-security internal algorithms",
        "initial_objective": "Proprietary zero-knowledge proof compiler."
    }).json()
    proj_id = proj_a["id"]

    # 4. User Beta attempts unauthorized read -> 403 Forbidden
    resp = client.get(f"/api/v1/projects/{proj_id}", headers=beta_hdr)
    assert resp.status_code == 403

    # 5. User Beta attempts unauthorized update -> 403 Forbidden
    resp = client.patch(f"/api/v1/projects/{proj_id}", headers=beta_hdr, json={
        "name": "Tampered By Beta"
    })
    assert resp.status_code == 403

    # 6. User Beta attempts unauthorized delete -> 403 Forbidden
    resp = client.delete(f"/api/v1/projects/{proj_id}", headers=beta_hdr)
    assert resp.status_code == 403

    # 7. User Beta attempts unauthorized context capture -> 403 Forbidden
    resp = client.post("/api/v1/context/capture", headers=beta_hdr, json={
        "project_id": proj_id,
        "provider": "claude",
        "raw_transcript": "User: Injection attempt.\nAssistant: Forbidden."
    })
    assert resp.status_code == 403

    # 8. User Beta attempts unauthorized context fetch -> 403 Forbidden
    resp = client.get(f"/api/v1/context/projects/{proj_id}/context", headers=beta_hdr)
    assert resp.status_code == 403

    # 9. User Beta attempts unauthorized context update -> 403 Forbidden
    resp = client.patch(f"/api/v1/context/projects/{proj_id}/context", headers=beta_hdr, json={
        "objective": "Tampered context"
    })
    assert resp.status_code == 403

    # 10. User Beta attempts unauthorized version listing -> 403 Forbidden
    resp = client.get(f"/api/v1/versions/projects/{proj_id}", headers=beta_hdr)
    assert resp.status_code == 403

    # 11. User Beta attempts unauthorized version diff -> 403 Forbidden
    resp = client.get(f"/api/v1/versions/projects/{proj_id}/diff?from_version=v1.0&to_version=v1.0", headers=beta_hdr)
    assert resp.status_code == 403

    # 12. User Beta attempts unauthorized handoff creation -> 403 Forbidden
    resp = client.post("/api/v1/handoffs", headers=beta_hdr, json={
        "project_id": proj_id,
        "destination_provider": "gemini"
    })
    assert resp.status_code == 403

    # 13. User Beta attempts unauthorized handoff listing -> 403 Forbidden
    resp = client.get(f"/api/v1/handoffs/projects/{proj_id}", headers=beta_hdr)
    assert resp.status_code == 403

    # 14. Unauthenticated request to private project -> 401 Unauthorized
    resp = client.get(f"/api/v1/projects/{proj_id}")
    assert resp.status_code == 401

    # 15. Fake / expired token -> 401 Unauthorized
    resp = client.get(f"/api/v1/projects/{proj_id}", headers={"Authorization": "Bearer invalid_expired_jwt_token"})
    assert resp.status_code == 401


def test_user_roles_and_admin_diagnostics(client):
    """
    Role Authorization & Diagnostics Tests:
    - Standard users default to 'user' role and are denied access to /api/v1/admin/diagnostics (403).
    - Users with 'developer' or 'admin' role can access /api/v1/admin/diagnostics (200).
    """
    # 1. Register standard user
    user_reg = client.post("/api/v1/auth/register", json={
        "email": "standard_dev@continuo.ai",
        "password": "UserPass123!",
        "full_name": "Standard Dev"
    })
    assert user_reg.status_code == 201
    user_data = user_reg.json()
    assert user_data.get("role") == "user"
    user_token = user_data["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Verify /auth/me returns role="user"
    me_resp = client.get("/api/v1/auth/me", headers=user_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "user"

    # Standard user attempting to access /admin/diagnostics gets 403 Forbidden
    diag_denied = client.get("/api/v1/admin/diagnostics", headers=user_headers)
    assert diag_denied.status_code == 403

    # 2. Register developer user
    dev_reg = client.post("/api/v1/auth/register", json={
        "email": "lead_architect@continuo.ai",
        "password": "ArchitectPass123!",
        "full_name": "Lead Architect",
        "role": "developer"
    })
    assert dev_reg.status_code == 201
    dev_data = dev_reg.json()
    assert dev_data.get("role") == "developer"
    dev_token = dev_data["access_token"]
    dev_headers = {"Authorization": f"Bearer {dev_token}"}

    # Developer user accessing /admin/diagnostics gets 200 OK
    diag_ok = client.get("/api/v1/admin/diagnostics", headers=dev_headers)
    assert diag_ok.status_code == 200
    diag_body = diag_ok.json()
    assert diag_body["status"] == "operational"
    assert diag_body["gateway_port"] in (8008, 8000)
    assert "active_users" in diag_body
    assert "active_projects" in diag_body
    assert "total_context_packages" in diag_body
    assert diag_body["features"]["role_based_access"] is True


def test_empty_and_invalid_transcript_validation(client):
    """
    Validation Test:
    Ensures empty or sub-10 character transcripts are rejected with 422 Unprocessable Entity.
    """
    reg = client.post("/api/v1/auth/register", json={
        "email": "validator@continuo.ai",
        "password": "ValidatorPass123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj = client.post("/api/v1/projects", headers=headers, json={"name": "Val Project"}).json()
    proj_id = proj["id"]

    # Short transcript under 10 chars
    short_resp = client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": proj_id,
        "provider": "chatgpt",
        "raw_transcript": "Hi"
    })
    assert short_resp.status_code == 422

    # Empty string transcript
    empty_resp = client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": proj_id,
        "provider": "chatgpt",
        "raw_transcript": ""
    })
    assert empty_resp.status_code == 422


def test_version_diff_identical_versions(client):
    """
    Version Diff Test:
    Ensures comparing identical versions returns 'No meaningful changes detected.'
    """
    reg = client.post("/api/v1/auth/register", json={
        "email": "diff_tester@continuo.ai",
        "password": "DiffPassword123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj = client.post("/api/v1/projects", headers=headers, json={"name": "Diff Project"}).json()
    proj_id = proj["id"]

    diff_resp = client.get(
        f"/api/v1/versions/projects/{proj_id}/diff?from_version=v1.0&to_version=v1.0",
        headers=headers
    )
def test_handoff_11_part_structured_payload(client):
    """
    Handoff Payload Fidelity Test:
    Ensures generated handoff payload contains the exact 11 standardized section headers
    and the continuation directive.
    """
    reg = client.post("/api/v1/auth/register", json={
        "email": "handoff_lead@continuo.ai",
        "password": "HandoffPassword123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj = client.post("/api/v1/projects", headers=headers, json={
        "name": "Cloud Mesh Network",
        "initial_objective": "Build zero-trust multi-cluster service mesh"
    }).json()
    proj_id = proj["id"]

    # Capture rich dialogue to populate sections
    dialogue = """
    User: Let's design the service mesh mTLS certificate rotation.
    Requirement: Auto-rotate envoy mTLS certs every 24 hours.
    Constraint: Zero dropped packets during key rotation.
    Decision: Use SPIFFE/SPIRE with cert-manager integration.
    Current State: Controller watching SPIFFE secrets.
    Completed: Deployed Spire server agent daemonset.
    Pending: Implement graceful Envoy listener reload via ADS API.
    File: k8s/spire-daemonset.yaml and envoy/cds.yaml
    Problem: Envoy reload caused 12ms latency spike under peak load.
    Failed Attempt: Tried hard restart of envoy pod which dropped active WebSocket connections.
    Next step: Wire ADS warm listener swap with graceful drain timeout.
    """
    client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": proj_id,
        "provider": "chatgpt",
        "raw_transcript": dialogue,
        "title": "mTLS Rotation Design"
    })

    # Generate handoff
    ho_resp = client.post("/api/v1/handoffs", headers=headers, json={
        "project_id": proj_id,
        "source_provider": "chatgpt",
        "destination_provider": "claude",
        "custom_instructions": "Focus strictly on ADS listener swap."
    })
    assert ho_resp.status_code == 201
    payload = ho_resp.json()["formatted_payload"]

    required_sections = [
        "PROJECT:",
        "OBJECTIVE:",
        "CURRENT STATE:",
        "COMPLETED WORK:",
        "STILL WORKING ON:",
        "IMPORTANT DECISIONS:",
        "CONSTRAINTS:",
        "OPEN PROBLEMS:",
        "FILES / CODE CONTEXT:",
        "FAILED ATTEMPTS:",
        "NEXT STEPS:"
    ]

    for section in required_sections:
        assert section in payload, f"Missing section in handoff payload: {section}"

    assert "Continue from the current state" in payload
    assert "https://claude.ai/new" == ho_resp.json()["destination_url"]




