"""
CONTINUO — Tests for Context Extraction Intelligence (Phase 9.5)
Validates structured entity extraction, confidence classification, tentative decision flagging,
design context, visual reference detection & associations, cross-tenant security,
deduplication, contradiction detection, secret sanitization, and backward compatibility.
"""

import io
import pytest
from PIL import Image

from backend.models import (
    User,
    Project,
    ContextGoal,
    ContextDecision,
    ContextTask,
    ContextTechnicalState,
    ContextImage,
    Conversation,
    ContextPackage,
)
from backend.services.context_engine import ContextEngine
from backend.services.context_extraction import ContextExtractionService
from backend.services.handoff_generator import HandoffService


def make_test_png() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGBA", (100, 100), color=(50, 100, 150, 255))
    img.save(buf, format="PNG")
    return buf.getvalue()


def register_user(client, email: str, password: str = "SecurePass123!", name: str = "Test User"):
    resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name,
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_project(client, headers: dict, name: str = "Continuo Test OS"):
    resp = client.post("/api/v1/projects", headers=headers, json={
        "name": name,
        "description": "Extraction test project",
        "initial_objective": "Test Context OS extraction",
    })
    assert resp.status_code == 201
    return resp.json()["id"]


# =============================================================================
# 1. EXPLICIT GOAL EXTRACTION
# =============================================================================

def test_1_explicit_goal_extraction():
    transcript = """
    User: I want to build an interactive 3D portfolio with Three.js.
    Requirement: Must support 60 FPS rendering on mobile devices.
    Constraint: Never load uncompressed textures over 2MB.
    """
    res = ContextExtractionService.extract(transcript)
    assert len(res.goals) >= 3
    goal_types = [g.category for g in res.goals]
    assert "goal" in goal_types
    assert "requirement" in goal_types
    assert "constraint" in goal_types
    assert any("portfolio" in g.title.lower() for g in res.goals)
    assert any("60 fps" in g.title.lower() for g in res.goals)
    assert any(g.confidence >= 0.85 for g in res.goals)
    assert all(g.explicit for g in res.goals)


# =============================================================================
# 2. EXPLICIT DECISION EXTRACTION
# =============================================================================

def test_2_explicit_decision_extraction():
    transcript = """
    Decision: We decided to use Three.js for client-side rendering.
    Decision: Standardized on PostgreSQL with SQLAlchemy for persistent storage.
    """
    res = ContextExtractionService.extract(transcript)
    assert len(res.decisions) == 2
    assert all(d.status == "accepted" for d in res.decisions)
    assert all(d.explicit for d in res.decisions)
    assert all(d.confidence >= 0.90 for d in res.decisions)
    categories = [d.category for d in res.decisions]
    assert "renderer" in categories or "design_system" in categories
    assert "database" in categories


# =============================================================================
# 3. AMBIGUOUS / TENTATIVE DECISION HANDLING
# =============================================================================

def test_3_ambiguous_decision_handling():
    transcript = """
    User: Maybe we should use Three.js for the 3D graphics.
    User: I like this design with the dark glass cards.
    """
    res = ContextExtractionService.extract(transcript)
    assert len(res.decisions) >= 1
    # Tentative statements should be under_review and have lower confidence
    tentative = [d for d in res.decisions if d.status == "under_review"]
    assert len(tentative) >= 1
    assert tentative[0].explicit is False
    assert tentative[0].confidence < 0.60


# =============================================================================
# 4. TASK EXTRACTION
# =============================================================================

def test_4_task_extraction():
    transcript = """
    Todo: Fix the character animation transition loop.
    Completed: Setup Vite bundler and Tailwind configuration.
    Task: Fix the demonstrated UI issue on mobile Safari.
    """
    res = ContextExtractionService.extract(transcript)
    assert len(res.tasks) >= 3
    statuses = [t.status for t in res.tasks]
    assert "todo" in statuses
    assert "completed" in statuses
    assert any("animation" in t.title.lower() for t in res.tasks)
    assert any("ui issue" in t.title.lower() for t in res.tasks)


