"""
CONTINUO — Persistent Context OS API Tests (Phase 9.3)
Validates CRUD, filtering, lifecycle automation, history preservation,
conflict resolution, IDOR defense, and cross-tenant isolation across:
1. ContextGoal
2. ContextDecision
3. ContextTask
4. ContextTechnicalState
"""

import pytest
from datetime import datetime


def register_user(client, email: str, password: str = "SecurePass123!", name: str = "Test User"):
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name,
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client, headers: dict, name: str = "Alpha OS Project"):
    resp = client.post("/api/v1/projects", headers=headers, json={
        "name": name,
        "description": "Core context test project",
        "initial_objective": "Test Context OS functionality",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


# =============================================================================
# GOALS API TESTS
# =============================================================================

def test_1_create_goal(client):
    """1. Create goal with default priority and status."""
    headers = register_user(client, "goal_creator@continuo.ai")
    proj_id = create_project(client, headers)

    resp = client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Establish Context Engine v2",
        "description": "Migrate from monolithic snapshots to granular relational entities.",
        "category": "requirement",
        "priority": "critical",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Establish Context Engine v2"
    assert data["category"] == "requirement"
    assert data["priority"] == "critical"
    assert data["status"] == "active"
    assert data["project_id"] == proj_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_2_list_goals_and_filtering(client):
    """2. List goals with status, priority, and category filters, ordered by updated_at DESC."""
    headers = register_user(client, "goal_lister@continuo.ai")
    proj_id = create_project(client, headers)

    # Create 3 goals
    client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Goal 1",
        "category": "goal",
        "status": "active",
        "priority": "high",
    })
    client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Goal 2",
        "category": "constraint",
        "status": "completed",
        "priority": "low",
    })
    client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Goal 3",
        "category": "goal",
        "status": "active",
        "priority": "critical",
    })

    # List all
    all_resp = client.get(f"/api/v1/projects/{proj_id}/goals", headers=headers)
    assert all_resp.status_code == 200
    assert len(all_resp.json()) == 3

    # Filter by status
    active_resp = client.get(f"/api/v1/projects/{proj_id}/goals?status=active", headers=headers)
    assert active_resp.status_code == 200
    assert len(active_resp.json()) == 2
    assert all(g["status"] == "active" for g in active_resp.json())

    # Filter by priority
    crit_resp = client.get(f"/api/v1/projects/{proj_id}/goals?priority=critical", headers=headers)
    assert crit_resp.status_code == 200
    assert len(crit_resp.json()) == 1
    assert crit_resp.json()[0]["title"] == "Goal 3"

    # Filter by category
    cat_resp = client.get(f"/api/v1/projects/{proj_id}/goals?category=constraint", headers=headers)
    assert cat_resp.status_code == 200
    assert len(cat_resp.json()) == 1
    assert cat_resp.json()[0]["title"] == "Goal 2"


def test_3_get_goal(client):
    """3. Get single goal by ID."""
    headers = register_user(client, "goal_getter@continuo.ai")
    proj_id = create_project(client, headers)

    create_resp = client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Inspect single goal",
        "category": "instruction",
    })
    goal_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/projects/{proj_id}/goals/{goal_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == goal_id
    assert get_resp.json()["title"] == "Inspect single goal"


def test_4_update_goal(client):
    """4. Update goal attributes."""
    headers = register_user(client, "goal_updater@continuo.ai")
    proj_id = create_project(client, headers)

    create_resp = client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Initial Goal",
        "status": "active",
        "priority": "normal",
    })
    goal_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/v1/projects/{proj_id}/goals/{goal_id}", headers=headers, json={
        "title": "Updated Goal",
        "status": "completed",
        "priority": "high",
        "description": "Now finished successfully",
    })
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["title"] == "Updated Goal"
    assert updated["status"] == "completed"
    assert updated["priority"] == "high"
    assert updated["description"] == "Now finished successfully"


def test_5_delete_goal(client):
    """5. Delete goal with 204 No Content and verify subsequent 404."""
    headers = register_user(client, "goal_deleter@continuo.ai")
    proj_id = create_project(client, headers)

    create_resp = client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Temporary Goal",
    })
    goal_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/projects/{proj_id}/goals/{goal_id}", headers=headers)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/projects/{proj_id}/goals/{goal_id}", headers=headers)
    assert get_resp.status_code == 404


