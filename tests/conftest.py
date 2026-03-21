"""
Test configuration for pytest.
"""
import pytest
from pathlib import Path


@pytest.fixture
def temp_trace_dir(tmp_path):
    """Create a temporary trace directory."""
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    return trace_dir


@pytest.fixture
def sample_session():
    """Create a sample session for testing."""
    from uuid import uuid4
    from mudipu.models import Session, BaseTurn as Turn
    
    session = Session(
        session_id=uuid4(),
        trace_id=uuid4(),
        name="test-session",
        tags=["test"],
    )
    
    # Add a sample turn
    turn = Turn(
        id=uuid4(),
        turn_number=1,
        timestamp="2026-03-20T10:00:00Z",
        request_messages=[
            {"role": "user", "content": "Hello"}
        ],
        response_message={
            "role": "assistant",
            "content": "Hi there!"
        },
        model="gpt-4",
        duration_ms=250.0,
        usage={
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    )
    
    session.add_turn(turn)
    
    return session