# =============================================================================
# 5. TECHNICAL STATE EXTRACTION
# =============================================================================

def test_5_technical_state_extraction():
    transcript = """
    The frontend is React and Three.js with Tailwind CSS.
    The backend is FastAPI with PostgreSQL and Redis cache broker.
    """
    res = ContextExtractionService.extract(transcript)
    assert len(res.technical_states) >= 4
    keys = [s.key for s in res.technical_states]
    assert "frontend" in keys or "3d_engine" in keys
    assert "backend" in keys
    assert "primary_db" in keys


# =============================================================================
# 6. PROJECT STATE EXTRACTION
# =============================================================================

def test_6_project_state_extraction():
    transcript = """
    Status: The GLB character has already been integrated and shaders are compiled.
    """
    res = ContextExtractionService.extract(transcript)
    assert "glb character" in res.project_state.lower() or "integrated" in res.project_state.lower()


# =============================================================================
# 7. EXPLICIT DESIGN CONTEXT EXTRACTION
# =============================================================================

def test_7_explicit_design_context_extraction():
    transcript = """
    Make my portfolio look like this.
    Use a dark glass aesthetic with large 3D visual and minimal layout.
    """
    res = ContextExtractionService.extract(transcript)
    assert len(res.design_context) >= 1
    assert any("dark glass" in dc.lower() or "minimal layout" in dc.lower() for dc in res.design_context)


# =============================================================================
# 8. VISUAL REFERENCE DETECTION FROM CONVERSATION
# =============================================================================

def test_8_visual_reference_detection_from_conversation():
    # 8a. Design reference
    res_design = ContextExtractionService.extract("Make my portfolio look like this screenshot.")
    assert len(res_design.visual_references) == 1
    assert res_design.visual_references[0].detected_role == "design_reference"

    # 8b. Character reference
    res_char = ContextExtractionService.extract("Use this character as the main portfolio character.")
    assert len(res_char.visual_references) == 1
    assert res_char.visual_references[0].detected_role == "character_reference"

    # 8c. UI bug screenshot
    res_bug = ContextExtractionService.extract("This screenshot shows the bug I'm talking about.")
    assert len(res_bug.visual_references) == 1
    assert res_bug.visual_references[0].detected_role == "ui_screenshot"


# =============================================================================
# 9. IMAGE ASSOCIATION WITH EXISTING CONTEXT IMAGE
# =============================================================================

def test_9_image_association(db_session):
    user = User(email="vis_test@continuo.ai", hashed_password="pw", full_name="Vis User")
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Vis Project")
    db_session.add(project)
    db_session.flush()

    image = ContextImage(
        project_id=project.id,
        user_id=user.id,
        original_filename="portfolio-mockup.png",
        storage_key=f"projects/{project.id}/assets/test.png",
        mime_type="image/png",
        image_format="png",
        file_size=1024,
        checksum_sha256="abc123456",
        image_type="other",
        description="Initial upload"
    )
    db_session.add(image)
    db_session.commit()

    transcript = "Make my portfolio look like this portfolio-mockup.png screenshot with dark glass."
    res = ContextExtractionService.extract(
        raw_text=transcript,
        project_id=project.id,
        current_user_id=user.id,
        db=db_session
    )
    assert len(res.visual_references) == 1
    assert res.visual_references[0].detected_image_id == image.id
    assert res.visual_references[0].detected_role == "design_reference"


# =============================================================================
# 10. IMAGE + DECISION ASSOCIATION
# =============================================================================

