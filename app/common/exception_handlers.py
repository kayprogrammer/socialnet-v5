from http import HTTPStatus
from litestar import (
    Response,
    Request,
    status_codes,
)
from litestar.exceptions import HTTPException, ValidationException
from litestar.status_codes import HTTP_500_INTERNAL_SERVER_ERROR


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


class SocketError:
    def __init__(
        self,
        err_type: str,
        err_msg: str,
        code: int = 4000,
        data: dict = None,
    ) -> None:
        self.err_type = err_type
        self.code = code
        self.err_msg = err_msg
        self.data = data


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


def cut_sentence(sentence, target_word):
    words = sentence.split()
    index_of_target = words.index(target_word)
    truncated_sentence = " ".join(words[: index_of_target + 1])
    return truncated_sentence


def change_length_error_message(message):
    # Split the input string into words
    words = message.split()

    allowed_keywords = ["items", "item", "characters"]
    target_keyword = next((kw for kw in allowed_keywords if kw in message), "character")
    index_of_target = words.index(target_keyword)

    # Create the transformed string
    other_kw = "max" if "at most" in message else "min"
    transformed_string = f"{words[index_of_target - 1]} {target_keyword} {other_kw}"
    return transformed_string


def validation_exception_handler(_: Request, exc: ValidationException) -> Response:
    # Get the original 'detail' list of errors
    details = exc.extra
    print(details)
    modified_details = {}
    for error in details:
        # Modify messages
        err_msg = error["message"]
        if err_msg.startswith("Value error,"):
            err_msg = err_msg[13:]
        if "at most" in err_msg or "at least" in err_msg:
            err_msg = change_length_error_message(err_msg)
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
