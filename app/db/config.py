from litestar import Litestar
from contextlib import asynccontextmanager
from app.core.config import settings
from tortoise import Tortoise
from tortoise.connection import connections
import logging, os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS = [
    "app.db.models.base",
    "app.db.models.general",
    "app.db.models.accounts",
    "app.db.models.feed",
    "app.db.models.profiles",
    "app.db.models.chat",
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
    if os.environ.get("ENVIRONMENT") == "testing":
        # Testing env
        await Tortoise.generate_schemas()
    logger.info("Initialized Tortoise ORM")
    yield
    await connections.close_all()
    logger.info("Closed Tortoise ORM connections")
