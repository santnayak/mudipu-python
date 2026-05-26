"""
Settings and environment variable handling.
"""

import os
from pathlib import Path
from typing import Optional


class Settings:
    """
    Environment-based settings for Mudipu SDK.
    """

    @staticmethod
    def get_trace_dir() -> Path:
        """Get trace directory from environment or default."""
        return Path(os.getenv("MUDIPU_TRACE_DIR", ".mudipu/traces"))

    @staticmethod
    def get_platform_url() -> Optional[str]:
        """Get platform URL from environment."""
        return os.getenv("MUDIPU_PLATFORM_URL")

    @staticmethod
    def get_api_key() -> Optional[str]:
        """Get API key from environment."""
        return os.getenv("MUDIPU_API_KEY")

    @staticmethod
    def is_enabled() -> bool:
        """Check if tracing is enabled via environment."""
        return os.getenv("MUDIPU_ENABLED", "true").lower() in ("true", "1", "yes")

    @staticmethod
    def is_debug() -> bool:
        """Check if debug mode is enabled."""
        return os.getenv("MUDIPU_DEBUG", "false").lower() in ("true", "1", "yes")

    @staticmethod
    def get_config_file() -> Optional[Path]:
        """Get configuration file path from environment."""
        path = os.getenv("MUDIPU_CONFIG")
        return Path(path) if path else None
