from app.api.utils.tools import generate_random_alphanumeric_string
from app.core.config import settings
from app.core.security import get_password_hash
from tortoise import fields
from app.db.models.base import BaseModel
from datetime import datetime
from slugify import slugify
import random


class Country(BaseModel):
    name = fields.CharField(max_length=100)
    code = fields.CharField(max_length=100)


class Region(BaseModel):
    name = fields.CharField(max_length=100)
    country = fields.ForeignKeyField("models.Country", related_name="regions")


class City(BaseModel):
    name = fields.CharField(max_length=100)
    region = fields.ForeignKeyField("models.Region", related_name="cities")
    country = fields.ForeignKeyField("models.Country", related_name="cities")

    def __str__(self):
        return self.name

    @property
    def region_name(self):
        region = self.region
        return region.name if region else None

    @property
    def country_name(self):
        return self.country.name


class User(BaseModel):
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    username = fields.CharField(max_length=200)
    email = fields.CharField(max_length=500, unique=True)
    password = fields.CharField(max_length=500)
    avatar = fields.ForeignKeyField("models.File", on_delete=fields.SET_NULL, null=True)
    terms_agreement = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    is_email_verified = fields.BooleanField(default=False)
    is_staff = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)

    # Tokens
    access_token = fields.CharField(1000, null=True)
    refresh_token = fields.CharField(1000, null=True)

    # Profile Fields
    bio = fields.CharField(max_length=200, null=True)
    city = fields.ForeignKeyField("models.City", on_delete=fields.SET_NULL, null=True)
    dob = fields.DatetimeField(null=True)

    @classmethod
    async def create_user(cls, data):
        data["password"] = get_password_hash(data["password"])
        user = await cls.create(**data)
        return user

    async def save(self, *args, **kwargs):
        # Generate usename
        if not self._saved_in_db:
            self.username = await self.generate_username()
        return await super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    async def generate_username(self):
        username = self.username
        slugified_name = slugify(self.full_name)
        unique_username = username or slugified_name
        obj = await User.get_or_none(username=unique_username)
        if obj:  # username already taken
            # Make it unique and re-run the function
            unique_username = (
                f"{unique_username}-{generate_random_alphanumeric_string()}"
            )
            self.username = unique_username
            return await self.generate_username()
        return unique_username


class Otp(BaseModel):
    user = fields.ForeignKeyField("models.User", unique=True)
    code = fields.IntField()

    def check_expiration(self):
        now = datetime.utcnow()
        diff = now - self.updated_at.replace(tzinfo=None)
        if diff.total_seconds() > settings.EMAIL_OTP_EXPIRE_SECONDS:
            return True
        return False

    @classmethod
    async def update_or_create(cls, user_id):
        code = random.randint(100000, 999999)
        otp, created = await super().update_or_create(
            user_id=user_id, defaults={"code": code}
        )
        return otp
