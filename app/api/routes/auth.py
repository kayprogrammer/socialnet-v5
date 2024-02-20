from litestar import Controller, get, post

from app.api.schemas.auth import (
    RegisterUserSchema,
    VerifyOtpSchema,
    RequestOtpSchema,
    SetNewPasswordSchema,
    LoginUserSchema,
    RefreshTokensSchema,
    RegisterResponseSchema,
    TokensResponseSchema,
)
from app.common.exception_handlers import ErrorCode, RequestError
from app.api.schemas.base import ResponseSchema

from app.api.utils.emails import send_email
from app.core.security import get_password_hash, verify_password
from app.api.utils.auth import Authentication
from app.db.models.accounts import Otp, User


class RegisterView(Controller):
    path = "/register"

    @post(
        summary="Register a new user",
        description="This endpoint registers new users into our application",
    )
    async def register(self, data: RegisterUserSchema) -> RegisterResponseSchema:
        # Check for existing user
        existing_user = await User.get_or_none(email=data.email)
        if existing_user:
            raise RequestError(
                err_code=ErrorCode.INVALID_ENTRY,
                err_msg="Invalid Entry",
                status_code=422,
                data={"email": "Email already registered!"},
            )

        # Create user
        user = await User.create_user(data.dict())

        # Send verification email
        await send_email(user, "activate")

        return RegisterResponseSchema(
            message="Registration successful", data={"email": user.email}
        )


class VerifyEmailView(Controller):
    path = "/verify-email"

    @post(
        summary="Verify a user's email",
        description="This endpoint verifies a user's email",
        status_code=200,
    )
    async def verify_email(self, data: VerifyOtpSchema) -> ResponseSchema:
        user_by_email = await User.get_or_none(email=data.email)

        if not user_by_email:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )

        if user_by_email.is_email_verified:
            return ResponseSchema(message="Email already verified")

        otp = await Otp.get_or_none(user_id=user_by_email.id)
        if not otp or otp.code != data.otp:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_OTP,
                err_msg="Incorrect Otp",
                status_code=404,
            )
        if otp.check_expiration():
            err_code = (ErrorCode.EXPIRED_OTP,)
            raise RequestError(err_msg="Expired Otp")

        user_by_email.is_email_verified = True
        await user_by_email.save()
        await otp.delete()
        # Send welcome email
        await send_email(user_by_email, "welcome")
        return ResponseSchema(message="Account verification successful")


class ResendVerificationEmailView(Controller):
    path = "/resend-verification-email"

    @post(
        summary="Resend Verification Email",
        description="This endpoint resends new otp to the user's email",
        status_code=200,
    )
    async def resend_verification_email(self, data: RequestOtpSchema) -> ResponseSchema:
        user_by_email = await User.get_or_none(email=data.email)
        if not user_by_email:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )
        if user_by_email.is_email_verified:
            return ResponseSchema(message="Email already verified")

        # Send verification email
        await send_email(user_by_email, "activate")
        return ResponseSchema(message="Verification email sent")


class SendPasswordResetOtpView(Controller):
    path = "/send-password-reset-otp"

    @post(
        summary="Send Password Reset Otp",
        description="This endpoint sends new password reset otp to the user's email",
        status_code=200,
    )
    async def send_password_reset_otp(self, data: RequestOtpSchema) -> ResponseSchema:
        user_by_email = await User.get_or_none(email=data.email)
        if not user_by_email:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )

        # Send password reset email
        await send_email(user_by_email, "reset")
        return ResponseSchema(message="Password otp sent")


class SetNewPasswordView(Controller):
    path = "/set-new-password"

    @post(
        summary="Set New Password",
        description="This endpoint verifies the password reset otp",
        status_code=200,
    )
    async def set_new_password(self, data: SetNewPasswordSchema) -> ResponseSchema:
        email = data.email
        otp_code = data.otp
        password = data.password

        user_by_email = await User.get_or_none(email=email)
        if not user_by_email:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_EMAIL,
                err_msg="Incorrect Email",
                status_code=404,
            )

        otp = await Otp.get_or_none(user_id=user_by_email.id)
        if not otp or otp.code != otp_code:
            raise RequestError(
                err_code=ErrorCode.INCORRECT_OTP,
                err_msg="Incorrect Otp",
                status_code=404,
            )

        if otp.check_expiration():
            raise RequestError(err_code=ErrorCode.EXPIRED_OTP, err_msg="Expired Otp")

        user_by_email.password = get_password_hash(password)
        await user_by_email.save()
        # Send password reset success email
        await send_email(user_by_email, "reset-success")
        return ResponseSchema(message="Password reset successful")


class LoginView(Controller):
    path = "/login"

    @post(
        summary="Login a user",
        description="This endpoint generates new access and refresh tokens for authentication",
    )
    async def login(
        self,
        data: LoginUserSchema,
    ) -> TokensResponseSchema:
        email = data.email
        plain_password = data.password
        user = await User.get_or_none(email=email)
        if not user or verify_password(plain_password, user.password) == False:
            raise RequestError(
                err_code=ErrorCode.INVALID_CREDENTIALS,
                err_msg="Invalid credentials",
                status_code=401,
            )

        if not user.is_email_verified:
            raise RequestError(
                err_code=ErrorCode.UNVERIFIED_USER,
                err_msg="Verify your email first",
                status_code=401,
            )

        # Create tokens and update in db
        user.access_token = await Authentication.create_access_token(
            {"user_id": str(user.id), "username": user.username}
        )
        user.refresh_token = await Authentication.create_refresh_token()
        await user.save()
        return TokensResponseSchema(
            message="Login successful",
            data={"access": user.access_token, "refresh": user.refresh_token},
        )


class RefreshTokensView(Controller):
    path = "/refresh"

    @post(
        summary="Refresh tokens",
        description="This endpoint refresh tokens by generating new access and refresh tokens for a user",
    )
    async def refresh(self, data: RefreshTokensSchema) -> TokensResponseSchema:
        token = data.refresh
        user = await User.get_or_none(refresh_token=token)
        if not user or not (await Authentication.decode_jwt(token)):
            raise RequestError(
                err_code=ErrorCode.INVALID_TOKEN,
                err_msg="Refresh token is invalid or expired",
                status_code=401,
            )

        user.access_token = await Authentication.create_access_token(
            {"user_id": str(user.id), "username": user.username}
        )
        user.refresh_token = await Authentication.create_refresh_token()
        await user.save()

        return TokensResponseSchema(
            message="Tokens refresh successful",
            data={"access": user.access_token, "refresh": user.refresh_token},
        )


class LogoutView(Controller):
    path = "/logout"

    @get(
        summary="Logout a user",
        description="This endpoint logs a user out from our application",
    )
    async def logout(self, user: User) -> ResponseSchema:
        user.access_token = user.refresh_token = None
        await user.save()
        return ResponseSchema(message="Logout successful")


auth_handlers = [
    RegisterView,
    VerifyEmailView,
    ResendVerificationEmailView,
    SendPasswordResetOtpView,
    SetNewPasswordView,
    LoginView,
    RefreshTokensView,
    LogoutView,
]
