from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "friend" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'PENDING',
    "requestee_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "requester_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_friend_request_946c65" UNIQUE ("requester_id", "requestee_id"),
    CONSTRAINT "uid_friend_request_946c65" UNIQUE ("requester_id", "requestee_id")
);
COMMENT ON COLUMN "friend"."status" IS 'PENDING: PENDING\nACCEPTED: ACCEPTED';
        CREATE TABLE IF NOT EXISTS "notification" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "ntype" VARCHAR(100) NOT NULL,
    "text" VARCHAR(100),
    "comment_id" UUID REFERENCES "comment" ("id") ON DELETE CASCADE,
    "post_id" UUID REFERENCES "post" ("id") ON DELETE CASCADE,
    "reply_id" UUID REFERENCES "reply" ("id") ON DELETE CASCADE,
    "sender_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "notification"."ntype" IS 'REACTION: REACTION\nCOMMENT: COMMENT\nREPLY: REPLY\nADMIN: ADMIN';
        CREATE TABLE "notification_user" (
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "notification_id" UUID NOT NULL REFERENCES "notification" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "notification_user";
        DROP TABLE IF EXISTS "friend";
        DROP TABLE IF EXISTS "notification";"""
