"""
CONTINUO — End-to-End Extraction Pipeline & Backend Save Verification
Verifies that normalized conversation payloads extracted from ChatGPT, Claude, and Gemini
flow smoothly through the popup capture formatting and are successfully ingested
by the Continuo Context Engine and Project Memory.
"""

def test_ai_adapters_to_context_engine_e2e(client):
    # 1. Register engineer
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "pipeline_tester@continuo.ai",
        "password": "SecurePassword123!",
        "full_name": "Pipeline Verification Bot"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project
    proj_resp = client.post("/api/v1/projects", headers=headers, json={
        "name": "Cross-AI Extraction Pipeline",
        "description": "Validation project for ChatGPT, Claude, and Gemini context persistence",
        "initial_objective": "Validate seamless context capture across all supported AI providers."
    })
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]
    assert proj_resp.json()["current_version"] == "v1.0"

    # 3. Simulate normalized ChatGPT capture
    chatgpt_normalized = {
        "provider": "chatgpt",
        "conversation_id": "c-chatgpt-8921-uuid",
        "title": "FastAPI Rate Limiting Architecture",
        "url": "https://chatgpt.com/c/c-chatgpt-8921-uuid",
        "messages": [
            {
                "role": "user",
                "content": "Let's design a distributed sliding-window rate limiter."
            },
            {
                "role": "assistant",
                "content": (
                    "Decision: Selected Redis sorted sets for sliding window tracking.\n"
                    "Requirement: Max 100 requests per minute per IP.\n"
                    "Constraint: Must fail open if Redis cluster is temporarily unreachable.\n"
                    "Completed: Lua script for atomic sliding-window increment.\n"
                    "Pending: Unit tests with mock Redis cluster.\n"
                    "Next step: Add FastAPI middleware hook."
                )
            }
        ]
    }

    # Format transcript using popup.js logic
    chatgpt_transcript = "\n\n".join([
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in chatgpt_normalized["messages"]
    ])

    cap_resp_1 = client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": project_id,
        "provider": chatgpt_normalized["provider"],
        "raw_transcript": chatgpt_transcript,
        "title": chatgpt_normalized["title"]
    })
    assert cap_resp_1.status_code == 201
    pkg_1 = cap_resp_1.json()
    assert pkg_1["version"] == "v1.1"
    assert pkg_1["quality_score"] > 60.0
    assert any("Redis sorted sets" in str(d) for d in pkg_1.get("decisions", []))

    # 4. Simulate normalized Claude capture continuing the project
    claude_normalized = {
        "provider": "claude",
        "conversation_id": "c-claude-4432-uuid",
        "title": "Redis Cluster Fault Tolerance",
        "url": "https://claude.ai/chat/c-claude-4432-uuid",
        "messages": [
            {
                "role": "user",
                "content": "Now let's implement the fallback circuit breaker in middleware.py."
            },
            {
                "role": "assistant",
                "content": (
                    "Decision: Used pybreaker with 5 failure threshold and 30s reset timeout.\n"
                    "Completed: FastAPI rate-limit middleware with pybreaker integration.\n"
                    "Current State: Middleware unit tests passing with 100% branch coverage.\n"
                    "Next step: Benchmark throughput under 10k req/s load."
                )
            }
        ]
    }

    claude_transcript = "\n\n".join([
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in claude_normalized["messages"]
    ])

    cap_resp_2 = client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": project_id,
        "provider": claude_normalized["provider"],
        "raw_transcript": claude_transcript,
        "title": claude_normalized["title"]
    })
    assert cap_resp_2.status_code == 201
    pkg_2 = cap_resp_2.json()
    assert pkg_2["version"] == "v1.2"
    assert pkg_2["quality_score"] > 60.0

    # 5. Simulate normalized Gemini capture
    gemini_normalized = {
        "provider": "gemini",
        "conversation_id": "c-gemini-7719",
        "title": "High Throughput Benchmark",
        "url": "https://gemini.google.com/app/c-gemini-7719",
        "messages": [
            {
                "role": "user",
                "content": "Review Locust load testing results and plan production rollout."
            },
            {
                "role": "assistant",
                "content": (
                    "Decision: Approved rollout strategy: 10% canary traffic followed by 100% switchover.\n"
                    "Completed: Load test reached 12,500 req/s with p99 latency < 8ms.\n"
                    "Next step: Merge canary PR into production branch."
                )
            }
        ]
    }

    gemini_transcript = "\n\n".join([
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in gemini_normalized["messages"]
    ])

    cap_resp_3 = client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": project_id,
        "provider": gemini_normalized["provider"],
        "raw_transcript": gemini_transcript,
        "title": gemini_normalized["title"]
    })
    assert cap_resp_3.status_code == 201
    pkg_3 = cap_resp_3.json()
    assert pkg_3["version"] == "v1.3"

    # 6. Verify full version history in Project Memory
    versions_resp = client.get(f"/api/v1/versions/projects/{project_id}", headers=headers)
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 4 # v1.0, v1.1, v1.2, v1.3
    version_tags = [v["version_number"] for v in versions]
    assert "v1.0" in version_tags
    assert "v1.1" in version_tags
    assert "v1.2" in version_tags
    assert "v1.3" in version_tags
