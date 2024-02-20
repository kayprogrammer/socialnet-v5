from http import HTTPStatus
from litestar import (
    Response,
    Request,
    status_codes,
)
from litestar.exceptions import HTTPException, ValidationException
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR

from app.api.utils.tools import cut_sentence


class ErrorCode:
    UNAUTHORIZED_USER = "unauthorized_user"
    NETWORK_FAILURE = "network_failure"
    SERVER_ERROR = "server_error"
    INVALID_ENTRY = "invalid_entry"
    INCORRECT_EMAIL = "incorrect_email"
    INCORRECT_OTP = "incorrect_otp"
    EXPIRED_OTP = "expired_otp"
    INVALID_AUTH = "invalid_auth"
    INVALID_TOKEN = "invalid_token"
    INVALID_CREDENTIALS = "invalid_credentials"
    UNVERIFIED_USER = "unverified_user"
    NON_EXISTENT = "non_existent"
    INVALID_OWNER = "invalid_owner"
    INVALID_PAGE = "invalid_page"
    INVALID_VALUE = "invalid_value"
    NOT_ALLOWED = "not_allowed"
    INVALID_DATA_TYPE = "invalid_data_type"
    BAD_REQUEST = "bad_request"


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class RequestError(Error):
    def __init__(
        self,
        err_code: str,
        err_msg: str,
        status_code: int = 400,
        data: dict = None,
        *args: object,
    ) -> None:
        self.status_code = HTTPStatus(status_code)
        self.err_code = err_code
        self.err_msg = err_msg
        self.data = data

        super().__init__(*args)


def request_error_handler(_: Request, exc: RequestError):
    err_dict = {
        "status": "failure",
        "code": exc.err_code,
        "message": exc.err_msg,
    }
    if exc.data:
        err_dict["data"] = exc.data
    return Response(status_code=exc.status_code, content=err_dict)


def http_exception_handler(_: Request, exc: HTTPException) -> Response:
    return Response(
        content={"status": "failure", "message": exc.detail},
        status_code=exc.status_code,
    )


def validation_exception_handler(_: Request, exc: ValidationException) -> Response:
    # Get the original 'detail' list of errors
    details = exc.extra
    modified_details = {}
    for error in details:
        # Modify messages
        err_msg = error["message"]
        if err_msg.startswith("Value error,"):
            err_msg = err_msg[13:]
        at_most = "at most"
        at_least = "at least"
        if at_most in err_msg:
            err_msg = f"{cut_sentence(err_msg, at_most)} max"
        elif at_least in err_msg:
            err_msg = f"{cut_sentence(err_msg, at_least)} min"
        modified_details[error["key"]] = err_msg
    return Response(
        status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "failure",
            "message": "Invalid Entry",
            "data": modified_details,
        },
    )


def internal_server_error_handler(_: Request, exc: Exception) -> Response:
    print(exc)
    return Response(
        content={
            "status": "failure",
            "message": "Server Error",
        },
        status_code=500,
    )


exc_handlers = {
    ValidationException: validation_exception_handler,
    HTTPException: http_exception_handler,
    HTTP_500_INTERNAL_SERVER_ERROR: internal_server_error_handler,
    RequestError: request_error_handler,
}
