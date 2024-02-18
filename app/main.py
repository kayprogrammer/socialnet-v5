from litestar import (
    Litestar,
)
from litestar.openapi import OpenAPIConfig, OpenAPIController
from litestar.config.cors import CORSConfig 
from litestar.middleware.rate_limit import RateLimitConfig
from pydantic_openapi_schema.v3_1_0 import Components, SecurityScheme

from app.core.config import settings
from app.common.exception_handlers import exc_handlers
from app.api.routers import all_routers
from app.db.config import init_tortoise, shutdown_tortoise


class MyOpenAPIController(OpenAPIController):
    path = "/"


openapi_config = OpenAPIConfig(
    title=settings.PROJECT_NAME,
    version="5.0.0",
    description="""
        A simple Social Networking API built with FastAPI & Piccolo ORM

        WEBSOCKETS:
            Notifications: 
                URL: wss://{host}/api/v5/ws/notifications
                * Requires authorization, so pass in the Bearer Authorization header.
                * You can only read and not send notification messages into this socket.
            Chats:
                URL: wss://{host}/api/v5/ws/chats/{id}
                * Requires authorization, so pass in the Bearer Authorization header.
                * Use chat_id as the ID for existing chat or username if its the first message in a DM.
                * You cannot read realtime messages from a username that doesn't belong to the authorized user, but you can surely send messages
                * Only send message to the socket endpoint after the message has been created or updated, and files has been uploaded.
                * Fields when sending message through the socket: e.g {"status": "CREATED", "id": "fe4e0235-80fc-4c94-b15e-3da63226f8ab"}
                    * status - This must be either CREATED or UPDATED (string type)
                    * id - This is the ID of the message (uuid type)
    """,
    security=[{"BearerToken": []}],
    components=Components(
        securitySchemes={
            "BearerToken": SecurityScheme(
                type="http",
                scheme="bearer",
            ),
        },
    ),
    openapi_controller=MyOpenAPIController,
    root_schema_site="swagger",
)

rate_limit_config = RateLimitConfig(rate_limit=("minute", 1000))
cors_config = CORSConfig(
    allow_origins=settings.CORS_ALLOWED_ORIGINS, allow_credentials=True
)

app = Litestar(
    route_handlers=all_routers,
    openapi_config=openapi_config,
    middleware=[rate_limit_config.middleware],
    exception_handlers=exc_handlers,
    cors_config=cors_config,
    on_startup=[init_tortoise],
    on_shutdown=[shutdown_tortoise]
)