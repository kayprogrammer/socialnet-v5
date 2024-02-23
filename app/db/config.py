from litestar import Litestar
from contextlib import asynccontextmanager
from app.core.config import settings
from tortoise import Tortoise
from tortoise.connection import connections

MODELS = [
    "app.db.models.base",
    "app.db.models.general",
    "app.db.models.accounts",
]

TORTOISE_ORM = {
    "connections": {"default": settings.TORTOISE_DATABASE_URL},
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


@asynccontextmanager
async def lifespan(app: Litestar):
    await Tortoise.init(config=TORTOISE_ORM)
    yield
    await connections.close_all()
