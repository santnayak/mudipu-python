"""
Main tracer implementation for capturing LLM interactions.
"""

from typing import Optional, Any
from uuid import uuid4
from datetime import datetime
from contextlib import contextmanager

from mudipu.config import get_config
from mudipu.context import trace_context
from mudipu.models import Session, BaseTurn as Turn, ToolCall


class MudipuTracer:
    """
    Main tracer for capturing and managing LLM traces.
    """

    def __init__(self, session_name: Optional[str] = None, tags: Optional[list[str]] = None):
        """
        Initialize tracer.

        Args:
            session_name: Optional name for the session
            tags: Optional tags for categorizing the session
        """
        self.config = get_config()
        self.session: Optional[Session] = None
        self.session_name = session_name
        self.tags = tags or []

    def start_session(self) -> Session:
        """
        Start a new tracing session.

        Returns:
            Created Session instance
        """
        if not self.config.enabled:
            raise RuntimeError("Tracing is disabled in configuration")

        self.session = Session(name=self.session_name, tags=self.tags)

        # Set context
        trace_context.session_id = self.session.session_id
        trace_context.trace_id = self.session.trace_id
        trace_context.turn_number = 0

        return self.session

    def end_session(self) -> Optional[Session]:
        """
        End the current tracing session.

        Returns:
            The completed Session, or None if no session was active
        """
        if self.session is None:
            return None

        self.session.end_session()

        # Auto-export if configured
        if self.config.auto_export:
            self._auto_export()

        # Reset context
        trace_context.reset()

        completed_session = self.session
        self.session = None

        return completed_session

    def record_turn(
        self,
        request_messages: list[dict],
        response_message: Optional[dict] = None,
        model: Optional[str] = None,
        request_tools: Optional[list[dict]] = None,
        duration_ms: Optional[float] = None,
        usage: Optional[dict] = None,
        tool_calls: Optional[list[ToolCall]] = None,
    ) -> Turn:
        """
        Record a single turn in the conversation.

        Args:
            request_messages: List of input messages
            response_message: Response message from LLM
            model: Model name/identifier
            request_tools: Available tools for the turn
            duration_ms: Duration in milliseconds
            usage: Token usage information
            tool_calls: Detected tool calls

        Returns:
            Created Turn instance
        """
        if self.session is None:
            raise RuntimeError("No active session. Call start_session() first.")

        turn_number = trace_context.increment_turn()

        turn = Turn(
            id=uuid4(),
            turn_number=turn_number,
            timestamp=datetime.utcnow().isoformat(),
            request_messages=request_messages,
            request_tools=request_tools or [],
            model=model,
            response_message=response_message,
            duration_ms=duration_ms,
            usage=usage,
            tool_calls_detected=tool_calls or [],
            has_tool_calls=bool(tool_calls),
        )

        self.session.add_turn(turn)

        return turn

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the current session.

        Args:
            key: Metadata key
            value: Metadata value
        """
        if self.session is None:
            raise RuntimeError("No active session")

        self.session.metadata[key] = value

    def _auto_export(self) -> None:
        """Auto-export session based on configuration."""
        if self.session is None:
            return

        from mudipu.exporters.json_exporter import JSONExporter
        from mudipu.exporters.html_exporter import HTMLExporter

        self.config.ensure_trace_dir()

        if self.config.export_format in ("json", "both"):
            exporter = JSONExporter()
            exporter.export(self.session)

        if self.config.export_format in ("html", "both"):
            exporter = HTMLExporter()
            exporter.export(self.session)

    @contextmanager
    def trace_session(self) -> Any:
        """
        Context manager for automatic session management.

        Example:
            with tracer.trace_session():
                # Your LLM calls here
                pass
        """
        try:
            self.start_session()
            yield self
        finally:
            self.end_session()

    @property
    def is_active(self) -> bool:
        """Check if tracer has an active session."""
        return self.session is not None
