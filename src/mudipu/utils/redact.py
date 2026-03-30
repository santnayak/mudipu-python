"""
Data redaction utilities for privacy and security.
"""

import re
from typing import Any, Optional


class Redactor:
    """
    Redact sensitive information from data.
    """

    def __init__(self, patterns: Optional[list[str]] = None):
        """
        Initialize redactor.

        Args:
            patterns: List of regex patterns to redact
        """
        self.patterns = patterns or self._default_patterns()
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    @staticmethod
    def _default_patterns() -> list[str]:
        """Default redaction patterns."""
        return [
            # Email addresses
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            # SSN
            r"\b\d{3}-\d{2}-\d{4}\b",
            # Credit card numbers
            r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            # API keys (various formats)
            r"\bsk-[a-zA-Z0-9]{32,}\b",
            r"\bAKIA[0-9A-Z]{16}\b",
            # Phone numbers
            r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            # IPv4 addresses
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        ]

    def redact_string(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact sensitive information from a string.

        Args:
            text: Text to redact
            replacement: Replacement string

        Returns:
            Redacted text
        """
        result = text
        for pattern in self.compiled_patterns:
            result = pattern.sub(replacement, result)
        return result

    def redact_dict(self, data: dict, replacement: str = "[REDACTED]") -> dict:
        """
        Recursively redact sensitive information from a dictionary.

        Args:
            data: Dictionary to redact
            replacement: Replacement string

        Returns:
            Redacted dictionary
        """
        result = {}

        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.redact_string(value, replacement)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, replacement)
            elif isinstance(value, list):
                result[key] = self.redact_list(value, replacement)
            else:
                result[key] = value

        return result

    def redact_list(self, data: list, replacement: str = "[REDACTED]") -> list:
        """
        Recursively redact sensitive information from a list.

        Args:
            data: List to redact
            replacement: Replacement string

        Returns:
            Redacted list
        """
        result = []

        for item in data:
            if isinstance(item, str):
                result.append(self.redact_string(item, replacement))
            elif isinstance(item, dict):
                result.append(self.redact_dict(item, replacement))
            elif isinstance(item, list):
                result.append(self.redact_list(item, replacement))
            else:
                result.append(item)

        return result

    def redact(self, data: Any, replacement: str = "[REDACTED]") -> Any:
        """
        Redact sensitive information from any data structure.

        Args:
            data: Data to redact
            replacement: Replacement string

        Returns:
            Redacted data
        """
        if isinstance(data, str):
            return self.redact_string(data, replacement)
        elif isinstance(data, dict):
            return self.redact_dict(data, replacement)
        elif isinstance(data, list):
            return self.redact_list(data, replacement)
        else:
            return data


# Global redactor instance
_global_redactor: Optional[Redactor] = None


def get_redactor() -> Redactor:
    """Get the global redactor instance."""
    global _global_redactor
    if _global_redactor is None:
        from mudipu.config import get_config

        config = get_config()
        _global_redactor = Redactor(patterns=config.redact_patterns)
    return _global_redactor


def redact(data: Any, replacement: str = "[REDACTED]") -> Any:
    """
    Convenience function to redact data using global redactor.

    Args:
        data: Data to redact
        replacement: Replacement string

    Returns:
        Redacted data
    """
    return get_redactor().redact(data, replacement)
