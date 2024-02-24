from enum import Enum
from slugify import slugify
from app.api.utils.file_processors import FileProcessor
from app.db.models.base import BaseModel
from tortoise import fields


class ReactionChoices(Enum):
    LIKE = "LIKE"
    LOVE = "LOVE"
    HAHA = "HAHA"
    WOW = "WOW"
    SAD = "SAD"
    ANGRY = "ANGRY"


class FeedAbstract(BaseModel):
    author = fields.ForeignKeyField("models.User")
    text = fields.TextField()
    slug = fields.CharField(max_length=1000, unique=True)

    class Meta:
        abstract = True

    async def save(self, *args, **kwargs):
        self.slug = slugify(f"{self.author.full_name} {self.id}")
        return await super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.author.full_name} ------ {self.text[:10]}..."


class Post(FeedAbstract):
    image = fields.ForeignKeyField("models.File", on_delete=fields.SET_NULL, null=True)

    @property
    def get_image(self):
        image = self.image
        if image:
            return FileProcessor.generate_file_url(
                key=image.id,
                folder="posts",
                content_type=image.resource_type,
            )
        return None


class Comment(FeedAbstract):
    post = fields.ForeignKeyField("models.Post")


class Reply(FeedAbstract):
    comment = fields.ForeignKeyField("models.Comment")


class Reaction(BaseModel):
    user = fields.ForeignKeyField("models.User")
    rtype = fields.CharField(max_length=20, choices=ReactionChoices)
    post = fields.ForeignKeyField(
        "models.Post", on_delete=fields.SET_NULL, null=True, blank=True
    )
    comment = fields.ForeignKeyField(
        "models.Comment", on_delete=fields.SET_NULL, null=True, blank=True
    )
    reply = fields.ForeignKeyField(
        "models.Reply", on_delete=fields.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        unique_together = (("user", "post"), ("user", "comment"), ("user", "comment"))

    def __str__(self):
        return f"{self.user.full_name} ------ {self.rtype}"

    @property
    def targeted_obj(self):
        # Return object the reaction object is targeted to (post, comment, or reply)
        return self.post or self.comment or self.reply
