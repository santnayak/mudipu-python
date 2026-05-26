"""
Tests for core tracer functionality.
"""

from uuid import UUID

from mudipu.tracer import MudipuTracer
from mudipu.context import trace_context


def test_tracer_initialization():
    """Test tracer can be initialized."""
    tracer = MudipuTracer(session_name="test", tags=["unit-test"])

    assert tracer.session_name == "test"
    assert tracer.tags == ["unit-test"]
    assert tracer.session is None


def test_start_session():
    """Test starting a session."""
    tracer = MudipuTracer(session_name="test")
    session = tracer.start_session()

    assert session is not None
    assert isinstance(session.session_id, UUID)
    assert isinstance(session.trace_id, UUID)
    assert session.name == "test"
    assert trace_context.session_id == session.session_id


def test_end_session():
    """Test ending a session."""
    tracer = MudipuTracer(session_name="test")
    tracer.start_session()

    session = tracer.end_session()

    assert session is not None
    assert session.ended_at is not None
    assert trace_context.session_id is None


def test_context_manager():
    """Test using tracer as context manager."""
    tracer = MudipuTracer(session_name="test")

    with tracer.trace_session():
        assert tracer.is_active
        assert trace_context.is_active()

    assert not tracer.is_active
    assert not trace_context.is_active()


def test_record_turn():
    """Test recording a turn."""
    tracer = MudipuTracer(session_name="test")
    tracer.start_session()

    turn = tracer.record_turn(
        request_messages=[{"role": "user", "content": "Hello"}],
        response_message={"role": "assistant", "content": "Hi"},
        model="gpt-4",
        duration_ms=250.0,
        usage={"total_tokens": 15},
    )

    assert turn.turn_number == 1
    assert turn.model == "gpt-4"
    assert tracer.session.turn_count == 1

    tracer.end_session()
