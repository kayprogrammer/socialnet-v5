from litestar import Request
from app.api.utils.auth import Authentication
from app.common.exception_handlers import ErrorCode, RequestError
from app.db.models.accounts import User


async def get_user(token):
    user = await Authentication.decodeAuthorization(token)
    if not user:
        raise RequestError(
            err_code=ErrorCode.INVALID_TOKEN,
            err_msg="Auth Token is Invalid or Expired",
            status_code=401,
        )
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
