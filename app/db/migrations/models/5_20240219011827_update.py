from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "username" VARCHAR(200) NOT NULL,
    "email" VARCHAR(500) NOT NULL UNIQUE,
    "password" VARCHAR(500) NOT NULL,
    "terms_agreement" BOOL NOT NULL  DEFAULT False,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_email_verified" BOOL NOT NULL  DEFAULT False,
    "is_staff" BOOL NOT NULL  DEFAULT False,
    "is_superuser" BOOL NOT NULL  DEFAULT False,
    "access_token" VARCHAR(1000),
    "refresh_token" VARCHAR(1000),
    "bio" VARCHAR(200),
    "dob" TIMESTAMPTZ,
    "avatar_id" UUID REFERENCES "file" ("id") ON DELETE SET NULL,
    "city_id" UUID REFERENCES "city" ("id") ON DELETE SET NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "user";"""
