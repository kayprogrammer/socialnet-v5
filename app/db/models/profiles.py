from enum import Enum
from app.api.utils.notification import get_notification_message
from app.db.models.accounts import User
from app.db.models.base import BaseModel
from tortoise import fields

class RequestStatusChoices(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"


class Friend(BaseModel):
    requester = fields.ForeignKeyField("models.User", related_name="requester_friends")
    requestee = fields.ForeignKeyField("models.User", related_name="requestee_friends")
    status = fields.CharEnumField(enum_type=RequestStatusChoices, max_length=20, default=RequestStatusChoices.PENDING)

    def __str__(self):
        return (
            f"{self.requester.full_name} & {self.requestee.full_name} --- {self.status}"
        )

    # So I'm supposed to do some bidirectional composite unique constraints somewhere around here but piccolo
    # has no provision currently for that (at least this  version) except by writing raw sql
    # in your migration files which is something I don't want to do. So I'll just focus on
    # doing very good validations. But there will be no db level constraints
    # I'll surely update this when they've updated the orm


class NotificationTypeChoices(Enum):
    REACTION = "REACTION"
    COMMENT = "COMMENT"
    REPLY = "REPLY"
    ADMIN = "ADMIN"


class Notification(BaseModel):
    sender = fields.ForeignKeyField("models.User", related_name="notifications_from")
    receivers = fields.ManyToManyField("models.User", related_name="notifications_to")
    ntype = fields.CharEnumField(enum_type=NotificationTypeChoices, max_length=100)
    post = fields.ForeignKeyField("models.Post", null=True)
    comment = fields.ForeignKeyField("models.Comment", null=True)
    reply = fields.ForeignKeyField("models.Reply", null=True)
    text = fields.CharField(max_length=100, null=True)
    read_by = fields.ManyToManyField("models.User")

    def __str__(self):
        return str(self.id)

    @property
    def message(self):
        text = self.text
        if not text:
            text = get_notification_message(self)
        return text

    # Set constraints
    class Meta:
        _space = "&ensp;&ensp;&nbsp;&nbsp;&nbsp;&nbsp;"
        constraints = [
            CheckConstraint(
                check=(Q(post__isnull=False, comment=None, reply=None))
                | (Q(post=None, comment__isnull=False, reply=None))
                | (Q(post=None, comment=None, reply__isnull=False))
                | (Q(post=None, comment=None, reply=None, ntype="ADMIN")),
                name="selected_object_constraints",
                violation_error_message=mark_safe(
                    f"""
                        * Cannot have cannot have post, comment, reply or any two of the three simultaneously. <br/>
                        {_space}* If the three are None, then it must be of type 'ADMIN'
                    """
                ),
            ),
            CheckConstraint(
                check=(Q(sender=None, ntype="ADMIN", text__isnull=False))
                | (Q(~Q(ntype="ADMIN"), sender__isnull=False, text=None)),
                name="sender_text_type_constraints",
                violation_error_message="If No Sender, type must be ADMIN and text must not be empty and vice versa.",
            ),
            CheckConstraint(
                check=(Q(Q(ntype="ADMIN") | Q(ntype="REACTION"), post__isnull=False))
                | (Q(Q(ntype="COMMENT") | Q(ntype="REACTION"), comment__isnull=False))
                | (Q(Q(ntype="REPLY") | Q(ntype="REACTION"), reply__isnull=False))
                | (Q(post=None, comment=None, reply=None, ntype="ADMIN")),
                name="post_comment_reply_type_constraints",
                violation_error_message=mark_safe(
                    f"""
                        * If Post, type must be ADMIN or REACTION. <br/>
                        {_space}* If Comment, type must be COMMENT or REACTION. <br/>
                        {_space}* If Reply, type must be REPLY or REACTION. <br/>
                    """
                ),
            ),
        ]