def test_10_image_decision_association(db_session):
    user = User(email="img_dec@continuo.ai", hashed_password="pw", full_name="Img Dec")
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Decision Image Project")
    db_session.add(project)
    db_session.flush()

    image = ContextImage(
        project_id=project.id,
        user_id=user.id,
        original_filename="design-ref.png",
        storage_key=f"projects/{project.id}/assets/dref.png",
        mime_type="image/png",
        image_format="png",
        file_size=1024,
        checksum_sha256="hash123",
        image_type="other"
    )
    db_session.add(image)
    db_session.commit()

    transcript = """
    Decision: We decided to use dark glass aesthetic for the entire design system.
    This screenshot design-ref.png is the visual reference for the theme.
    """
    res = ContextExtractionService.extract(
        raw_text=transcript,
        project_id=project.id,
        current_user_id=user.id,
        db=db_session
    )
    counts = ContextExtractionService.persist_extracted_context(
        extracted=res,
        project=project,
        user=user,
        db=db_session
    )
    assert counts["decisions"] >= 1
    assert counts["visual_associations"] >= 1

    db_session.refresh(image)
    assert len(image.get_list("associated_decision_ids")) >= 1
    assert image.image_type == "design_reference"


# =============================================================================
# 11. IMAGE + GOAL ASSOCIATION
# =============================================================================

def test_11_image_goal_association(db_session):
    user = User(email="img_goal@continuo.ai", hashed_password="pw", full_name="Img Goal")
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Goal Image Project")
    db_session.add(project)
    db_session.flush()

    image = ContextImage(
        project_id=project.id,
        user_id=user.id,
        original_filename="mascot.png",
        storage_key=f"projects/{project.id}/assets/mascot.png",
        mime_type="image/png",
        image_format="png",
        file_size=1024,
        checksum_sha256="hash_mascot",
        image_type="other"
    )
    db_session.add(image)
    db_session.commit()

    transcript = """
    Goal: Build an interactive 3D character experience.
    Use this mascot.png character as the main portfolio character.
    """
    res = ContextExtractionService.extract(
        raw_text=transcript,
        project_id=project.id,
        current_user_id=user.id,
        db=db_session
    )
    counts = ContextExtractionService.persist_extracted_context(
        extracted=res,
        project=project,
        user=user,
        db=db_session
    )
    assert counts["goals"] >= 1
    assert counts["visual_associations"] >= 1

    db_session.refresh(image)
    assert len(image.get_list("associated_context_ids")) >= 1
    assert image.image_type == "character_reference"


# =============================================================================
# 12. IMAGE + TASK ASSOCIATION (BUG SCREENSHOT)
# =============================================================================

def test_12_image_task_association(db_session):
    user = User(email="img_task@continuo.ai", hashed_password="pw", full_name="Img Task")
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Task Image Project")
    db_session.add(project)
    db_session.flush()

    image = ContextImage(
        project_id=project.id,
        user_id=user.id,
        original_filename="error-dialog.png",
        storage_key=f"projects/{project.id}/assets/err.png",
        mime_type="image/png",
        image_format="png",
        file_size=1024,
        checksum_sha256="err_hash",
        image_type="other"
    )
    db_session.add(image)
    db_session.commit()

    transcript = """
    This screenshot error-dialog.png shows the bug I'm talking about.
    Task: Fix the demonstrated UI issue on Safari.
    """
    res = ContextExtractionService.extract(
        raw_text=transcript,
        project_id=project.id,
        current_user_id=user.id,
        db=db_session
    )
    counts = ContextExtractionService.persist_extracted_context(
        extracted=res,
        project=project,
        user=user,
        db=db_session
    )
    assert counts["tasks"] >= 1
    assert counts["visual_associations"] >= 1

    db_session.refresh(image)
    assert len(image.get_list("associated_context_ids")) >= 1
    assert image.image_type == "ui_screenshot"


# =============================================================================
# 13. FOREIGN IMAGE ASSOCIATION REJECTION (TENANT ISOLATION)
# =============================================================================

