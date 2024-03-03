from typing import Optional, Union
from litestar import Request, WebSocket
from litestar.exceptions import WebSocketException
from app.api.utils.auth import Authentication
from app.common.exception_handlers import ErrorCode, RequestError
from app.core.config import settings
from app.db.models.accounts import User


async def get_user(token, websocket: Optional[WebSocket] = None):
    user = await Authentication.decodeAuthorization(token)
    if not user:
        err_msg = "Auth Token is Invalid or Expired"
        if not websocket:
            raise RequestError(
                err_code=ErrorCode.INVALID_TOKEN,
                err_msg=err_msg,
                status_code=401,
            )
        await websocket.send_json(
            {
                "status": "error",
                "type": ErrorCode.INVALID_TOKEN,
                "code": 4001,
                "message": err_msg,
            }
        )
        raise WebSocketException(detail=err_msg, code=4001)
    return user


async def get_current_user(request: Request) -> User:
    token = request.headers.get("authorization")
    if not token or len(token) < 10:
        raise RequestError(
            err_code=ErrorCode.UNAUTHORIZED_USER,
            err_msg="Unauthorized User!",
            status_code=401,
        )
    return await get_user(token)


async def get_current_user_or_guest(
    request: Request,
) -> Optional[User]:
    token = request.headers.get("authorization")
    if not token or len(token) < 10:
        return None
    return await get_user(token)

async def get_current_socket_user(
    websocket: WebSocket,
) -> Union[User, str]:
    await websocket.accept()
    token = websocket.headers.get("authorization")
    # Return user or socket secret key
    if not token:
        err_msg = "Unauthorized User!"
        await websocket.send_json(
            {
                "status": "error",
                "type": ErrorCode.UNAUTHORIZED_USER,
                "code": 4001,
                "message": err_msg,
            }
        )
        raise WebSocketException(code=4001, detail=err_msg)
    if token == settings.SOCKET_SECRET:
        return token
    return await get_user(token, websocket)