def test_6_invalid_goal_status_priority(client):
    """6. Invalid status or priority value triggers 422 Unprocessable Entity."""
    headers = register_user(client, "goal_validator@continuo.ai")
    proj_id = create_project(client, headers)

    # Invalid status
    bad_status = client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Invalid Status",
        "status": "non_existent_status",
    })
    assert bad_status.status_code == 422

    # Invalid priority
    bad_priority = client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={
        "title": "Invalid Priority",
        "priority": "super_duper_urgent",
    })
    assert bad_priority.status_code == 422


def test_7_goal_cross_user_rejection(client):
    """7. User B cannot read, update, or delete User A's goal."""
    headers_a = register_user(client, "owner_a@continuo.ai")
    headers_b = register_user(client, "intruder_b@continuo.ai")

    proj_a = create_project(client, headers_a, "User A Project")
    goal_resp = client.post(f"/api/v1/projects/{proj_a}/goals", headers=headers_a, json={
        "title": "Confidential Goal A",
    })
    goal_a_id = goal_resp.json()["id"]

    # User B cannot GET
    get_resp = client.get(f"/api/v1/projects/{proj_a}/goals/{goal_a_id}", headers=headers_b)
    assert get_resp.status_code == 403

    # User B cannot PATCH
    patch_resp = client.patch(f"/api/v1/projects/{proj_a}/goals/{goal_a_id}", headers=headers_b, json={
        "title": "Compromised Goal",
    })
    assert patch_resp.status_code == 403

    # User B cannot DELETE
    del_resp = client.delete(f"/api/v1/projects/{proj_a}/goals/{goal_a_id}", headers=headers_b)
    assert del_resp.status_code == 403


def test_8_goal_cross_project_rejection(client):
    """8. Goal A from Project A cannot be accessed through Project B even by same owner."""
    headers = register_user(client, "multi_proj_owner@continuo.ai")
    proj_1 = create_project(client, headers, "Project One")
    proj_2 = create_project(client, headers, "Project Two")

    goal_resp = client.post(f"/api/v1/projects/{proj_1}/goals", headers=headers, json={
        "title": "Project 1 Goal",
    })
    goal_id = goal_resp.json()["id"]

    # Access through Project 2 must return 404 (does not exist in Project 2)
    cross_get = client.get(f"/api/v1/projects/{proj_2}/goals/{goal_id}", headers=headers)
    assert cross_get.status_code == 404

    cross_patch = client.patch(f"/api/v1/projects/{proj_2}/goals/{goal_id}", headers=headers, json={
        "title": "Tampered",
    })
    assert cross_patch.status_code == 404

    cross_del = client.delete(f"/api/v1/projects/{proj_2}/goals/{goal_id}", headers=headers)
    assert cross_del.status_code == 404


# =============================================================================
# DECISIONS API TESTS
# =============================================================================

def test_9_create_decision(client):
    """9. Create architectural decision."""
    headers = register_user(client, "decision_architect@continuo.ai")
    proj_id = create_project(client, headers)

    resp = client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={
        "title": "Adopt SQLite and PostgreSQL Dual Persistence",
        "description": "Support zero-setup local storage with seamless PostgreSQL production migration.",
        "rationale": "Enables instant local developer evaluation while offering cloud scalability.",
        "category": "database",
        "status": "accepted",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Adopt SQLite and PostgreSQL Dual Persistence"
    assert data["category"] == "database"
    assert data["status"] == "accepted"
    assert data["superseded_by_id"] is None


def test_10_update_decision(client):
    """10. Update decision attributes."""
    headers = register_user(client, "decision_editor@continuo.ai")
    proj_id = create_project(client, headers)

    create_resp = client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={
        "title": "Initial Decision",
        "category": "architecture",
        "status": "under_review",
    })
    dec_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/v1/projects/{proj_id}/decisions/{dec_id}", headers=headers, json={
        "status": "accepted",
        "rationale": "Consensus reached after team review.",
    })
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "accepted"
    assert patch_resp.json()["rationale"] == "Consensus reached after team review."


