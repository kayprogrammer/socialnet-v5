from tortoise import fields
from .base import BaseModel


class SiteDetail(BaseModel):
    name = fields.CharField(max_length=300, default="SocialNet")
    email = fields.CharField(default="kayprogrammer1@gmail.com")
    phone = fields.CharField(max_length=300, default="+2348133831036")
    address = fields.CharField(max_length=300, default="234, Lagos, Nigeria")
    fb = fields.CharField(max_length=300, default="https://facebook.com")
    tw = fields.CharField(max_length=300, default="https://twitter.com")
    wh = fields.CharField(
        max_length=300,
        default="https://wa.me/2348133831036",
    )
    ig = fields.CharField(max_length=300, default="https://instagram.com")

    def __str__(self):
        return self.name
