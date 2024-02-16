from pydantic import BaseModel, validator, Field, EmailStr

from .base import ResponseSchema


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

    class Config:
        orm_mode = True


class SiteDetailResponseSchema(ResponseSchema):
    data: SiteDetailDataSchema
