from litestar.testing import AsyncTestClient
from asgi_lifespan import LifespanManager
from app.db.config import MODELS
from app.db.models.accounts import User
from tortoise import Tortoise
from app.api.utils.auth import Authentication
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor
import pytest, asyncio, os
from app.main import app

os.environ["ENVIRONMENT"] = "testing"
test_db = factories.postgresql_proc(port=None, dbname="test_db")


# GENERAL FIXTURES
@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_url(test_db):
    pg_host = test_db.host
    pg_port = test_db.port
    pg_user = test_db.user
    pg_db = test_db.dbname
    pg_password = test_db.password

    with DatabaseJanitor(
        pg_user, pg_host, pg_port, pg_db, test_db.version, pg_password
    ):
        url = f"postgres://{pg_user}:@{pg_host}:{pg_port}/{pg_db}"
        yield url


@pytest.fixture(autouse=True)
async def setup_db(db_url, mocker):
    mocker.patch("app.db.config.DB_URL", new=db_url)
    await Tortoise.init(
        db_url=db_url,
        modules={"models": MODELS},
    )
    # await Tortoise._drop_databases()
    await Tortoise.generate_schemas()


@pytest.fixture
async def client():
    async with LifespanManager(app):
        async with AsyncTestClient(app=app) as client:
            yield client


# -----------------------------------------------------------------------


# AUTH FIXTURES
@pytest.fixture
async def test_user():
    user = await User.create_user(
        first_name="Test",
        last_name="Name",
        email="test@example.com",
        password="testpassword",
    )
    return user


@pytest.fixture
async def verified_user():
    user = await User.create_user(
        first_name="Test",
        last_name="Verified",
        email="testverifieduser@example.com",
        password="testpassword",
        is_email_verified=True,
    )
    return user


@pytest.fixture
async def another_verified_user():
    user = await User.create_user(
        first_name="AnotherTest",
        last_name="UserVerified",
        email="anothertestverifieduser@example.com",
        password="anothertestverifieduser123",
        is_email_verified=True,
    )
    return user


@pytest.fixture
async def authorized_client(verified_user: User, client: AsyncTestClient):
    verified_user.access_token = await Authentication.create_access_token(
        {"user_id": str(verified_user.id), "username": verified_user.username}
    )
    verified_user.refresh_token = await Authentication.create_refresh_token()
    await verified_user.save()
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {verified_user.access_token}",
    }
    return client


@pytest.fixture
async def another_authorized_client(
    another_verified_user: User, client: AsyncTestClient
):
    another_verified_user.access_token = await Authentication.create_access_token(
        {
            "user_id": str(another_verified_user.id),
            "username": another_verified_user.username,
        }
    )
    another_verified_user.refresh_token = await Authentication.create_refresh_token()
    await another_verified_user.save()
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {another_verified_user.access_token}",
    }
    return client


# -----------------------------------------------------------------------
