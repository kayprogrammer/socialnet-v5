import json
from typing import Any
from litestar.handlers import WebsocketListener
from litestar import WebSocket

from app.common.exception_handlers import ErrorCode, SocketError
from app.db.models.accounts import User


class BaseSocketConnectionHandler(WebsocketListener):
    active_connections: list[WebSocket] = []

    async def on_accept(self, socket: WebSocket, user: Any) -> None:
        if isinstance(user, SocketError):
            await self.send_error_data(socket, user.err_msg, user.err_type, user.code)
        self.active_connections.append(socket)

    async def on_receive(self, socket: WebSocket, data: str):
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            await self.send_error_data(
                socket, "Invalid JSON", ErrorCode.INVALID_DATA_TYPE
            )
        return data

    async def send_personal_message(self, data: dict, socket: WebSocket):
        await socket.send_json(data)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

    async def send_error_data(
        self,
        socket: WebSocket,
        message,
        err_type=ErrorCode.BAD_REQUEST,
        code=4000,
        data=None,
    ):
        err_data = {
            "status": "error",
            "type": err_type,
            "code": code,
            "message": message,
        }
        if data:
            err_data["data"] = data
        await socket.send_json(err_data)
        await socket.close(code, message)
