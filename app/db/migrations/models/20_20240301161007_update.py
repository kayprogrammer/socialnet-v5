from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE "notification_user" (
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "notification_id" UUID NOT NULL REFERENCES "notification" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "notification_user";
        DROP TABLE IF EXISTS "chat_user";"""
