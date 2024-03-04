from typing import Literal, Union
from uuid import UUID
from litestar import WebSocket
from pydantic import BaseModel
from app.api.sockets.base import BaseSocketConnectionHandler
from app.common.exception_handlers import ErrorCode
from app.db.models.accounts import User
from app.db.models.profiles import Notification


class NotificationData(BaseModel):
    id: UUID
    status: Literal["CREATED", "DELETED"]
    ntype: str


class NotificationSocketHandler(BaseSocketConnectionHandler):
    path = "/notifications"

    async def receive_data(self, websocket: WebSocket):
        data = await super().on_receive(websocket)
        # Ensure data is a notification data. That means it align with the Notification data above
        try:
            NotificationData(**data)
        except Exception:
            await self.send_error_data(
                websocket, "Invalid Notification data", ErrorCode.INVALID_ENTRY
            )
        return data

    async def broadcast(self, data: dict, user: User):
        for connection in self.active_connections:
            if not user:
                continue
            user_is_among_receivers = await Notification.filter(
                receivers__id=user.id, id=data["id"]
            )
            if user_is_among_receivers:
                # Only true receivers should access the data
                await connection.send_json(data)


# @notification_socket_router.websocket("/notifications")
# async def websocket_endpoint(
#     websocket: WebSocket, user: Union[User, str] = Depends(get_current_socket_user)
# ):
#     websocket.scope["user"] = (
#         user if isinstance(user, User) else None
#     )  # Attach user to webscoket
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await manager.receive_data(websocket)
#             if isinstance(user, str):
#                 # in app connection (with socket secret)
#                 # Send data
#                 await manager.broadcast(data)
#             else:
#                 await manager.send_error_data(
#                     websocket, "Unauthorized to send data", ErrorCode.NOT_ALLOWED, 4001
#                 )
#     except Exception as e:
#         if websocket in manager.active_connections:
#             manager.active_connections.remove(websocket)
#         if isinstance(e, WebSocketException):
#             await websocket.close()
