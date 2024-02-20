from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import AnyUrl, EmailStr, validator
from pydantic_settings import BaseSettings

PROJECT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # DEBUG
    DEBUG: bool

    # TOKENS
    EMAIL_OTP_EXPIRE_SECONDS: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    # SECURITY
    SECRET_KEY: str
    SOCKET_SECRET: str

    # PROJECT DETAILS
    PROJECT_NAME: str
    FRONTEND_URL: str
    CORS_ALLOWED_ORIGINS: Union[List, str]
    ALLOWED_HOSTS: Union[List, str]

    # POSTGRESQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    TORTOISE_DATABASE_URL: str = None

    # FIRST SUPERUSER
    FIRST_SUPERUSER_EMAIL: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # FIRST AUCTIONEER
    FIRST_CLIENT_EMAIL: EmailStr
    FIRST_CLIENT_PASSWORD: str

    # EMAIL CONFIG
    MAIL_SENDER_EMAIL: str
    MAIL_SENDER_PASSWORD: str
    MAIL_SENDER_HOST: str
    MAIL_SENDER_PORT: int

    # CLOUDINARY CONFIG
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    @validator("CORS_ALLOWED_ORIGINS", "ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        return v.split()

    @validator("TORTOISE_DATABASE_URL", pre=True)
    def assemble_postgres_connection(
        cls, v: Optional[str], values: Dict[str, str]
    ) -> str:
        # Assemble postgres url
        if isinstance(v, str):
            return v
        postgres_server = values.get("POSTGRES_SERVER")
        if values.get("DEBUG"):
            postgres_server = "localhost"

        return str(
            AnyUrl.build(
                scheme="postgres",
                username=values.get("POSTGRES_USER"),
                password=values.get("POSTGRES_PASSWORD"),
                host=postgres_server,
                port=values.get("POSTGRES_PORT"),
                path=values.get("POSTGRES_DB"),
            )
        )

    class Config:
        env_file = f"{PROJECT_DIR}/.env"
        case_sensitive = True


settings: Settings = Settings()
