from typing import Any, Dict, List, Optional
from pydantic import Field, validator
from app.api.schemas.base import (
    BaseModel,
    PaginatedResponseDataSchema,
    ResponseSchema,
    UserDataSchema,
)
from uuid import UUID
from datetime import datetime
from app.api.utils.file_processors import FileProcessor
from .schema_examples import file_upload_data

from app.api.utils.validators import validate_file_type, validate_image_type


class ChatSchema(BaseModel):
    id: UUID
    name: Optional[str]
    owner: UserDataSchema
    ctype: str
    description: Optional[str]
    image: Optional[str] = Field(..., alias="get_image")
    latest_message: Optional[Dict]
    created_at: datetime
    updated_at: datetime

    @validator("latest_message", pre=True)
    def resolve_latest_message(cls, v):
        if len(v) > 0:
            message = v[0]
            return {
                "sender": UserDataSchema.model_validate(message.sender).model_dump(),
                "text": message.text,
                "file": message.get_file,
            }
        return None


class MessageSchema(BaseModel):
    id: UUID
    chat_id: UUID
    sender: UserDataSchema
    text: Optional[str]
    file: Optional[str] = Field(..., alias="get_file")
    created_at: datetime
    updated_at: datetime


class MessageUpdateSchema(BaseModel):
    file_type: Optional[str] = Field(None, example="image/jpeg")
    text: Optional[str] = Field(None, example="Hello")

    @validator("text", always=True)
    def validate_text(cls, v, values):
        if not v and not values.get("file_type"):
            raise ValueError("You must enter a text")
        return v

    @validator("file_type", pre=True)
    def validate_file_type(cls, v):
        return validate_file_type(v)


class MessageCreateSchema(MessageUpdateSchema):
    chat_id: UUID = Field(None)
    username: str = Field(None, example="john-doe")

    @validator("username", pre=True)
    def validate_username(cls, v, values):
        chat_id = values.get("chat_id")
        if not chat_id and not v:
            raise ValueError("You must enter the recipient's username")
        elif chat_id and v:
            raise ValueError("Can't enter username when chat_id is set")
        return v


class MessagesResponseDataSchema(PaginatedResponseDataSchema):
    items: List[MessageSchema]


class MessagesSchema(BaseModel):
    chat: ChatSchema
    messages: MessagesResponseDataSchema
    users: List[UserDataSchema] = Field(..., alias="recipients")


class GroupChatSchema(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    image: Optional[str] = Field(..., alias="get_image")
    users: List[UserDataSchema] = Field(..., alias="recipients")


username_field = Field(None, min_items=1, max_items=99, example=["john-doe"])


class GroupChatInputSchema(BaseModel):
    name: str = Field(..., max_length=100)
    description: str = Field(None, max_length=1000)
    usernames_to_add: Optional[List[str]] = username_field
    usernames_to_remove: Optional[List[str]] = username_field
    file_type: Optional[str] = Field(None, example="image/jpeg")

    @validator("file_type", always=True)
    def validate_img_type(cls, v):
        return validate_image_type(v)

    @validator("usernames_to_remove", always=True)
    def validate_usernames_to_remove(cls, v, values):
        usernames_to_add = values.get("usernames_to_add")
        if v and usernames_to_add:
            # Convert lists to sets and check for intersection
            intersection = set(v) & set(usernames_to_add)
            if intersection:
                raise ValueError(
                    "Must not have any matching items with usernames to add"
                )
        return v


class GroupChatCreateSchema(GroupChatInputSchema):
    usernames_to_add: List[str] = Field(
        ..., min_items=1, max_items=99, example=["john-doe"]
    )
    usernames_to_remove: Optional[List[str]] = Field(None, exclude=True, hidden=True)


# RESPONSES
class ChatsResponseDataSchema(PaginatedResponseDataSchema):
    chats: List[ChatSchema] = Field(..., alias="items")


class ChatsResponseSchema(ResponseSchema):
    data: ChatsResponseDataSchema


class MessageCreateResponseDataSchema(MessageSchema):
    file: Any = Field(None, exclude=True, hidden=True)
    file_upload_id: Optional[Any] = Field(..., exclude=True, hidden=True)
    file_upload_data: Optional[Dict] = Field(None, example=file_upload_data)

    @validator("file_upload_data", always=True)
    def assemble_file_upload_data(cls, v, values):
        file_upload_id = values.get("file_upload_id")
        if file_upload_id:
            return FileProcessor.generate_file_signature(
                key=file_upload_id,
                folder="messages",
            )
        return None


class MessageCreateResponseSchema(ResponseSchema):
    data: MessageCreateResponseDataSchema


class ChatResponseSchema(ResponseSchema):
    data: MessagesSchema


class GroupChatInputResponseDataSchema(GroupChatSchema):
    image: Any = Field(None, exclude=True, hidden=True)
    image_upload_id: Optional[Any] = Field(..., exclude=True, hidden=True)
    file_upload_data: Optional[Dict] = Field(None, example=file_upload_data)

    @validator("file_upload_data", always=True)
    def assemble_file_upload_data(cls, v, values):
        image_upload_id = values.get("image_upload_id")
        if image_upload_id:
            return FileProcessor.generate_file_signature(
                key=image_upload_id,
                folder="groups",
            )
        return None


class GroupChatInputResponseSchema(ResponseSchema):
    data: GroupChatInputResponseDataSchema