def test_13_foreign_image_association_rejection(db_session):
    user1 = User(email="u1_img@continuo.ai", hashed_password="pw", full_name="U1")
    user2 = User(email="u2_img@continuo.ai", hashed_password="pw", full_name="U2")
    db_session.add_all([user1, user2])
    db_session.flush()

    proj1 = Project(user_id=user1.id, name="Proj 1")
    proj2 = Project(user_id=user2.id, name="Proj 2")
    db_session.add_all([proj1, proj2])
    db_session.flush()

    # Image belonging to User 2 / Proj 2
    foreign_img = ContextImage(
        project_id=proj2.id,
        user_id=user2.id,
        original_filename="secret.png",
        storage_key=f"projects/{proj2.id}/assets/sec.png",
        mime_type="image/png",
        image_format="png",
        file_size=1024,
        checksum_sha256="secret_hash",
        image_type="other"
    )
    db_session.add(foreign_img)
    db_session.commit()

    # User 1 tries to associate User 2's image
    transcript = f"Here is our screenshot {foreign_img.id} for the design reference."
    res = ContextExtractionService.extract(
        raw_text=transcript,
        project_id=proj1.id,
        current_user_id=user1.id,
        db=db_session
    )
    # The foreign image should NOT be matched to user1's project
    assert res.visual_references[0].detected_image_id is None

    # Even if forcefully injected in result, persist_extracted_context must reject it
    res.visual_references[0].detected_image_id = foreign_img.id
    counts = ContextExtractionService.persist_extracted_context(
        extracted=res,
        project=proj1,
        user=user1,
        db=db_session
    )
    assert counts["visual_associations"] == 0

    db_session.refresh(foreign_img)
    assert len(foreign_img.get_list("associated_context_ids")) == 0
    assert len(foreign_img.get_list("associated_decision_ids")) == 0


# =============================================================================
# 14. DUPLICATE EXTRACTION HANDLING
# =============================================================================

def test_14_duplicate_extraction_handling(db_session):
    user = User(email="dup_test@continuo.ai", hashed_password="pw", full_name="Dup User")
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Deduplication Project")
    db_session.add(project)
    db_session.flush()

    transcript = """
    Goal: Build an interactive 3D portfolio.
    Decision: We decided to use Three.js.
    Task: Fix the character animation loop.
    """
    res1 = ContextExtractionService.extract(transcript)
    counts1 = ContextExtractionService.persist_extracted_context(res1, project, user, db_session)
    assert counts1["goals"] == 1
    assert counts1["decisions"] == 1
    assert counts1["tasks"] == 1

    # Ingest the exact same transcript again
    res2 = ContextExtractionService.extract(transcript)
    counts2 = ContextExtractionService.persist_extracted_context(res2, project, user, db_session)
    # Deduplication must prevent recreating duplicate active records
    assert counts2["goals"] == 0
    assert counts2["decisions"] == 0
    assert counts2["tasks"] == 0

    # Total records in DB must remain 1
    assert db_session.query(ContextGoal).filter(ContextGoal.project_id == project.id).count() == 1
    assert db_session.query(ContextDecision).filter(ContextDecision.project_id == project.id).count() == 1
    assert db_session.query(ContextTask).filter(ContextTask.project_id == project.id).count() == 1


# =============================================================================
# 15. CONTRADICTION DETECTION INTEGRATION
# =============================================================================

def test_15_contradiction_detection_integration(db_session):
    user = User(email="contra_test@continuo.ai", hashed_password="pw", full_name="Contra User")
    db_session.add(user)
    db_session.flush()

    project = Project(user_id=user.id, name="Contradiction Project")
    db_session.add(project)
    db_session.flush()

    # Step 1: Existing accepted decision using Three.js
    initial_decision = ContextDecision(
        project_id=project.id,
        user_id=user.id,
        title="We decided to use Three.js",
        category="renderer",
        status="accepted"
    )
    db_session.add(initial_decision)
    db_session.commit()

    # Step 2: Ingest contradictory decision "Switch to Babylon.js"
    new_transcript = """
    Decision: Switched to Babylon.js for WebGPU performance.
    """
    res = ContextExtractionService.extract(
        raw_text=new_transcript,
        project_id=project.id,
        current_user_id=user.id,
        db=db_session
    )
    assert len(res.contradictions) >= 1
    assert any("babylon" in c.explanation.lower() or "three.js" in c.explanation.lower() for c in res.contradictions)

    # Step 3: Persisting the replacement must mark the old decision as superseded
    ContextExtractionService.persist_extracted_context(res, project, user, db_session)
    db_session.refresh(initial_decision)
    assert initial_decision.status == "superseded"
    assert initial_decision.superseded_by_id is not None


