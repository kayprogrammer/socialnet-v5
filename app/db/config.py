from app.core.config import settings
from tortoise import Tortoise
from tortoise.connection import connections

MODELS = [
    "app.db.models.base",
    "app.db.models.general",
    "app.db.models.accounts",
]

DB_URL = settings.TORTOISE_DATABASE_URL

TORTOISE_ORM = {
    "connections": {"default": DB_URL},
    "apps": {
        "models": {
            "models": MODELS
            + [
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}


async def init_tortoise():
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": MODELS},
    )


async def shutdown_tortoise() -> None:
    await connections.close_all()
