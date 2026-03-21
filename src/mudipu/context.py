"""
Context management for tracing.

Provides thread-local storage for the current session and turn information.
"""
import contextvars
from typing import Optional
from uuid import UUID

# Context variables for thread-safe tracing
_session_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar("session_id", default=None)
_trace_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar("trace_id", default=None)
_turn_number: contextvars.ContextVar[int] = contextvars.ContextVar("turn_number", default=0)


class TraceContext:
    """
    Context manager for tracing information.
    """
    
    @property
    def session_id(self) -> Optional[UUID]:
        """Get current session ID from context."""
        return _session_id.get()
    
    @session_id.setter
    def session_id(self, value: Optional[UUID]) -> None:
        """Set session ID in context."""
        _session_id.set(value)
    
    @property
    def trace_id(self) -> Optional[UUID]:
        """Get current trace ID from context."""
        return _trace_id.get()
    
    @trace_id.setter
    def trace_id(self, value: Optional[UUID]) -> None:
        """Set trace ID in context."""
        _trace_id.set(value)
    
    @property
    def turn_number(self) -> int:
        """Get current turn number from context."""
        return _turn_number.get()
    
    @turn_number.setter
    def turn_number(self, value: int) -> None:
        """Set turn number in context."""
        _turn_number.set(value)
    
    def increment_turn(self) -> int:
        """
        Increment turn number and return new value.
        
        Returns:
            New turn number
        """
        current = self.turn_number
        new_turn = current + 1
        self.turn_number = new_turn
        return new_turn
    
    def reset(self) -> None:
        """Reset all context variables."""
        self.session_id = None
        self.trace_id = None
        self.turn_number = 0
    
    def is_active(self) -> bool:
        """Check if tracing context is active."""
        return self.session_id is not None


# Global context instance
trace_context = TraceContext()
