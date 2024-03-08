from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "notificationreadby";
        DROP TABLE IF EXISTS "chat_user";
        DROP TABLE IF EXISTS "notificationreadby";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE "chat_user" (
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "chat_id" UUID NOT NULL REFERENCES "chat" ("id") ON DELETE CASCADE
);
        CREATE TABLE "notificationreadby" (
    "notification_id" UUID NOT NULL REFERENCES "notification" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);"""
