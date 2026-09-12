"""
CONTINUO — Tests for Version Diff Engine
"""

from backend.services.version_diff import VersionDiffEngine

def test_version_diff_calculation():
    old_pkg = {
        "objective": "Build REST API",
        "current_state": "v1.0 Prototype working in Flask",
        "requirements": ["Basic user signup", "Password reset"],
        "decisions": ["Used Flask and SQLite"],
        "failed_attempts": []
    }

    new_pkg = {
        "objective": "Build high-performance REST API",
        "current_state": "v1.1 Migrated to FastAPI with Supabase",
        "requirements": ["Basic user signup", "Password reset", "OAuth2 social login"],
        "decisions": ["Used FastAPI and Supabase PostgreSQL"],
        "failed_attempts": ["Tried keeping Flask with async gevent, but latency remained high"]
    }

    diff = VersionDiffEngine.compute_diff(old_pkg, new_pkg, "v1.0", "v1.1", "proj-123")

    assert "OAuth2 social login" in diff["added"]["requirements"]
    assert "Used Flask and SQLite" in diff["removed"]["decisions"]
    assert "Used FastAPI and Supabase PostgreSQL" in diff["added"]["decisions"]
    assert "current_state" in diff["modified"]
    assert "Flask" in diff["modified"]["current_state"]["previous"]
    assert "FastAPI" in diff["modified"]["current_state"]["current"]
    assert "added" in diff["summary"]
