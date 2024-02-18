from pydantic import validator, Field, EmailStr

from .base import BaseModel, ResponseSchema


# Site Details
class SiteDetailDataSchema(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str
    fb: str
    tw: str
    wh: str
    ig: str


class SiteDetailResponseSchema(ResponseSchema):
    data: SiteDetailDataSchema
