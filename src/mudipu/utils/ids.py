"""
ID generation utilities.
"""

import uuid
from typing import Optional


def generate_session_id() -> uuid.UUID:
    """Generate a unique session ID."""
    return uuid.uuid4()


def generate_trace_id() -> uuid.UUID:
    """Generate a unique trace ID."""
    return uuid.uuid4()


def generate_turn_id() -> uuid.UUID:
    """Generate a unique turn ID."""
    return uuid.uuid4()


def generate_tool_call_id() -> str:
    """
    Generate a tool call ID in OpenAI format.

    Returns:
        Tool call ID string (e.g., 'call_abc123...')
    """
    return f"call_{uuid.uuid4().hex[:24]}"


def short_id(id_value: Optional[uuid.UUID] = None) -> str:
    """
    Generate or shorten a UUID to first 8 characters.

    Args:
        id_value: Optional UUID to shorten

    Returns:
        Short ID string
    """
    if id_value is None:
        id_value = uuid.uuid4()

    return str(id_value)[:8]
