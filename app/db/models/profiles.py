from enum import Enum
from app.api.utils.notification import get_notification_message
from app.db.models.base import BaseModel
from tortoise import fields


class RequestStatusChoices(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"


class Friend(BaseModel):
    requester = fields.ForeignKeyField("models.User", related_name="requester_friends")
    requestee = fields.ForeignKeyField("models.User", related_name="requestee_friends")
    status = fields.CharEnumField(
        enum_type=RequestStatusChoices,
        max_length=20,
        default=RequestStatusChoices.PENDING,
    )

    def __str__(self):
        return (
            f"{self.requester.full_name} & {self.requestee.full_name} --- {self.status}"
        )

    class Meta:
        # This version of the tortoise orm cannot create bidirectional unique constraints
        # And this is the latest version as at the time this project was built.
        # So help me manage this abeg.
        unique_together = (("requester", "requestee"), ("requester", "requestee"))


class NotificationTypeChoices(Enum):
    REACTION = "REACTION"
    COMMENT = "COMMENT"
    REPLY = "REPLY"
    ADMIN = "ADMIN"


class Notification(BaseModel):
    sender = fields.ForeignKeyField(
        "models.User", related_name="notifications_from", null=True
    )
    receivers = fields.ManyToManyField(
        "models.User", related_name="notifications_to", null=True
    )
    ntype = fields.CharEnumField(enum_type=NotificationTypeChoices, max_length=100)
    post = fields.ForeignKeyField("models.Post", null=True)
    comment = fields.ForeignKeyField("models.Comment", null=True)
    reply = fields.ForeignKeyField("models.Reply", null=True)
    text = fields.CharField(max_length=100, null=True)
    read_by = fields.ManyToManyField(
        "models.User", related_name="notifications_read", null=True
    )

    def __str__(self):
        return str(self.id)

    @property
    def message(self):
        text = self.text
        if not text:
            text = get_notification_message(self)
        return text

    async def user_is_read(self, user_id):
        return await self.read_by.filter(id=user_id).exists()

    # So I'm supposed to do some check constraints somewhere around here but tortoise orm
    # has no provision currently for that (at least this  version) except by writing raw sql
    # in your migration files which is something I don't want to do. So I'll just focus on
    # doing very good validations. But there will be no db level constraints
    # I'll surely update this when they've updated the orm
