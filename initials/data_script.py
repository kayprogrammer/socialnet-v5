from app.core.config import settings
from app.db.models.accounts import City, Country, Region, User
from app.db.models.feed import Post
from app.db.models.general import SiteDetail


class CreateData(object):
    async def initialize(self) -> None:
        city_id = (await self.create_city()).id
        await self.create_superuser(city_id)
        client_user = await self.create_client(city_id)
        await self.create_sitedetail()
        await self.create_post(client_user)

    async def create_city(self) -> None:
        country, created = await Country.get_or_create(name="Nigeria", code="NG")
        region, created = await Region.get_or_create(
            name="Lagos", defaults={"country_id": country.id}
        )
        city, created = await City.get_or_create(
            name="Lekki", defaults={"region_id": region.id, "country_id": country.id}
        )
        return city

    async def create_superuser(self, city_id) -> None:
        user_dict = {
            "first_name": "Test",
            "last_name": "Admin",
            "password": settings.FIRST_SUPERUSER_PASSWORD,
            "is_staff": True,
            "is_superuser": True,
            "is_email_verified": True,
            "city_id": city_id,
        }
        superuser = await User.get_or_create(
            email=settings.FIRST_SUPERUSER_EMAIL, defaults=user_dict
        )
        return superuser

    async def create_client(self, city_id) -> None:
        user_dict = {
            "first_name": "Test",
            "last_name": "Client",
            "password": settings.FIRST_CLIENT_PASSWORD,
            "is_email_verified": True,
            "city_id": city_id,
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