def test_11_supersede_decision(client):
    """11. Supersede Decision A with Decision B."""
    headers = register_user(client, "decision_super_11@continuo.ai")
    proj_id = create_project(client, headers)

    dec_a = client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={
        "title": "Use Webpack 4",
        "status": "accepted",
        "category": "tooling",
    }).json()

    dec_b = client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={
        "title": "Migrate to Vite",
        "status": "accepted",
        "category": "tooling",
        "rationale": "Significantly faster HMR and modern ESM bundling.",
    }).json()

    patch_resp = client.patch(f"/api/v1/projects/{proj_id}/decisions/{dec_a['id']}", headers=headers, json={
        "status": "superseded",
        "superseded_by_id": dec_b["id"],
    })
    assert patch_resp.status_code == 200
    updated_a = patch_resp.json()
    assert updated_a["status"] == "superseded"
    assert updated_a["superseded_by_id"] == dec_b["id"]


def test_12_preserve_historical_decision(client):
    """12. Preserve historical decision when superseded (not deleted, still queryable)."""
    headers = register_user(client, "decision_history_12@continuo.ai")
    proj_id = create_project(client, headers)

    dec_a = client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={
        "title": "Old Decision to Preserve",
        "status": "accepted",
    }).json()

    dec_b = client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={
        "title": "New Decision",
        "status": "accepted",
    }).json()

    # Supersede Decision A
    client.patch(f"/api/v1/projects/{proj_id}/decisions/{dec_a['id']}", headers=headers, json={
        "status": "superseded",
        "superseded_by_id": dec_b["id"],
    })

    # Verify Decision A is still present and readable
    get_a = client.get(f"/api/v1/projects/{proj_id}/decisions/{dec_a['id']}", headers=headers)
    assert get_a.status_code == 200
    assert get_a.json()["id"] == dec_a["id"]
    assert get_a.json()["status"] == "superseded"

    # Verify listing includes both decisions
    list_resp = client.get(f"/api/v1/projects/{proj_id}/decisions", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2


def test_13_reject_cross_project_supersession(client):
    """13. Reject supersession referencing a decision in a different project."""
    headers = register_user(client, "cross_super_user@continuo.ai")
    proj_1 = create_project(client, headers, "Project 1")
    proj_2 = create_project(client, headers, "Project 2")

    dec_p1 = client.post(f"/api/v1/projects/{proj_1}/decisions", headers=headers, json={
        "title": "Project 1 Choice",
    }).json()

    dec_p2 = client.post(f"/api/v1/projects/{proj_2}/decisions", headers=headers, json={
        "title": "Project 2 Choice",
    }).json()

    # Attempt to supersede Decision in Project 1 with Decision from Project 2
    bad_supersede = client.patch(f"/api/v1/projects/{proj_1}/decisions/{dec_p1['id']}", headers=headers, json={
        "status": "superseded",
        "superseded_by_id": dec_p2["id"],
    })
    assert bad_supersede.status_code == 400
    assert "Replacement decision must belong to the same project" in bad_supersede.json()["detail"]


def test_14_decision_cross_user_protection(client):
    """14. User B cannot access or modify User A's decisions."""
    headers_a = register_user(client, "dec_owner_a@continuo.ai")
    headers_b = register_user(client, "dec_intruder_b@continuo.ai")

    proj_a = create_project(client, headers_a)
    dec_a = client.post(f"/api/v1/projects/{proj_a}/decisions", headers=headers_a, json={
        "title": "Proprietary Architecture Decision",
    }).json()

    # User B GET rejected
    assert client.get(f"/api/v1/projects/{proj_a}/decisions/{dec_a['id']}", headers=headers_b).status_code == 403
    # User B PATCH rejected
    assert client.patch(f"/api/v1/projects/{proj_a}/decisions/{dec_a['id']}", headers=headers_b, json={"title": "Hacked"}).status_code == 403
    # User B DELETE rejected
    assert client.delete(f"/api/v1/projects/{proj_a}/decisions/{dec_a['id']}", headers=headers_b).status_code == 403


# =============================================================================
# TASKS API TESTS
# =============================================================================

def test_15_create_task(client):
    """15. Create task."""
    headers = register_user(client, "task_user@continuo.ai")
    proj_id = create_project(client, headers)

    resp = client.post(f"/api/v1/projects/{proj_id}/tasks", headers=headers, json={
        "title": "Implement JWT rotation endpoint",
        "description": "Add refresh token verification and revocation check.",
        "status": "todo",
        "priority": "high",
    })
    assert resp.status_code == 201
    task = resp.json()
    assert task["title"] == "Implement JWT rotation endpoint"
    assert task["status"] == "todo"
    assert task["completed_at"] is None


def test_16_update_task(client):
    """16. Update task title and description."""
    headers = register_user(client, "task_updater@continuo.ai")
    proj_id = create_project(client, headers)

    task = client.post(f"/api/v1/projects/{proj_id}/tasks", headers=headers, json={
        "title": "Base Task",
    }).json()

    resp = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "title": "Refined Task Title",
        "priority": "critical",
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Refined Task Title"
    assert resp.json()["priority"] == "critical"


def test_17_task_lifecycle_todo_to_in_progress(client):
    """17. todo → in_progress transition."""
    headers = register_user(client, "task_17@continuo.ai")
    proj_id = create_project(client, headers)

    task = client.post(f"/api/v1/projects/{proj_id}/tasks", headers=headers, json={
        "title": "Task 17",
        "status": "todo",
    }).json()

    step = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "status": "in_progress",
    }).json()
    assert step["status"] == "in_progress"
    assert step["completed_at"] is None


