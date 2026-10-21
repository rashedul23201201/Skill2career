import logging
from typing import Dict, Set, List, Any, Optional
from fastapi import WebSocket

logger = logging.getLogger("chat.websocket")


class ConnectionManager:
    """In-memory duplex WebSocket connection manager for real-time chat (SKL-16).
    Supports multiple concurrent connections per user (e.g., multiple browser tabs or devices).
    """

    def __init__(self):
        # Maps user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Register and accept an authenticated user's WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(
            "WebSocket connected: User ID %s (Total active sockets for user: %s)",
            user_id,
            len(self.active_connections[user_id]),
        )

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Unregister an authenticated user's WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info("WebSocket disconnected: User ID %s", user_id)

    def is_user_online(self, user_id: int) -> bool:
        """Check if a specific user currently maintains at least one active WebSocket session."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_personal_message(self, user_id: int, message: Dict[str, Any]) -> None:
        """Deliver a structured JSON payload to all active WebSocket clients of a user."""
        if user_id not in self.active_connections:
            return

        dead_sockets: List[WebSocket] = []
        for socket in list(self.active_connections[user_id]):
            try:
                await socket.send_json(message)
            except Exception as exc:
                logger.warning(
                    "Failed to deliver WebSocket message to User ID %s: %s", user_id, exc
                )
                dead_sockets.append(socket)

        for dead_socket in dead_sockets:
            self.disconnect(user_id, dead_socket)

    async def broadcast_to_users(
        self, user_ids: List[int], message: Dict[str, Any]
    ) -> None:
        """Broadcast a structured JSON payload to multiple recipients."""
        for uid in user_ids:
            await self.send_personal_message(uid, message)


# Global singleton instance for application-wide duplex dispatch
connection_manager = ConnectionManager()
