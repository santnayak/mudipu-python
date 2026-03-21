"""
Session-level capture utilities.
"""
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

from mudipu.models import Session
from mudipu.context import trace_context


class SessionCapture:
    """
    Helper for capturing session-level events and metadata.
    """
    
    def __init__(self, session: Session):
        """
        Initialize session capture.
        
        Args:
            session: Session to capture for
        """
        self.session = session
    
    def add_event(self, event_type: str, data: dict[str, Any]) -> None:
        """
        Add a custom event to the session.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if "events" not in self.session.metadata:
            self.session.metadata["events"] = []
        
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        
        self.session.metadata["events"].append(event)
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the session.
        
        Args:
            tag: Tag to add
        """
        if tag not in self.session.tags:
            self.session.tags.append(tag)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set session metadata.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.session.metadata[key] = value
    
    def record_error(self, error: Exception, context: Optional[dict] = None) -> None:
        """
        Record an error in the session.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
        """
        if "errors" not in self.session.metadata:
            self.session.metadata["errors"] = []
        
        error_record = {
            "type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "turn_number": trace_context.turn_number,
            "context": context or {},
        }
        
        self.session.metadata["errors"].append(error_record)
    
    def get_summary(self) -> dict:
        """
        Get a summary of the session.
        
        Returns:
            Session summary dictionary
        """
        return {
            "session_id": str(self.session.session_id),
            "name": self.session.name,
            "turn_count": self.session.turn_count,
            "total_duration_ms": self.session.total_duration_ms,
            "total_tokens": self.session.total_tokens,
            "tags": self.session.tags,
            "created_at": self.session.created_at,
            "ended_at": self.session.ended_at,
        }
