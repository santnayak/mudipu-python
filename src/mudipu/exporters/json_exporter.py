"""
JSON exporter for trace data.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from mudipu.models import Session, ExportMetadata
from mudipu.config import get_config
from mudipu.version import __version__


class JSONExporter:
    """
    Export trace sessions to JSON format.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize JSON exporter.
        
        Args:
            output_dir: Directory to write JSON files (defaults to config trace_dir)
        """
        config = get_config()
        self.output_dir = output_dir or config.trace_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, session: Session, filename: Optional[str] = None) -> Path:
        """
        Export a session to JSON file.
        
        Args:
            session: Session to export
            filename: Optional custom filename
            
        Returns:
            Path to the exported file
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            session_name = session.name or "session"
            filename = f"{session_name}_{timestamp}_{session.session_id}.json"
        
        output_path = self.output_dir / filename
        
        # Create export data
        export_data = {
            "metadata": ExportMetadata(
                sdk_version=__version__,
                exporter_type="json",
            ).model_dump(),
            "session": session.model_dump(mode="json"),
        }
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_path
    
    def export_multiple(self, sessions: list[Session]) -> list[Path]:
        """
        Export multiple sessions.
        
        Args:
            sessions: List of sessions to export
            
        Returns:
            List of paths to exported files
        """
        return [self.export(session) for session in sessions]
    
    @staticmethod
    def load(path: Path) -> Session:
        """
        Load a session from JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Loaded Session instance
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        session_data = data.get("session", data)
        return Session(**session_data)


from typing import Optional
