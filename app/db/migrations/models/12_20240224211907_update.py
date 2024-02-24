from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "feedabstract";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ;"""
