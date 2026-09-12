"""
CONTINUO — Tests for Context Engine Extraction Pipeline
"""

import pytest
from backend.services.context_engine import ContextEngine

SAMPLE_TRANSCRIPT = """
User: I want to build a real-time notification engine for Nexora AI.
Objective: Implement a resilient background dispatch worker with WebSocket broadcasting.

Requirement: Must support at least 10,000 concurrent socket connections.
Requirement: Must integrate with Supabase for persistent delivery logs.
Constraint: Do not use external third-party push brokers like Pusher; use self-hosted Redis pub/sub.
Constraint: Never expose service-role API keys to the client browser.

Decision: We decided to use FastAPI WebSockets combined with Redis Pub/Sub.
Decision: Standardized on JSON message envelope format with UUID v4 tracing.

Current State: Redis listener worker is implemented. Client socket reconnect loop is working.
Completed: Schema definitions for notifications table created.
Pending: Implement exponential backoff retry policy for dropped connections.
Open problem: Disconnections during load spikes around 8,000 users.
Error: ConnectionRefusedError: [Errno 111] Connect call failed in worker.py line 42
Tried: We tried using in-memory Python asyncio queues but memory spiked to 2GB under load. Discarded approach.

Files: src/worker.py, backend/sockets.py, config/redis.conf
Next step: Add load balancing across 3 Uvicorn workers and test reconnect resiliency.
"""

def test_context_engine_extraction():
    pkg = ContextEngine.extract(SAMPLE_TRANSCRIPT, project_name="Nexora Notifications")

    assert "notification" in pkg["objective"].lower() or "implement" in pkg["objective"].lower()
    assert len(pkg["requirements"]) >= 2
    assert any("socket" in r.lower() or "supabase" in r.lower() for r in pkg["requirements"])
    assert len(pkg["constraints"]) >= 2
    assert any("pusher" in c.lower() or "secret" in c.lower() or "key" in c.lower() for c in pkg["constraints"])
    assert len(pkg["decisions"]) >= 1
    assert any("redis" in d.lower() or "fastapi" in d.lower() for d in pkg["decisions"])
    assert len(pkg["files_context"]) >= 2
    assert any("worker.py" in f for f in pkg["files_context"])
    assert len(pkg["failed_attempts"]) >= 1
    assert "asyncio" in pkg["failed_attempts"][0].lower() or "queue" in pkg["failed_attempts"][0].lower()
