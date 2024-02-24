from app.core.config import settings
from app.db.models.accounts import User
from app.db.models.feed import Post
from app.db.models.general import SiteDetail


class CreateData(object):
    async def initialize(self) -> None:
        await self.create_superuser()
        client_user = await self.create_client()
        await self.create_sitedetail()
        await self.create_post(client_user)

    async def create_superuser(self) -> None:
        user_dict = {
            "first_name": "Test",
            "last_name": "Admin",
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "admin": True,
            "superuser": True,
            "is_email_verified": True,
        }
        superuser = await User.get_or_create(
            email=settings.FIRST_SUPERUSER_EMAIL, defaults=user_dict
        )
        return superuser

    async def create_client(self) -> None:
        user_dict = {
            "first_name": "Test",
            "last_name": "Client",
            "password": settings.FIRST_CLIENT_PASSWORD,
            "is_email_verified": True,
        }
        client = await User.get_or_create(
            email=settings.FIRST_CLIENT_EMAIL, defaults=user_dict
        )
        return client

    async def create_sitedetail(self) -> None:
        sitedetail, created = await SiteDetail.get_or_create()
        return sitedetail

    async def create_post(self, client_user) -> None:
        post, created = await Post.get_or_create(
            author=client_user, text="This is the first post"
        )
        return post
