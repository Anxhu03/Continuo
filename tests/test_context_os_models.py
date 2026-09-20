"""
CONTINUO — Tests for Persistent Context OS Data Models (Phase 9.2)
Validates ContextGoal, ContextDecision, ContextTask, ContextTechnicalState,
supersession, validation guards, ownership isolation, cascade deletion, and Alembic migrations.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command
from pathlib import Path

from backend.models import (
    User,
    Project,
    ContextGoal,
    ContextDecision,
    ContextTask,
    ContextTechnicalState,
    generate_uuid,
    utc_now,
)
from backend.services.auth import hash_password, create_access_token


def create_test_user(db_session, email="developer@continuo.ai"):
    user = User(
        email=email,
        hashed_password=hash_password("ContinuoTestPass123!"),
        full_name="Continuo Developer",
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_project(db_session, user, name="Portfolio 2.0"):
    project = Project(
        user_id=user.id,
        name=name,
        description="Next-gen 3D portfolio project memory layer.",
        current_version="v1.0",
        health_score=90.0,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


# -----------------------------------------------------------------------------
# 1. ContextGoal Creation & Validation
# -----------------------------------------------------------------------------
def test_context_goal_creation_and_validation(db_session):
    user = create_test_user(db_session, "goal_test@continuo.ai")
    project = create_test_project(db_session, user)

    goal = ContextGoal(
        project_id=project.id,
        user_id=user.id,
        title="Implement 3D character hero viewer",
        description="Interactive glTF character with orbit controls and bloom effect.",
        category="objective",
        status="active",
        priority="critical",
    )
    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)

    assert goal.id is not None
    assert goal.project_id == project.id
    assert goal.user_id == user.id
    assert goal.title == "Implement 3D character hero viewer"
    assert goal.status == "active"
    assert goal.priority == "critical"
    assert goal.created_at is not None

    # Relationship verification
    assert goal in project.goals
    assert goal in user.goals

    # Validation guards
    with pytest.raises(ValueError, match="Invalid goal status"):
        ContextGoal(
            project_id=project.id,
            user_id=user.id,
            title="Invalid Status Goal",
            status="non_existent_status",
        )

    with pytest.raises(ValueError, match="Invalid priority"):
        ContextGoal(
            project_id=project.id,
            user_id=user.id,
            title="Invalid Priority Goal",
            priority="ultra_high",
        )


# -----------------------------------------------------------------------------
# 2. ContextDecision Creation & Validation
# -----------------------------------------------------------------------------
def test_context_decision_creation_and_validation(db_session):
    user = create_test_user(db_session, "decision_test@continuo.ai")
    project = create_test_project(db_session, user)

    decision = ContextDecision(
        project_id=project.id,
        user_id=user.id,
        title="Use Three.js with glTF Loader",
        description="Standardized 3D rendering pipeline for the avatar.",
        rationale="Superior community ecosystem and lighter bundle size than Babylon.",
        category="architecture",
        status="accepted",
    )
    db_session.add(decision)
    db_session.commit()
    db_session.refresh(decision)

    assert decision.id is not None
    assert decision.title == "Use Three.js with glTF Loader"
    assert decision.status == "accepted"
    assert decision.rationale is not None

    # Relationship verification
    assert decision in project.decisions
    assert decision in user.decisions

    # Validation guard
    with pytest.raises(ValueError, match="Invalid decision status"):
        ContextDecision(
            project_id=project.id,
            user_id=user.id,
            title="Bad Status Decision",
            status="invalid_status",
        )


# -----------------------------------------------------------------------------
# 3. ContextDecision Supersession (Historical Preservation)
# -----------------------------------------------------------------------------
def test_context_decision_supersession(db_session):
    user = create_test_user(db_session, "supersede_test@continuo.ai")
    project = create_test_project(db_session, user)

    # Initial Decision A
    decision_a = ContextDecision(
        project_id=project.id,
        user_id=user.id,
        title="Use Three.js for 3D character viewport",
        description="Initial 3D rendering engine selection.",
        rationale="Rapid prototyping ease.",
        category="architecture",
        status="accepted",
    )
    db_session.add(decision_a)
    db_session.commit()
    db_session.refresh(decision_a)

    # Subsequent Decision B superseding Decision A
    decision_b = ContextDecision(
        project_id=project.id,
        user_id=user.id,
        title="Migrate to Babylon.js for WebGPU pipeline",
        description="Upgraded 3D engine to support WebGPU compute shaders.",
        rationale="Three.js lacked mature WebGPU compute shader node architecture.",
        category="architecture",
        status="accepted",
    )
    db_session.add(decision_b)
    db_session.commit()
    db_session.refresh(decision_b)

    # Mark Decision A as superseded by Decision B
    decision_a.status = "superseded"
    decision_a.superseded_by_id = decision_b.id
    db_session.commit()
    db_session.refresh(decision_a)

    # Verify Decision A is preserved in history and linked to Decision B
    assert decision_a.status == "superseded"
    assert decision_a.superseded_by_id == decision_b.id
    assert decision_a.superseded_by is not None
    assert decision_a.superseded_by.id == decision_b.id
    assert decision_a.superseded_by.title == "Migrate to Babylon.js for WebGPU pipeline"

    # Both decisions still exist in the project history
    all_decisions = (
        db_session.query(ContextDecision)
        .filter(ContextDecision.project_id == project.id)
        .all()
    )
    assert len(all_decisions) == 2


# -----------------------------------------------------------------------------
# 4. ContextTask Lifecycle
# -----------------------------------------------------------------------------
def test_context_task_lifecycle(db_session):
    user = create_test_user(db_session, "task_test@continuo.ai")
    project = create_test_project(db_session, user)

    # Create task in 'todo'
    task = ContextTask(
        project_id=project.id,
        user_id=user.id,
        title="Tune Three.js volumetric rim light intensity",
        description="Reduce bloom specular artifacts on the glass pedestal.",
        status="todo",
        priority="high",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.status == "todo"
    assert task.completed_at is None

    # Transition to 'in_progress'
    task.status = "in_progress"
    db_session.commit()
    db_session.refresh(task)
    assert task.status == "in_progress"

    # Complete task
    completion_time = utc_now()
    task.status = "completed"
    task.completed_at = completion_time
    db_session.commit()
    db_session.refresh(task)

    assert task.status == "completed"
    assert task.completed_at is not None

    # Validation guards
    with pytest.raises(ValueError, match="Invalid task status"):
        ContextTask(
            project_id=project.id,
            user_id=user.id,
            title="Invalid Status Task",
            status="finished",  # must be 'completed'
        )

    with pytest.raises(ValueError, match="Invalid priority"):
        ContextTask(
            project_id=project.id,
            user_id=user.id,
            title="Invalid Priority Task",
            priority="medium",  # must be 'normal'
        )


# -----------------------------------------------------------------------------
# 5. ContextTechnicalState Creation & Uniqueness
# -----------------------------------------------------------------------------
def test_context_technical_state_creation_and_uniqueness(db_session):
    user = create_test_user(db_session, "tech_test@continuo.ai")
    project = create_test_project(db_session, user)

    state_item = ContextTechnicalState(
        project_id=project.id,
        user_id=user.id,
        category="framework",
        key="runtime",
        value="Node.js v22",
    )
    db_session.add(state_item)
    db_session.commit()
    db_session.refresh(state_item)

    assert state_item.id is not None
    assert state_item.category == "framework"
    assert state_item.key == "runtime"
    assert state_item.value == "Node.js v22"

    # Second item in different category/key succeeds
    renderer_item = ContextTechnicalState(
        project_id=project.id,
        user_id=user.id,
        category="renderer",
        key="engine",
        value="Three.js",
    )
    db_session.add(renderer_item)
    db_session.commit()

    # Uniqueness constraint: same project_id, category, and key must fail
    duplicate_item = ContextTechnicalState(
        project_id=project.id,
        user_id=user.id,
        category="framework",
        key="runtime",
        value="Node.js v20",
    )
    db_session.add(duplicate_item)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# -----------------------------------------------------------------------------
# 6. Project Ownership & User Isolation
# -----------------------------------------------------------------------------
def test_project_ownership_isolation(db_session):
    user_a = create_test_user(db_session, "usera@continuo.ai")
    user_b = create_test_user(db_session, "userb@continuo.ai")

    proj_a = create_test_project(db_session, user_a, "Project Alpha")
    proj_b = create_test_project(db_session, user_b, "Project Beta")

    # Add items to Project Alpha (User A)
    goal_a = ContextGoal(
        project_id=proj_a.id,
        user_id=user_a.id,
        title="Alpha Goal",
    )
    decision_a = ContextDecision(
        project_id=proj_a.id,
        user_id=user_a.id,
        title="Alpha Decision",
    )
    db_session.add_all([goal_a, decision_a])
    db_session.commit()

    # Add items to Project Beta (User B)
    goal_b = ContextGoal(
        project_id=proj_b.id,
        user_id=user_b.id,
        title="Beta Goal",
    )
    decision_b = ContextDecision(
        project_id=proj_b.id,
        user_id=user_b.id,
        title="Beta Decision",
    )
    db_session.add_all([goal_b, decision_b])
    db_session.commit()

    # Assert User A only retrieves Project Alpha items
    user_a_goals = (
        db_session.query(ContextGoal)
        .filter(ContextGoal.project_id == proj_a.id, ContextGoal.user_id == user_a.id)
        .all()
    )
    assert len(user_a_goals) == 1
    assert user_a_goals[0].title == "Alpha Goal"

    # Assert User B only retrieves Project Beta items
    user_b_goals = (
        db_session.query(ContextGoal)
        .filter(ContextGoal.project_id == proj_b.id, ContextGoal.user_id == user_b.id)
        .all()
    )
    assert len(user_b_goals) == 1
    assert user_b_goals[0].title == "Beta Goal"


# -----------------------------------------------------------------------------
# 7. Cross-User Access Rejection via API Endpoints
# -----------------------------------------------------------------------------
def test_cross_user_access_rejection(client, db_session):
    user_a = create_test_user(db_session, "owner_a@continuo.ai")
    user_b = create_test_user(db_session, "intruder_b@continuo.ai")

    proj_a = create_test_project(db_session, user_a, "Owner Project")

    # User B tries to access Project A endpoints
    token_b = create_access_token(user_b.id, user_b.email)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Attempting to fetch project details
    resp = client.get(f"/api/v1/projects/{proj_a.id}", headers=headers_b)
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]

    # Attempting to delete project
    resp_del = client.delete(f"/api/v1/projects/{proj_a.id}", headers=headers_b)
    assert resp_del.status_code == 403


# -----------------------------------------------------------------------------
# 8. Project Cascade Deletion
# -----------------------------------------------------------------------------
def test_project_cascade_deletion(client, db_session):
    user = create_test_user(db_session, "cascade_user@continuo.ai")
    project = create_test_project(db_session, user, "Cascade Target")

    # Attach Context OS entities
    goal = ContextGoal(project_id=project.id, user_id=user.id, title="Cascade Goal")
    decision = ContextDecision(project_id=project.id, user_id=user.id, title="Cascade Decision")
    task = ContextTask(project_id=project.id, user_id=user.id, title="Cascade Task")
    tech = ContextTechnicalState(project_id=project.id, user_id=user.id, category="db", key="type", value="sqlite")

    db_session.add_all([goal, decision, task, tech])
    db_session.commit()

    # Verify records exist
    assert db_session.query(ContextGoal).filter(ContextGoal.project_id == project.id).count() == 1
    assert db_session.query(ContextDecision).filter(ContextDecision.project_id == project.id).count() == 1
    assert db_session.query(ContextTask).filter(ContextTask.project_id == project.id).count() == 1
    assert db_session.query(ContextTechnicalState).filter(ContextTechnicalState.project_id == project.id).count() == 1

    # Delete project via API with owner authentication
    token = create_access_token(user.id, user.email)
    headers = {"Authorization": f"Bearer {token}"}
    del_resp = client.delete(f"/api/v1/projects/{project.id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify all child Context OS records were cleanly purged
    assert db_session.query(ContextGoal).filter(ContextGoal.project_id == project.id).count() == 0
    assert db_session.query(ContextDecision).filter(ContextDecision.project_id == project.id).count() == 0
    assert db_session.query(ContextTask).filter(ContextTask.project_id == project.id).count() == 0
    assert db_session.query(ContextTechnicalState).filter(ContextTechnicalState.project_id == project.id).count() == 0
    assert db_session.query(Project).filter(Project.id == project.id).count() == 0


# -----------------------------------------------------------------------------
# 9. & 10. Migration Upgrade & Downgrade
# -----------------------------------------------------------------------------
def test_alembic_migration_upgrade_and_downgrade():
    alembic_ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))

    # Test downgrade to 0001
    command.downgrade(alembic_cfg, "0001_initial_schema")

    # Test upgrade back to head (0002_context_os_entities)
    command.upgrade(alembic_cfg, "head")
