"""
Extended models for SDK usage, building on shared contracts.
"""
from typing import Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

# Try to import from shared contracts, fallback to local if not available
try:
    from mudipu_contracts.schemas import Turn as BaseTurn, ToolCall, TraceEvent
except ImportError:
    # Fallback: define minimal versions locally
    from pydantic import BaseModel
    
    class ToolCall(BaseModel):
        """Represents a tool/function call from the LLM."""
        id: str
        type: str = "function"
        function_name: Optional[str] = None
        function_arguments: Optional[str] = None
    
    class BaseTurn(BaseModel):
        """Represents a single turn in a conversation trace."""
        id: UUID
        turn_number: int
        timestamp: str
        request_messages: list[dict] = Field(default_factory=list)
        request_tools: list[dict] = Field(default_factory=list)
        model: Optional[str] = None
        response_message: Optional[dict] = None
        duration_ms: Optional[float] = None
        usage: Optional[dict] = None
        tool_calls_detected: list[ToolCall] = Field(default_factory=list)
        has_tool_calls: bool = False
    
    class TraceEvent(BaseModel):
        """Event published when a trace is captured."""
        event_type: str
        session_id: UUID
        trace_id: UUID
        turn_data: BaseTurn
        timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Session(BaseModel):
    """
    Represents a complete tracing session.
    """
    session_id: UUID = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: Optional[str] = None
    
    # Session metadata
    name: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Turns tracked
    turns: list[BaseTurn] = Field(default_factory=list)
    turn_count: int = 0
    
    # Statistics
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    
    def add_turn(self, turn: BaseTurn) -> None:
        """Add a turn to the session."""
        self.turns.append(turn)
        self.turn_count += 1
        if turn.duration_ms:
            self.total_duration_ms += turn.duration_ms
        if turn.usage and "total_tokens" in turn.usage:
            self.total_tokens += turn.usage["total_tokens"]
    
    def end_session(self) -> None:
        """Mark session as ended."""
        self.ended_at = datetime.utcnow().isoformat()


class ExportMetadata(BaseModel):
    """
    Metadata for exported trace files.
    """
    exported_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    sdk_version: str
    format_version: str = "1.0"
    exporter_type: str  # "json", "html", "platform"