def test_18_task_lifecycle_in_progress_to_completed(client):
    """18. in_progress → completed transition."""
    headers = register_user(client, "task_18@continuo.ai")
    proj_id = create_project(client, headers)

    task = client.post(f"/api/v1/projects/{proj_id}/tasks", headers=headers, json={
        "title": "Task 18",
        "status": "in_progress",
    }).json()

    step = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "status": "completed",
    }).json()
    assert step["status"] == "completed"


def test_19_task_completed_at_populated(client):
    """19. completed_at is automatically populated when status moves to completed."""
    headers = register_user(client, "task_19@continuo.ai")
    proj_id = create_project(client, headers)

    task = client.post(f"/api/v1/projects/{proj_id}/tasks", headers=headers, json={
        "title": "Task 19",
        "status": "todo",
    }).json()
    assert task["completed_at"] is None

    step = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "status": "completed",
    }).json()
    assert step["completed_at"] is not None


def test_20_task_completed_to_in_progress_clears_completed_at(client):
    """20. completed → in_progress (or todo/blocked) clears completed_at."""
    headers = register_user(client, "task_20@continuo.ai")
    proj_id = create_project(client, headers)

    task = client.post(f"/api/v1/projects/{proj_id}/tasks", headers=headers, json={
        "title": "Task 20",
        "status": "completed",
    }).json()
    assert task["completed_at"] is not None

    # Move back to in_progress
    step1 = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "status": "in_progress",
    }).json()
    assert step1["status"] == "in_progress"
    assert step1["completed_at"] is None

    # Move back to completed
    step2 = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "status": "completed",
    }).json()
    assert step2["completed_at"] is not None

    # Move to blocked
    step3 = client.patch(f"/api/v1/projects/{proj_id}/tasks/{task['id']}", headers=headers, json={
        "status": "blocked",
    }).json()
    assert step3["status"] == "blocked"
    assert step3["completed_at"] is None



def test_21_task_cross_user_protection(client):
    """21. User B cannot access or modify User A's tasks."""
    headers_a = register_user(client, "task_a@continuo.ai")
    headers_b = register_user(client, "task_b@continuo.ai")

    proj_a = create_project(client, headers_a)
    task_a = client.post(f"/api/v1/projects/{proj_a}/tasks", headers=headers_a, json={
        "title": "User A Task",
    }).json()

    assert client.get(f"/api/v1/projects/{proj_a}/tasks/{task_a['id']}", headers=headers_b).status_code == 403
    assert client.patch(f"/api/v1/projects/{proj_a}/tasks/{task_a['id']}", headers=headers_b, json={"status": "completed"}).status_code == 403
    assert client.delete(f"/api/v1/projects/{proj_a}/tasks/{task_a['id']}", headers=headers_b).status_code == 403


# =============================================================================
# TECHNICAL STATE API TESTS
# =============================================================================

def test_22_create_technical_state(client):
    """22. Create technical state key-value record."""
    headers = register_user(client, "tech_creator@continuo.ai")
    proj_id = create_project(client, headers)

    resp = client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={
        "category": "renderer",
        "key": "engine",
        "value": "Three.js",
    })
    assert resp.status_code == 201
    state = resp.json()
    assert state["category"] == "renderer"
    assert state["key"] == "engine"
    assert state["value"] == "Three.js"
    assert state["project_id"] == proj_id


