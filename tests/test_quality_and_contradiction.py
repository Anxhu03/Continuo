"""
CONTINUO — Tests for Quality Scorer & Contradiction Detection
"""

from backend.services.quality_scorer import QualityScorer
from backend.services.contradiction import ContradictionDetector

def test_dynamic_quality_scoring():
    # Rich, high-completeness package
    rich_context = {
        "objective": "Build and deploy production authentication microservice with OAuth2 and PKCE.",
        "requirements": [
            "Support Google and GitHub OAuth providers",
            "Generate short-lived JWTs (15 min) and rotating refresh tokens",
            "Store hashed user credentials with argon2/pbkdf2"
        ],
        "constraints": [
            "Do not store plaintext passwords under any circumstances",
            "Never expose internal service tokens"
        ],
        "decisions": [
            "Decided to use FastAPI with SQLAlchemy and PostgreSQL",
            "Adopted PyJWT for token generation"
        ],
        "current_state": "FastAPI routes implemented. Token issuing verified.",
        "completed_work": ["Auth endpoints built", "Database migrations run"],
        "pending_work": ["Setup Redis blacklist for revoked tokens"],
        "failed_attempts": ["Tried in-memory token set but failed across multiple worker processes"],
        "files_context": ["auth/router.py", "auth/service.py", "models/user.py"],
        "dependencies": ["FastAPI", "PostgreSQL", "PyJWT"],
        "next_steps": ["Implement refresh token rotation endpoint", "Run unit tests"]
    }

    rich_score = QualityScorer.evaluate(rich_context)
    assert rich_score["overall_score"] > 80.0
    assert len(rich_score["contradictions"]) == 0

    # Minimal / incomplete package
    sparse_context = {
        "objective": "Build app",
        "requirements": [],
        "constraints": [],
        "decisions": [],
        "current_state": "Starting",
    }
    sparse_score = QualityScorer.evaluate(sparse_context)
    assert sparse_score["overall_score"] < 50.0
    assert len(sparse_score["recommendations"]) >= 2
    # Verify score is dynamic and not hardcoded
    assert rich_score["overall_score"] != sparse_score["overall_score"]

def test_contradiction_detection():
    conflicting_context = {
        "objective": "Build enterprise data platform",
        "requirements": ["Store unstructured events in MongoDB"],
        "constraints": ["Do not use NoSQL engines"],
        "decisions": ["Decided to use PostgreSQL for relational integrity", "Switched to MongoDB for rapid prototyping"],
        "current_state": "Architecture design phase"
    }

    contradictions = ContradictionDetector.analyze(conflicting_context)
    assert len(contradictions) >= 1
    topics = [c["topic"] for c in contradictions]
    assert any("Database" in t or "NoSQL" in t or "MongoDB" in t for t in topics)
