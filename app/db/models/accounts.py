from datetime import datetime
import random
from app.core.config import settings
from tortoise import fields
from app.db.models.base import BaseModel


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
    async def get_or_create(cls, user_id):
        code = random.randint(100000, 999999)
        otp = await super().get_or_create(user_id=user_id, defaults={"code": code})
        return otp
