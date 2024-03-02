from enum import Enum
from app.api.utils.file_processors import FileProcessor
from app.db.models.accounts import User
from app.db.models.base import BaseModel
from tortoise import fields


class ChatChoices(Enum):
    DM = "DM"
    GROUP = "GROUP"


class Chat(BaseModel):
    name = fields.CharField(max_length=100, null=True)
    owner = fields.ForeignKeyField("models.User", related_name="owned_chats")
    ctype = fields.CharEnumField(
        enum_type=ChatChoices, max_length=10, default=ChatChoices.DM
    )
    users: fields.ManyToManyRelation[User] = fields.ManyToManyField(
        "models.User", related_name="membered_chats"
    )
    description = fields.CharField(max_length=1000, null=True)
    image = fields.ForeignKeyField("models.File", on_delete=fields.SET_NULL, null=True)

    def __str__(self):
        return str(self.id)

    @property
    def get_image(self):
        image = self.image
        if image:
            return FileProcessor.generate_file_url(
                key=image.id,
                folder="chats",
                content_type=image.resource_type,
            )
        return None

    # So I'm supposed to do some check constraints somewhere around here but tortoise orm
    # has no provision currently for that (at least this  version) except by writing raw sql
    # in your migration files which is something I don't want to do. So I'll just focus on
    # doing very good validations. But there will be no db level constraints
    # I'll surely update this when they've updated the orm


class Message(BaseModel):
    sender = fields.ForeignKeyField("models.User", related_name="messages")
    chat = fields.ForeignKeyField("models.Chat", related_name="messages")
    text = fields.TextField(null=True)
    file = fields.ForeignKeyField("models.File", on_delete=fields.SET_NULL, null=True)

    async def save(self, *args, **kwargs):
        if not self._saved_in_db:
            await self.chat.save()  # So that chat updated_at can be updated
        return await super().save(*args, **kwargs)

    @property
    def get_file(self):
        file = self.file
        if file:
            return FileProcessor.generate_file_url(
                key=file.id,
                folder="messages",
                content_type=file.resource_type,
            )
        return None
