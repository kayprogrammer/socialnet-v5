from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" ADD "sender_id" UUID NOT NULL;
        ALTER TABLE "message" ADD "chat_id" UUID NOT NULL;
        ALTER TABLE "message" ADD "file_id" UUID;
        ALTER TABLE "message" ADD CONSTRAINT "fk_message_file_73c198d3" FOREIGN KEY ("file_id") REFERENCES "file" ("id") ON DELETE SET NULL;
        ALTER TABLE "message" ADD CONSTRAINT "fk_message_user_3a8687bc" FOREIGN KEY ("sender_id") REFERENCES "user" ("id") ON DELETE CASCADE;
        ALTER TABLE "message" ADD CONSTRAINT "fk_message_chat_9538747f" FOREIGN KEY ("chat_id") REFERENCES "chat" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "message" DROP CONSTRAINT "fk_message_chat_9538747f";
        ALTER TABLE "message" DROP CONSTRAINT "fk_message_user_3a8687bc";
        ALTER TABLE "message" DROP CONSTRAINT "fk_message_file_73c198d3";
        ALTER TABLE "message" DROP COLUMN "sender_id";
        ALTER TABLE "message" DROP COLUMN "chat_id";
        ALTER TABLE "message" DROP COLUMN "file_id";"""
