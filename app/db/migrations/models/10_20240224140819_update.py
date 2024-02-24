from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "reaction" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "rtype" VARCHAR(20) NOT NULL,
    "comment_id" UUID REFERENCES "comment" ("id") ON DELETE SET NULL,
    "post_id" UUID REFERENCES "post" ("id") ON DELETE SET NULL,
    "reply_id" UUID REFERENCES "reply" ("id") ON DELETE SET NULL,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_reaction_user_id_7ee1a2" UNIQUE ("user_id", "post_id"),
    CONSTRAINT "uid_reaction_user_id_74f245" UNIQUE ("user_id", "comment_id"),
    CONSTRAINT "uid_reaction_user_id_74f245" UNIQUE ("user_id", "comment_id")
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "reaction";"""
