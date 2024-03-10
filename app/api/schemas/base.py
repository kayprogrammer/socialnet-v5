from typing import Optional
from pydantic import BaseModel as OriginalBaseModel, Field
from .schema_examples import user_data


class BaseModel(OriginalBaseModel):
    class Config:
        arbitrary_types_allowed = True
        from_attributes = True

    @staticmethod
    def model_json_schema(schema: dict, _):
        props = {}
        for k, v in schema.get("properties", {}).items():
            if not v.get("hidden", False):
                props[k] = v
        schema["properties"] = props


class ResponseSchema(BaseModel):
    status: str = "success"
    message: str


class PaginatedResponseDataSchema(BaseModel):
    per_page: int
    current_page: int
    last_page: int


class UserDataSchema(BaseModel):
    name: str = Field(..., alias="full_name")
    username: str
    avatar: Optional[str] = Field(..., alias="get_avatar")

    class Config:
        json_schema_extra = {"example": user_data}
