import asyncio, os, sys, logging

sys.path.append(os.path.abspath("./"))  # To single-handedly execute this script

from tortoise import Tortoise

from app.db.config import TORTOISE_ORM
from initials.data_script import CreateData
from tortoise.connection import connections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    create_data = CreateData()
    await create_data.initialize()


async def main() -> None:
    # Initialize DB
    await Tortoise.init(config=TORTOISE_ORM)
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")
    # Close connections
    await connections.close_all()


if __name__ == "__main__":
    asyncio.run(main())