# =============================================================================
# 16. EXISTING CONTEXT PACKAGE COMPATIBILITY
# =============================================================================

def test_16_existing_context_package_compatibility():
    transcript = """
    User: I want to build a real-time notification engine for Nexora AI.
    Objective: Implement a resilient background dispatch worker with WebSocket broadcasting.
    Requirement: Must support at least 10,000 concurrent socket connections.
    Constraint: Do not use external third-party push brokers like Pusher.
    Decision: We decided to use FastAPI WebSockets combined with Redis Pub/Sub.
    Current State: Redis listener worker is implemented.
    """
    # Verify legacy ContextEngine.extract remains 100% compatible
    pkg = ContextEngine.extract(transcript, project_name="Nexora Notifications")
    expected_fields = [
        "objective", "requirements", "constraints", "instructions",
        "decisions", "current_state", "completed_work", "pending_work",
        "open_problems", "errors", "failed_attempts", "files_context",
        "design_decisions", "dependencies", "next_steps"
    ]
    for field in expected_fields:
        assert field in pkg
    assert len(pkg["requirements"]) >= 1
    assert len(pkg["decisions"]) >= 1


# =============================================================================
# 17. EXISTING HANDOFF COMPATIBILITY
# =============================================================================

def test_17_existing_handoff_compatibility():
    pkg_data = {
        "objective": "Build Context OS intelligence",
        "requirements": ["Structured extraction", "Visual context"],
        "constraints": ["No vision API", "Zero breaking changes"],
        "instructions": ["Maintain 100% backward compatibility"],
        "decisions": ["Standardize on ContextExtractionService"],
        "current_state": "Testing Phase 9.5",
        "completed_work": ["Implemented extraction models"],
        "pending_work": ["Full test suite verification"],
        "open_problems": [],
        "errors": [],
        "failed_attempts": [],
        "files_context": ["backend/services/context_extraction.py"],
        "design_decisions": ["Dark glass aesthetic"],
        "dependencies": ["FastAPI", "SQLAlchemy", "Pillow"],
        "next_steps": ["Run pytest", "Commit and push"]
    }
    res = HandoffService.generate(
        context_data=pkg_data,
        destination_provider="claude",
        project_name="Continuo OS"
    )
    payload = res["formatted_payload"]
    assert "PROJECT:" in payload or "OBJECTIVE:" in payload
    assert "Continuo OS" in payload
    assert "Structured extraction" in payload


# =============================================================================
# 18. EMPTY CONVERSATION BEHAVIOR
# =============================================================================

def test_18_empty_conversation_behavior():
    res_empty = ContextExtractionService.extract("")
    assert res_empty.goals == []
    assert res_empty.decisions == []
    assert res_empty.tasks == []
    assert res_empty.technical_states == []
    assert res_empty.visual_references == []
    assert res_empty.confidence_summary["overall"] == 0.0

    res_ws = ContextExtractionService.extract("    \n\n\t   ")
    assert res_ws.goals == []


# =============================================================================
# 19. MALFORMED EXTRACTION INPUT
# =============================================================================

def test_19_malformed_extraction_input():
    malformed = "\x00\x01\x02\xff\xfe\x07???///### $$$ === \n\n ::: 1234567890 !@#$%^&*()"
    res = ContextExtractionService.extract(malformed)
    # Must never crash and return valid Pydantic model
    assert isinstance(res.goals, list)
    assert isinstance(res.decisions, list)
    assert isinstance(res.tasks, list)


