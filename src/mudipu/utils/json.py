"""
JSON utilities for safe serialization.
"""
import json
from typing import Any
from datetime import datetime
from uuid import UUID
from pathlib import Path


class MudipuJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles common Python types.
    """
    
    def default(self, obj: Any) -> Any:
        """Handle non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "model_dump"):
            # Pydantic models
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            # Older Pydantic models
            return obj.dict()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        
        return super().default(obj)


def safe_dumps(obj: Any, indent: int = 2) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        indent: Indentation level
        
    Returns:
        JSON string
    """
    return json.dumps(obj, cls=MudipuJSONEncoder, indent=indent)


def safe_loads(json_str: str) -> Any:
    """
    Safely deserialize JSON string.
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Deserialized object
    """
    return json.loads(json_str)


def pretty_print(obj: Any) -> None:
    """
    Pretty print an object as JSON.
    
    Args:
        obj: Object to print
    """
    print(safe_dumps(obj, indent=2))
