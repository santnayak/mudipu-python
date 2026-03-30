"""
Platform exporter for sending traces to Mudipu platform.

Note: Requires 'mudipu-packages' to be installed.
Install with: pip install mudipu[platform]
"""

import asyncio
from typing import Optional

from mudipu.models import Session
from mudipu.config import get_config

# Check if platform dependencies are available
try:
    from mudipu_contracts.schemas import TraceEvent
    from mudipu_clients.nats_client import MudipuNATSClient

    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False
    TraceEvent = None
    MudipuNATSClient = None


class PlatformExporter:
    """
    Export trace sessions to Mudipu platform via NATS.

    Requires platform dependencies. Install with: pip install mudipu[platform]
    """

    def __init__(self, platform_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize platform exporter.

        Args:
            platform_url: Platform URL (defaults to config)
            api_key: API key for authentication (defaults to config)

        Raises:
            ImportError: If platform dependencies are not installed
        """
        if not PLATFORM_AVAILABLE:
            raise ImportError("Platform dependencies not installed. " "Install with: pip install mudipu[platform]")

        config = get_config()
        self.platform_url = platform_url or config.platform_url or "nats://localhost:4222"
        self.api_key = api_key or config.api_key
        self.nats_client = MudipuNATSClient(nats_url=self.platform_url)

    async def export_async(self, session: Session) -> None:
        """
        Export a session to the platform asynchronously.

        Args:
            session: Session to export
        """
        await self.nats_client.connect()

        try:
            # Publish each turn as a trace event
            for turn in session.turns:
                event = TraceEvent(
                    event_type="turn_recorded",
                    session_id=session.session_id,
                    trace_id=session.trace_id,
                    turn_data=turn,
                )

                await self.nats_client.publish(
                    subject="mudipu.traces.turn",
                    data=event.model_dump(mode="json"),
                )
        finally:
            await self.nats_client.disconnect()

    def export(self, session: Session) -> None:
        """
        Export a session to the platform (synchronous wrapper).

        Args:
            session: Session to export
        """
        asyncio.run(self.export_async(session))

    async def export_multiple_async(self, sessions: list[Session]) -> None:
        """
        Export multiple sessions asynchronously.

        Args:
            sessions: List of sessions to export
        """
        await self.nats_client.connect()

        try:
            for session in sessions:
                await self.export_async(session)
        finally:
            await self.nats_client.disconnect()

    def export_multiple(self, sessions: list[Session]) -> None:
        """
        Export multiple sessions (synchronous wrapper).

        Args:
            sessions: List of sessions to export
        """
        asyncio.run(self.export_multiple_async(sessions))
