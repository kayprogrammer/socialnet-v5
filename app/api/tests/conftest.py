from litestar.testing import AsyncTestClient
from app.db.config import TORTOISE_ORM
from app.db.models.accounts import City, Country, Region, User
from tortoise import Tortoise
from tortoise.connection import connections

from app.api.utils.auth import Authentication
import pytest, asyncio, os
from app.db.models.chat import Chat, Message
from app.db.models.feed import Comment, Post, Reaction, Reply
from app.db.models.profiles import Friend
from app.main import app

os.environ["ENVIRONMENT"] = "testing"


# GENERAL FIXTURES
@pytest.fixture(scope="session")
def event_loop():
    """Overrides pytest default function scoped event loop"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_conf():
    NEW_ORM_CONF = TORTOISE_ORM
    NEW_ORM_CONF["connections"]["default"] = "sqlite://:memory:"
    yield NEW_ORM_CONF


@pytest.fixture()
async def setup_db(db_conf):
    await Tortoise.init(config=db_conf)
    await Tortoise.generate_schemas()
    yield
    await connections.close_all()
    await Tortoise._drop_databases()


@pytest.fixture()
async def client(mocker, db_conf, setup_db):
    mocker.patch("app.db.config.TORTOISE_ORM", new=db_conf)

    async with AsyncTestClient(app=app) as client:
        yield client


# -----------------------------------------------------------------------


# AUTH FIXTURES
@pytest.fixture
async def test_user():
    user_dict = {
        "first_name": "Test",
        "last_name": "Name",
        "email": "test@example.com",
        "password": "testpassword",
    }
    user = await User.create_user(user_dict)
    return user


@pytest.fixture()
async def verified_user():
    user_dict = {
        "first_name": "Test",
        "last_name": "Verified",
        "email": "testverifieduser@example.com",
        "password": "testpassword",
        "is_email_verified": True,
    }
    user = await User.create_user(user_dict)
    return user


@pytest.fixture
async def another_verified_user():
    user_dict = {
        "first_name": "AnotherTest",
        "last_name": "UserVerified",
        "email": "anothertestverifieduser@example.com",
        "password": "anothertestverifieduser123",
        "is_email_verified": True,
    }
    user = await User.create_user(user_dict)
    return user


@pytest.fixture
async def authorized_client(client: AsyncTestClient, verified_user: User):
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
async def another_verified_user_tokens(another_verified_user: User):
    access = await Authentication.create_access_token(
        {
            "user_id": str(another_verified_user.id),
            "username": another_verified_user.username,
        }
    )
    refresh = await Authentication.create_refresh_token()
    another_verified_user.access_token = access
    another_verified_user.refresh_token = refresh
    await another_verified_user.save()
    return {"access": access, "refresh": refresh}


@pytest.fixture
async def another_authorized_client(
    client: AsyncTestClient, another_verified_user_tokens
):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {another_verified_user_tokens['access']}",
    }
    return client


# -----------------------------------------------------------------------


# PROFILE FIXTURES
@pytest.fixture
async def city():
    country = await Country.create(name="TestCountry", code="TC")
    region = await Region.create(name="TestRegion", country=country)
    city = await City.create(name="TestCity", region=region, country=country)
    return city


@pytest.fixture
async def friend(verified_user: User, another_verified_user: User):
    friend = await Friend.create(
        status="ACCEPTED",
        requester=verified_user,
        requestee=another_verified_user,
    )
    return friend


# -------------------------------------------------------------------------------


# CHAT FIXTURES
@pytest.fixture
async def chat(verified_user, another_verified_user):
    # Create Chat
    chat = await Chat.create(ctype="DM", owner=verified_user)
    await chat.users.add(another_verified_user)
    return chat


@pytest.fixture
async def group_chat(verified_user, another_verified_user):
    # Create Group Chat
    chat = await Chat.create(
        owner=verified_user,
        name="My New Group",
        ctype="GROUP",
        description="This is the description of my group chat",
    )
    await chat.users.add(another_verified_user)
    return chat


@pytest.fixture
async def message(chat):
    # Create Message
    message = await Message.create(chat=chat, sender=chat.owner, text="Hello Boss")
    return message


# -------------------------------------------------------------------------------


# FEED FIXTURES
@pytest.fixture
async def post(verified_user):
    # Create Post
    post = await Post.create(text="This is a nice new platform", author=verified_user)
    return post


@pytest.fixture
async def reaction(post):
    # Create Reaction
    author = post.author
    reaction = await Reaction.create(rtype="LIKE", user=author, post=post)
    return reaction


@pytest.fixture
async def comment(post):
    # Create Comment
    author = post.author
    comment = await Comment.create(text="Just a comment", author=author, post=post)
    comment.reactions_count = 0
    comment.replies_count = 0
    return comment


@pytest.fixture
async def reply(comment):
    # Create Reply
    author = comment.author
    reply = await Reply.create(text="Simple reply", author=author, comment=comment)
    reply.reactions_count = 0
    return reply


# -------------------------------------------------------------------------------
