from litestar import Litestar
from app.core.config import settings
from tortoise import Tortoise

TORTOISE_ORM = {
    "connections": {"default": settings.TORTOISE_DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "app.db.models.general"
            ],
            "default_connection": "default",
            "generated_modules": {
                "app.db.migrations": ["*"],  # You can customize this pattern
            },
        },
    },
}

async def init():
    await Tortoise.init(
        db_url=settings.TORTOISE_DATABASE_URL,
        modules={'models': [
            "app.db.models.base"
            "app.db.models.general"
        ]}
    )