def test_23_get_technical_state(client):
    """23. Get technical state by ID."""
    headers = register_user(client, "tech_getter@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={
        "category": "database",
        "key": "orm",
        "value": "SQLAlchemy",
    }).json()

    resp = client.get(f"/api/v1/projects/{proj_id}/technical-state/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["key"] == "orm"
    assert resp.json()["value"] == "SQLAlchemy"


def test_24_update_technical_state(client):
    """24. Update technical state value."""
    headers = register_user(client, "tech_updater@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={
        "category": "runtime",
        "key": "version",
        "value": "Python 3.12",
    }).json()

    patch_resp = client.patch(f"/api/v1/projects/{proj_id}/technical-state/{created['id']}", headers=headers, json={
        "value": "Python 3.14",
    })
    assert patch_resp.status_code == 200
    assert patch_resp.json()["value"] == "Python 3.14"


def test_25_delete_technical_state(client):
    """25. Delete technical state."""
    headers = register_user(client, "tech_deleter@continuo.ai")
    proj_id = create_project(client, headers)

    created = client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={
        "category": "cache",
        "key": "provider",
        "value": "Redis",
    }).json()

    del_resp = client.delete(f"/api/v1/projects/{proj_id}/technical-state/{created['id']}", headers=headers)
    assert del_resp.status_code == 204

    assert client.get(f"/api/v1/projects/{proj_id}/technical-state/{created['id']}", headers=headers).status_code == 404


def test_26_duplicate_category_key_conflict_409(client):
    """26. Duplicate (project_id, category, key) returns clean 409 Conflict without SQL leakage."""
    headers = register_user(client, "tech_conflict@continuo.ai")
    proj_id = create_project(client, headers)

    # First record succeeds
    resp1 = client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={
        "category": "renderer",
        "key": "engine",
        "value": "Three.js",
    })
    assert resp1.status_code == 201

    # Duplicate record triggers 409 Conflict
    resp2 = client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={
        "category": "renderer",
        "key": "engine",
        "value": "Babylon.js",
    })
    assert resp2.status_code == 409
    data = resp2.json()
    assert "already exists" in data["detail"]
    assert "SELECT" not in data["detail"]
    assert "IntegrityError" not in data["detail"]


def test_27_technical_state_cross_user_protection(client):
    """27. User B cannot access User A's technical state."""
    headers_a = register_user(client, "tech_a@continuo.ai")
    headers_b = register_user(client, "tech_b@continuo.ai")

    proj_a = create_project(client, headers_a)
    created_a = client.post(f"/api/v1/projects/{proj_a}/technical-state", headers=headers_a, json={
        "category": "secret_config",
        "key": "cluster_size",
        "value": "64",
    }).json()

    assert client.get(f"/api/v1/projects/{proj_a}/technical-state/{created_a['id']}", headers=headers_b).status_code == 403
    assert client.patch(f"/api/v1/projects/{proj_a}/technical-state/{created_a['id']}", headers=headers_b, json={"value": "1"}).status_code == 403
    assert client.delete(f"/api/v1/projects/{proj_a}/technical-state/{created_a['id']}", headers=headers_b).status_code == 403


# =============================================================================
# GENERAL & EDGE CASE TESTS
# =============================================================================

def test_28_authentication_required(client):
    """28. Unauthenticated requests are rejected with 401 Unauthorized."""
    proj_id = "some-random-uuid"

    assert client.get(f"/api/v1/projects/{proj_id}/goals").status_code == 401
    assert client.post(f"/api/v1/projects/{proj_id}/goals", json={"title": "Test"}).status_code == 401

    assert client.get(f"/api/v1/projects/{proj_id}/decisions").status_code == 401
    assert client.post(f"/api/v1/projects/{proj_id}/decisions", json={"title": "Test"}).status_code == 401

    assert client.get(f"/api/v1/projects/{proj_id}/tasks").status_code == 401
    assert client.post(f"/api/v1/projects/{proj_id}/tasks", json={"title": "Test"}).status_code == 401

    assert client.get(f"/api/v1/projects/{proj_id}/technical-state").status_code == 401
    assert client.post(f"/api/v1/projects/{proj_id}/technical-state", json={"category": "c", "key": "k", "value": "v"}).status_code == 401


