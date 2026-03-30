"""
Capture and record LLM turn data.
"""

from typing import Optional
from uuid import uuid4

from mudipu.context import trace_context
from mudipu.models import BaseTurn as Turn, ToolCall


def capture_llm_turn(
    request_messages: list[dict],
    response_data: dict,
    model: str,
    tools: Optional[list[dict]] = None,
    duration_ms: Optional[float] = None,
) -> Optional[Turn]:
    """
    Capture a complete LLM turn.

    Args:
        request_messages: Input messages
        response_data: Response from LLM
        model: Model identifier
        tools: Available tools
        duration_ms: Duration of the call

    Returns:
        Captured Turn instance, or None if no active session
    """
    # Check if we have an active session
    if not trace_context.is_active():
        return None

    # Extract response message
    response_message = _extract_response_message(response_data)

    # Extract tool calls if present
    tool_calls = _extract_tool_calls(response_data)

    # Extract usage
    usage = response_data.get("usage")

    # Create turn
    turn = Turn(
        id=uuid4(),
        turn_number=trace_context.increment_turn(),
        timestamp=_get_timestamp(),
        request_messages=request_messages,
        request_tools=tools or [],
        model=model,
        response_message=response_message,
        duration_ms=duration_ms,
        usage=usage,
        tool_calls_detected=tool_calls,
        has_tool_calls=bool(tool_calls),
    )

    # Record turn using the global tracer
    # We'll need to access the active tracer instance
    # For now, we'll store turns in a session-scoped storage
    _store_turn(turn)

    return turn


def _extract_response_message(response_data: dict) -> dict:
    """Extract the message portion from response data."""
    # If response_data already looks like a message
    if "role" in response_data:
        return response_data

    # Default assistant message
    return {
        "role": "assistant",
        "content": response_data.get("content", ""),
    }


def _extract_tool_calls(response_data: dict) -> list[ToolCall]:
    """Extract tool calls from response data."""
    tool_calls: list[ToolCall] = []

    if "tool_calls" in response_data:
        for tc in response_data["tool_calls"]:
            tool_call = ToolCall(
                id=tc.get("id", str(uuid4())),
                type=tc.get("type", "function"),
                function_name=tc.get("function", {}).get("name"),
                function_arguments=tc.get("function", {}).get("arguments"),
            )
            tool_calls.append(tool_call)

    return tool_calls


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime

    return datetime.utcnow().isoformat()


# Session-scoped turn storage
# This is a simple approach - in practice, you might use a more sophisticated
# storage mechanism or integrate directly with the tracer
_turn_storage: dict[str, list[Turn]] = {}


def _store_turn(turn: Turn) -> None:
    """Store a turn in session-scoped storage."""
    session_id = str(trace_context.session_id)

    if session_id not in _turn_storage:
        _turn_storage[session_id] = []

    _turn_storage[session_id].append(turn)


def get_stored_turns(session_id: str) -> list[Turn]:
    """Retrieve stored turns for a session."""
    return _turn_storage.get(session_id, [])


def clear_stored_turns(session_id: str) -> None:
    """Clear stored turns for a session."""
    if session_id in _turn_storage:
        del _turn_storage[session_id]
