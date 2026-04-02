"""
Platform exporter for sending traces to the Mudipu platform gateway.

Note: Requires 'mudipu-packages' to be installed.
Install with: pip install mudipu[platform]
"""
import json
import urllib.request
import urllib.error
from typing import Optional

from mudipu.models import Session
from mudipu.config import get_config

# Check if platform dependencies are available
try:
    from mudipu_contracts.schemas import TraceEvent
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False
    TraceEvent = None


class PlatformExporter:
    """
    Export trace sessions to the Mudipu platform gateway via HTTP.

    The gateway handles routing to NATS internally — the SDK only needs
    to push JSON payloads to the gateway's ingest endpoint.

    Requires: pip install mudipu[platform]
    """

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Args:
            gateway_url: Base URL of the Mudipu platform gateway.
                         Defaults to config value or ``http://localhost:8000``.
            api_key:     API key for authentication. Defaults to config value.

        Raises:
            ImportError: If ``mudipu-packages`` is not installed.
        """
        if not PLATFORM_AVAILABLE:
            raise ImportError(
                "Platform dependencies not installed. "
                "Install with: pip install mudipu[platform]"
            )

        config = get_config()
        self.gateway_url = (
            gateway_url
            or getattr(config, "platform_url", None)
            or "http://localhost:8000"
        ).rstrip("/")
        self.api_key = api_key or getattr(config, "api_key", None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post(self, path: str, payload: dict) -> None:
        """Send a single JSON payload to the gateway."""
        url = f"{self.gateway_url}{path}"
        data = json.dumps(payload, default=str).encode()
        req = urllib.request.Request(url, data=data, headers=self._build_headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Platform gateway returned {exc.code} for {url}: {exc.reason}"
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export(self, session: Session) -> None:
        """
        Serialize all turns in *session* as ``TraceEvent`` objects and POST
        them to the platform gateway.

        Args:
            session: Completed :class:`~mudipu.models.Session` to export.
        """
        for turn in session.turns:
            event = TraceEvent(
                event_type="turn_recorded",
                session_id=session.session_id,
                trace_id=session.trace_id,
                turn_data=turn,
            )
            self._post("/ingest/turn", event.model_dump(mode="json"))

    def export_multiple(self, sessions: list[Session]) -> None:
        """
        Export multiple sessions to the platform gateway.

        Args:
            sessions: List of :class:`~mudipu.models.Session` objects.
        """
        for session in sessions:
            self.export(session)

