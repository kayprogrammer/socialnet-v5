import json
from litestar.handlers import WebsocketListener
from litestar.exceptions import WebSocketException
from litestar import WebSocket

from app.common.exception_handlers import ErrorCode


class BaseSocketConnectionHandler(WebsocketListener):
    active_connections: list[WebSocket] = []

    async def on_accept(self, socket: WebSocket) -> None:
        print("Connection accepted")
        self.active_connections.append(socket)

    def on_disconnect(self, code: int, reason: str) -> None:
        print("Connection closed")
        raise WebSocketException(detail=reason, code=code)

    async def on_receive(self, socket: WebSocket, data: str):
        try:
            data = json.loads(data)
        except json.decoder.JSONDecodeError:
            await self.send_error_data(
                socket, "Invalid JSON", ErrorCode.INVALID_DATA_TYPE
            )
        return data

    async def send_personal_message(self, data: dict, websocket: WebSocket):
        await websocket.send_json(data)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

    async def send_error_data(
        self,
        websocket: WebSocket,
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
        await websocket.send_json(err_data)
        self.on_disconnect(code, message)
