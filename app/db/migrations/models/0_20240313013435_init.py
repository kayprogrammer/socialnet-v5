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
CREATE TABLE IF NOT EXISTS "country" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "code" VARCHAR(100) NOT NULL
);
CREATE TABLE IF NOT EXISTS "region" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "country_id" UUID NOT NULL REFERENCES "country" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "city" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "country_id" UUID NOT NULL REFERENCES "country" ("id") ON DELETE CASCADE,
    "region_id" UUID REFERENCES "region" ("id") ON DELETE CASCADE
);
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
);
CREATE TABLE IF NOT EXISTS "otp" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "code" INT NOT NULL,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "post" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "slug" VARCHAR(1000) NOT NULL UNIQUE,
    "author_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "image_id" UUID REFERENCES "file" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "comment" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "slug" VARCHAR(1000) NOT NULL UNIQUE,
    "author_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "post_id" UUID NOT NULL REFERENCES "post" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "reply" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT NOT NULL,
    "slug" VARCHAR(1000) NOT NULL UNIQUE,
    "author_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "comment_id" UUID NOT NULL REFERENCES "comment" ("id") ON DELETE CASCADE
);
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
);
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
    "sender_id" UUID REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "notification"."ntype" IS 'REACTION: REACTION\nCOMMENT: COMMENT\nREPLY: REPLY\nADMIN: ADMIN';
CREATE TABLE IF NOT EXISTS "chat" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100),
    "ctype" VARCHAR(10) NOT NULL  DEFAULT 'DM',
    "description" VARCHAR(1000),
    "image_id" UUID REFERENCES "file" ("id") ON DELETE SET NULL,
    "owner_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "chat"."ctype" IS 'DM: DM\nGROUP: GROUP';
CREATE TABLE IF NOT EXISTS "message" (
    "id" UUID NOT NULL  PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "text" TEXT,
    "chat_id" UUID NOT NULL REFERENCES "chat" ("id") ON DELETE CASCADE,
    "file_id" UUID REFERENCES "file" ("id") ON DELETE SET NULL,
    "sender_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "notification_user" (
    "notification_id" UUID NOT NULL REFERENCES "notification" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "notification_read_by" (
    "notification_id" UUID NOT NULL REFERENCES "notification" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "chat_user" (
    "chat_id" UUID NOT NULL REFERENCES "chat" ("id") ON DELETE CASCADE,
    "user_id" UUID NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
