"""
Capture tool/function executions.
"""

from typing import Optional, Any
from datetime import datetime

from mudipu.context import trace_context


def capture_tool_execution(
    tool_name: str,
    arguments: dict[str, Any],
    result: Optional[Any] = None,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
) -> dict:
    """
    Capture a tool execution event.

    Args:
        tool_name: Name of the tool/function
        arguments: Arguments passed to the tool
        result: Tool execution result
        error: Error message if tool failed
        duration_ms: Execution duration

    Returns:
        Tool execution record
    """
    execution_record = {
        "tool_name": tool_name,
        "arguments": arguments,
        "result": result,
        "error": error,
        "duration_ms": duration_ms,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": str(trace_context.session_id) if trace_context.session_id else None,
        "trace_id": str(trace_context.trace_id) if trace_context.trace_id else None,
        "turn_number": trace_context.turn_number,
    }

    # Store in tool execution storage
    _store_tool_execution(execution_record)

    return execution_record


# Tool execution storage
_tool_executions: dict[str, list[dict]] = {}


def _store_tool_execution(record: dict) -> None:
    """Store tool execution record."""
    session_id = record.get("session_id")
    if not session_id:
        return

    if session_id not in _tool_executions:
        _tool_executions[session_id] = []

    _tool_executions[session_id].append(record)


def get_tool_executions(session_id: str) -> list[dict]:
    """Retrieve tool executions for a session."""
    return _tool_executions.get(session_id, [])


def clear_tool_executions(session_id: str) -> None:
    """Clear tool executions for a session."""
    if session_id in _tool_executions:
        del _tool_executions[session_id]
