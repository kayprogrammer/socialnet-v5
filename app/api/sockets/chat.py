import json
import os
from typing import Any, Literal
from uuid import UUID
from litestar import WebSocket
from pydantic import BaseModel
import websockets
from app.api.schemas.chat import MessageSchema
from app.api.sockets.base import BaseSocketConnectionHandler
from app.common.exception_handlers import ErrorCode
from app.core.config import settings
from app.db.models.accounts import User
from app.db.models.chat import Chat, Message


class SocketMessageSchema(BaseModel):
    status: Literal["CREATED", "UPDATED", "DELETED"]
    id: UUID


class ChatSocketHandler(BaseSocketConnectionHandler):
    path = "/chats/{id:str}"

    async def on_accept(self, socket: WebSocket, user: Any, id: str) -> None:
        await super().on_accept(socket, user)
        # Verify chat ID & membership
        if user != settings.SOCKET_SECRET:
            await self.validate_chat_membership(socket, user, id)
        group_name = f"chat_{id}"
        socket.scope["group_name"] = group_name

    async def validate_chat_membership(self, socket: WebSocket, user: User, id: str):
        user_id = user.id
        chat, obj_user = await self.get_chat_or_user(socket, user, id)
        if not chat and not obj_user:  # If no chat nor user
            await self.send_error_data(socket, "Invalid ID", "invalid_input", 4004)

        if (
            chat and user not in (await chat.users.all()) and user_id != chat.owner_id
        ):  # If chat but user is not a member
            await self.send_error_data(
                socket, "You're not a member of this chat", "invalid_member", 4001
            )

    async def get_chat_or_user(self, socket: WebSocket, user, id):
        chat, obj_user = None, None
        if user.id != id:
            chat = await Chat.get_or_none(id=id).prefetch_related("users")
            if not chat:
                # Probably a first DM message
                obj_user = await User.get_or_none(username=id)
        else:
            obj_user = user  # Message is sent to self
        socket.scope["obj_user"] = obj_user
        return chat, obj_user

    async def on_receive(self, socket: WebSocket, data: str, user: Any):
        data = await super().on_receive(socket, data)
        # Ensure data is a notification data. That means it align with the Notification data above
        try:
            data = SocketMessageSchema(**data)
        except Exception:
            await self.send_error_data(
                socket, "Invalid Message data", ErrorCode.INVALID_ENTRY, 4220
            )

        status = data.status
        if status == "DELETED" and user != settings.SOCKET_SECRET:
            await self.send_error_data(
                socket,
                "Not allowed to send deletion socket",
                ErrorCode.UNAUTHORIZED_USER,
                4001,
            )

        message_data = {"id": str(data.id), "status": status}
        if status != "DELETED":
            message = await Message.get_or_none(id=data.id).select_related(
                "sender", "sender__avatar", "file"
            )
            if not message:
                await self.send_error_data(
                    socket, "Invalid message ID", ErrorCode.NON_EXISTENT, 4004
                )
            elif message.sender_id != user.id:
                await self.send_error_data(
                    socket, "Message isn't yours", ErrorCode.INVALID_OWNER, 4001
                )

            data = message_data | {
                "chat_id": str(message.chat_id),
                "created_at": str(message.created_at),
                "updated_at": str(message.updated_at),
            }
            message_data = data | MessageSchema.model_validate(message).model_dump(
                exclude={"id", "chat", "created_at", "updated_at"}
            )

        for connection in self.active_connections:
            # Only true receivers should access the data
            if connection.scope["group_name"] == socket.scope["group_name"]:
                user = connection.scope["user"]
                obj_user = connection.scope.get("obj_user")
                if obj_user:
                    # Ensure that reading messages from a user id can only be done by the owner
                    if user == obj_user:
                        await connection.send_json(message_data)
                else:
                    await connection.send_json(message_data)
        return "Sent"


# Send message deletion details in websocket
async def send_message_deletion_in_socket(
    secured: bool, host: str, chat_id: UUID, message_id: UUID
):
    if os.environ.get("ENVIRONMENT") == "testing":
        return
    websocket_scheme = "wss://" if secured else "ws://"
    uri = f"{websocket_scheme}{host}/api/v5/ws/chats/{chat_id}"
    chat_data = {
        "id": str(message_id),
        "status": "DELETED",
    }
    headers = [
        ("Authorization", settings.SOCKET_SECRET),
    ]
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # Send the message to the WebSocket server
        await websocket.send(json.dumps(chat_data))
        await websocket.close()