def test_29_invalid_project_access_404(client):
    """29. Accessing a non-existent project returns 404 Not Found."""
    headers = register_user(client, "valid_user_ghost_project@continuo.ai")
    ghost_proj = "00000000-0000-0000-0000-000000000000"

    assert client.get(f"/api/v1/projects/{ghost_proj}/goals", headers=headers).status_code == 404
    assert client.post(f"/api/v1/projects/{ghost_proj}/goals", headers=headers, json={"title": "X"}).status_code == 404
    assert client.get(f"/api/v1/projects/{ghost_proj}/decisions", headers=headers).status_code == 404
    assert client.get(f"/api/v1/projects/{ghost_proj}/tasks", headers=headers).status_code == 404
    assert client.get(f"/api/v1/projects/{ghost_proj}/technical-state", headers=headers).status_code == 404


def test_30_malformed_payload_validation_422(client):
    """30. Malformed payload returns 422 Unprocessable Entity."""
    headers = register_user(client, "malformed_tester@continuo.ai")
    proj_id = create_project(client, headers)

    # Empty title
    assert client.post(f"/api/v1/projects/{proj_id}/goals", headers=headers, json={"title": ""}).status_code == 422
    # Missing required category/key in technical state
    assert client.post(f"/api/v1/projects/{proj_id}/technical-state", headers=headers, json={"value": "missing cat and key"}).status_code == 422
    # Missing title in decisions
    assert client.post(f"/api/v1/projects/{proj_id}/decisions", headers=headers, json={"description": "no title"}).status_code == 422


def test_source_session_validation(client, db_session):
    """Validate source_session_id: valid session succeeds, foreign or missing session returns 400."""
    from backend.models import Conversation

    headers_1 = register_user(client, "session_owner_1@continuo.ai")
    headers_2 = register_user(client, "session_owner_2@continuo.ai")

    proj_1 = create_project(client, headers_1, "Project 1")
    proj_2 = create_project(client, headers_2, "Project 2")

    # 1. Capture a session in Project 1 to create a conversation
    cap_resp = client.post("/api/v1/context/capture", headers=headers_1, json={
        "project_id": proj_1,
        "provider": "chatgpt",
        "raw_transcript": "User: Refactor auth. Requirement: JWT.",
        "title": "Auth Dialogue",
    })
    assert cap_resp.status_code == 201

    conv_1 = db_session.query(Conversation).filter(Conversation.project_id == proj_1).first()
    assert conv_1 is not None

    # 2. Capture a session in Project 2
    cap_resp_2 = client.post("/api/v1/context/capture", headers=headers_2, json={
        "project_id": proj_2,
        "provider": "claude",
        "raw_transcript": "User: Design system. Requirement: Glassmorphism.",
        "title": "Design Dialogue",
    })
    assert cap_resp_2.status_code == 201

    conv_2 = db_session.query(Conversation).filter(Conversation.project_id == proj_2).first()
    assert conv_2 is not None

    # 3. Create goal with non-existent session -> 400 Bad Request
    ghost_session = client.post(f"/api/v1/projects/{proj_1}/goals", headers=headers_1, json={
        "title": "Goal with ghost session",
        "source_session_id": "00000000-0000-0000-0000-000000000000",
    })
    assert ghost_session.status_code == 400
    assert "does not exist" in ghost_session.json()["detail"]

    # 4. Attempt to link Project 1 Goal to Project 2 Session -> 400 Bad Request
    cross_session = client.post(f"/api/v1/projects/{proj_1}/goals", headers=headers_1, json={
        "title": "Goal with cross project session",
        "source_session_id": conv_2.id,
    })
    assert cross_session.status_code == 400
    assert "does not belong to this project" in cross_session.json()["detail"]

    # 5. Successfully link Project 1 Goal to Project 1 Session -> 201 Created
    valid_goal = client.post(f"/api/v1/projects/{proj_1}/goals", headers=headers_1, json={
        "title": "Goal with valid session",
        "source_session_id": conv_1.id,
    })
    assert valid_goal.status_code == 201
    assert valid_goal.json()["source_session_id"] == conv_1.id

