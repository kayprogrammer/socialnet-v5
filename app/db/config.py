from app.core.config import settings
from tortoise import Tortoise
from tortoise.connection import connections

TORTOISE_ORM = {
    "connections": {"default": settings.TORTOISE_DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "app.db.models.base",
                "app.db.models.general",
                "app.db.models.accounts",
                "aerich.models"
            ],
            "default_connection": "default",
        },
    },
}

async def init_tortoise():
    await Tortoise.init(
        db_url=settings.TORTOISE_DATABASE_URL,
        modules={'models': [
            "app.db.models.base",
            "app.db.models.general",
        ]}
    )

async def shutdown_tortoise() -> None:
    await connections.close_all()