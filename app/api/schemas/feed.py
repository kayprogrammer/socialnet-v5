from uuid import UUID
from pydantic import Field, computed_field, validator

from app.db.models.feed import ReactionChoices
from .base import (
    BaseModel,
    ResponseSchema,
    UserDataSchema,
    PaginatedResponseDataSchema,
)
from app.api.utils.file_processors import FileProcessor
from app.api.utils.validators import validate_image_type
from datetime import datetime
from typing import Any, Optional, Dict, List


class PostSchema(BaseModel):
    author: UserDataSchema
    text: str
    slug: str = Field(..., example="john-doe-d10dde64-a242-4ed0-bd75-4c759644b3a6")
    reactions_count: int = 0
    comments_count: int = 0
    image: Optional[str] = Field(..., example="https://img.url", alias="get_image")
    created_at: datetime
    updated_at: datetime


class PostInputSchema(BaseModel):
    text: str
    file_type: Optional[str] = Field(None, example="image/jpeg")

    @validator("file_type")
    def validate_img_type(cls, v):
        return validate_image_type(v)


class PostsResponseDataSchema(PaginatedResponseDataSchema):
    posts: List[PostSchema] = Field(..., alias="items")


class PostsResponseSchema(ResponseSchema):
    data: PostsResponseDataSchema


class PostInputResponseDataSchema(PostSchema):
    image: Optional[Any] = Field(..., exclude=True, hidden=True)
    image_upload_id: Optional[Any] = Field(..., exclude=True, hidden=True)

    @computed_field
    def file_upload_data(self) -> Dict:
        image_upload_id = self.image_upload_id
        if image_upload_id:
            return FileProcessor.generate_file_signature(
                key=image_upload_id,
                folder="posts",
            )
        return None


class PostInputResponseSchema(ResponseSchema):
    data: PostInputResponseDataSchema


class PostResponseSchema(ResponseSchema):
    data: PostSchema


# REACTIONS
class ReactionSchema(BaseModel):
    id: UUID
    user: UserDataSchema
    rtype: str = "LIKE"


class ReactionInputSchema(BaseModel):
    rtype: ReactionChoices


class ReactionsResponseDataSchema(PaginatedResponseDataSchema):
    reactions: List[ReactionSchema] = Field(..., alias="items")


class ReactionsResponseSchema(ResponseSchema):
    data: ReactionsResponseDataSchema


class ReactionResponseSchema(ResponseSchema):
    data: ReactionSchema


# COMMENTS AND REPLIES


class ReplySchema(BaseModel):
    author: UserDataSchema
    slug: str
    text: str
    reactions_count: int = 0


class CommentSchema(ReplySchema):
    replies_count: int = 0


class CommentWithRepliesResponseDataSchema(PaginatedResponseDataSchema):
    items: List[ReplySchema]


class CommentWithRepliesSchema(BaseModel):
    comment: CommentSchema
    replies: CommentWithRepliesResponseDataSchema


class CommentInputSchema(BaseModel):
    text: str


class CommentsResponseDataSchema(PaginatedResponseDataSchema):
    comments: List[CommentSchema] = Field(..., alias="items")


class CommentsResponseSchema(ResponseSchema):
    data: CommentsResponseDataSchema


class CommentResponseSchema(ResponseSchema):
    data: CommentSchema


class CommentWithRepliesResponseSchema(ResponseSchema):
    data: CommentWithRepliesSchema


class ReplyResponseSchema(ResponseSchema):
    data: ReplySchema
