from pydantic import validator, Field, EmailStr
from app.api.schemas.schema_examples import UserExample, token_example
from .base import BaseModel, ResponseSchema


class RegisterUserSchema(BaseModel):
    first_name: str = Field(..., examples=[UserExample.first_name], max_length=50)
    last_name: str = Field(..., examples=[UserExample.last_name], max_length=50)
    email: EmailStr = Field(..., examples=[UserExample.email])
    password: str = Field(..., examples=[UserExample.password], min_length=8)
    terms_agreement: bool

    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.split(" ")) > 1:
            raise ValueError("No spacing allowed")
        return v

    @validator("terms_agreement")
    def validate_terms_agreement(cls, v):
        if not v:
            raise ValueError("You must agree to terms and conditions")
        return v

class VerifyOtpSchema(BaseModel):
    email: EmailStr = Field(..., examples=[UserExample.email])
    otp: int


class RequestOtpSchema(BaseModel):
    email: EmailStr = Field(..., examples=[UserExample.email])


class SetNewPasswordSchema(VerifyOtpSchema):
    password: str = Field(..., examples=["newstrongpassword"])

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("8 characters min!")
        return v


class LoginUserSchema(BaseModel):
    email: EmailStr = Field(..., examples=[UserExample.email])
    password: str = Field(..., examples=[UserExample.password])


class RefreshTokensSchema(BaseModel):
    refresh: str = Field(
        ...,
        examples=[token_example],
    )


class RegisterResponseSchema(ResponseSchema):
    data: RequestOtpSchema


class TokensResponseDataSchema(BaseModel):
    access: str = Field(
        ...,
        examples=[token_example],
    )
    refresh: str = Field(
        ...,
        examples=[token_example],
    )


class TokensResponseSchema(ResponseSchema):
    data: TokensResponseDataSchema
