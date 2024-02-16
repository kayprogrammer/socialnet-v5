from tortoise import Model, fields

class BaseModel(Model):
    id = fields.UUIDField(auto_generate=True, unique=True, primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

class File(BaseModel):
    resource_type = fields.CharField(max_length=20)
