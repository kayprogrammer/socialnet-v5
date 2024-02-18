from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "file" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "resource_type" VARCHAR(20) NOT NULL
);
CREATE TABLE IF NOT EXISTS "sitedetail" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(300) NOT NULL  DEFAULT 'SocialNet',
    "email" VARCHAR(1000) NOT NULL  DEFAULT 'kayprogrammer1@gmail.com',
    "phone" VARCHAR(300) NOT NULL  DEFAULT '+2348133831036',
    "address" VARCHAR(300) NOT NULL  DEFAULT '234, Lagos, Nigeria',
    "fb" VARCHAR(300) NOT NULL  DEFAULT 'https://facebook.com',
    "tw" VARCHAR(300) NOT NULL  DEFAULT 'https://twitter.com',
    "wh" VARCHAR(300) NOT NULL  DEFAULT 'https://wa.me/2348133831036',
    "ig" VARCHAR(300) NOT NULL  DEFAULT 'https://instagram.com'
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