# =============================================================================
# 20. SECRET SANITIZATION COMPATIBILITY
# =============================================================================

def test_20_secret_sanitization_compatibility():
    transcript = """
    Decision: We decided to use Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID for authentication.
    Task: Fix database password=SuperSecretPass123! in connection postgres://user:secret@localhost:5432/db.
    Constraint: Do not leak API key sk-ant-api03-abcdef1234567890abcdef1234567890.
    """
    res = ContextExtractionService.extract(transcript)
    for d in res.decisions:
        assert "eyJhb" not in d.title
        assert "[REDACTED" in d.title or "token" in d.title.lower()

    for t in res.tasks:
        assert "SuperSecretPass123!" not in t.title
        assert "postgres://user:secret" not in t.title

    for g in res.goals:
        assert "sk-ant-api03" not in g.title


# =============================================================================
# 21. REST API: STATELESS EXTRACT-OS
# =============================================================================

def test_21_api_extract_os_stateless(client):
    resp = client.post("/api/v1/context/extract-os", json={
        "raw_transcript": "Decision: We will use Three.js for 3D visuals. Todo: Fix animation lag."
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "extracted" in data
    assert len(data["extracted"]["decisions"]) >= 1
    assert len(data["extracted"]["tasks"]) >= 1
    assert data["persisted_counts"] == {}


# =============================================================================
# 22. REST API: PROJECT-SCOPED EXTRACT-OS WITH PERSISTENCE
# =============================================================================

def test_22_api_extract_os_project_scoped_and_persist(client):
    headers = register_user(client, "extract_api@continuo.ai")
    proj_id = create_project(client, headers)

    resp = client.post(f"/api/v1/context/projects/{proj_id}/extract-os", headers=headers, json={
        "raw_transcript": """
        Goal: Build an interactive portfolio.
        Decision: We decided to use React with Tailwind CSS.
        Task: Implement the responsive navigation bar.
        """,
        "auto_persist": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["persisted_counts"]["goals"] >= 1
    assert data["persisted_counts"]["decisions"] >= 1
    assert data["persisted_counts"]["tasks"] >= 1

    # Verify entities are queryable via Phase 9.3 APIs
    goals_resp = client.get(f"/api/v1/projects/{proj_id}/goals", headers=headers)
    assert goals_resp.status_code == 200
    assert len(goals_resp.json()) >= 1


# =============================================================================
# 23. REST API: CONTEXT CAPTURE PERSISTS CONTEXT OS SEAMLESSLY
# =============================================================================

def test_23_capture_context_persists_context_os(client):
    headers = register_user(client, "capture_sync@continuo.ai")
    proj_id = create_project(client, headers)

    # Ingest transcript via legacy /capture endpoint
    resp = client.post("/api/v1/context/capture", headers=headers, json={
        "project_id": proj_id,
        "provider": "chatgpt",
        "title": "Session with ChatGPT",
        "raw_transcript": """
        Objective: Create real-time notification engine.
        Requirement: Must support WebSocket scaling.
        Decision: We decided to use FastAPI and Redis PubSub.
        Todo: Write integration tests for load testing.
        """
    })
    assert resp.status_code == 201
    pkg_data = resp.json()
    # Verifies legacy response format is 100% intact
    assert pkg_data["project_id"] == proj_id
    assert "version" in pkg_data
    assert "quality_score" in pkg_data

    # Verifies Context OS entities were automatically synthesized in DB
    decisions_resp = client.get(f"/api/v1/projects/{proj_id}/decisions", headers=headers)
    assert decisions_resp.status_code == 200
    assert len(decisions_resp.json()) >= 1

    tasks_resp = client.get(f"/api/v1/projects/{proj_id}/tasks", headers=headers)
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()) >= 1
