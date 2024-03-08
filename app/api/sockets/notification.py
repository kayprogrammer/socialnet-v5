from typing import Any, Literal
from uuid import UUID
from litestar import WebSocket
from pydantic import BaseModel
from app.api.sockets.base import BaseSocketConnectionHandler
from app.common.exception_handlers import ErrorCode
from app.db.models.profiles import Notification


class NotificationData(BaseModel):
    id: UUID
    status: Literal["CREATED", "DELETED"]
    ntype: str


class NotificationSocketHandler(BaseSocketConnectionHandler):
    path = "/notifications"

    async def on_receive(self, socket: WebSocket, data: str, user: Any):
        data = await super().on_receive(socket, data)
        print(data)
        # Ensure data is a notification data. That means it align with the Notification data above
        try:
            NotificationData(**data)
        except Exception:
            await self.send_error_data(
                socket, "Invalid Notification data", ErrorCode.INVALID_ENTRY
            )

        for connection in self.active_connections:
            user = connection.scope["user"]
            user_is_among_receivers = await Notification.filter(
                receivers__id=user.id, id=data["id"]
            )
            if user_is_among_receivers:
                # Only true receivers should access the data
                await connection.send_json(data)
        return "Sent"
