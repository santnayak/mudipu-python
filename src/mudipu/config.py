"""
Configuration management for Mudipu SDK.
"""

from typing import Optional, Literal
from pathlib import Path
from pydantic import BaseModel, Field


class MudipuConfig(BaseModel):
    """
    Central configuration for Mudipu instrumentation.
    """

    # Tracing
    enabled: bool = Field(default=True, description="Enable/disable tracing globally")
    trace_dir: Path = Field(default=Path(".mudipu/traces"), description="Directory to store trace files")

    # Export settings
    auto_export: bool = Field(default=True, description="Automatically export traces after session")
    export_format: Literal["json", "html", "both"] = Field(default="both", description="Default export format")

    # Platform integration
    platform_enabled: bool = Field(default=False, description="Send traces to Mudipu platform")
    platform_url: Optional[str] = Field(default=None, description="Mudipu platform URL")
    api_key: Optional[str] = Field(default=None, description="API key for platform authentication")

    # Privacy & Security
    redact_enabled: bool = Field(default=False, description="Enable data redaction")
    redact_patterns: list[str] = Field(
        default_factory=lambda: [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # emails
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\bsk-[a-zA-Z0-9]{32,}\b",  # API keys
        ],
        description="Regex patterns for redaction",
    )

    # Performance
    max_turns_per_session: int = Field(default=1000, description="Maximum turns to track per session")
    buffer_size: int = Field(default=100, description="Buffer size for batched exports")

    # Debugging
    debug: bool = Field(default=False, description="Enable debug logging")
    verbose: bool = Field(default=False, description="Verbose output")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def ensure_trace_dir(self) -> None:
        """Ensure trace directory exists."""
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, path: Path) -> "MudipuConfig":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            MudipuConfig instance
        """
        import yaml

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to save YAML configuration
        """
        import yaml

        data = self.model_dump(mode="json")
        # Convert Path to string for YAML serialization
        data["trace_dir"] = str(data["trace_dir"])

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)


# Global config instance
_config: Optional[MudipuConfig] = None


def get_config() -> MudipuConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = MudipuConfig()
    return _config


def set_config(config: MudipuConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset configuration to defaults."""
    global _config
    _config = None
