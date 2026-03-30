"""
Time utilities for consistent time handling.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time with timezone info.

    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """
    Get current UTC time as ISO format string.

    Returns:
        ISO format timestamp
    """
    return utc_now().isoformat()


def parse_iso(timestamp: str) -> datetime:
    """
    Parse ISO format timestamp string.

    Args:
        timestamp: ISO format timestamp string

    Returns:
        Parsed datetime
    """
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def format_duration(milliseconds: float) -> str:
    """
    Format duration in milliseconds to human-readable string.

    Args:
        milliseconds: Duration in milliseconds

    Returns:
        Formatted duration string
    """
    if milliseconds < 1000:
        return f"{milliseconds:.2f}ms"

    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.2f}s"

    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f}m"

    hours = minutes / 60
    return f"{hours:.2f}h"


def time_since(timestamp: str) -> str:
    """
    Calculate time elapsed since a timestamp.

    Args:
        timestamp: ISO format timestamp

    Returns:
        Human-readable time elapsed string
    """
    then = parse_iso(timestamp)
    now = utc_now()
    delta = now - then

    seconds = delta.total_seconds()

    if seconds < 60:
        return f"{int(seconds)}s ago"

    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m ago"

    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)}h ago"

    days = hours / 24
    return f"{int(days)}d ago"
