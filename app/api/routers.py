from litestar import Router
from litestar.di import Provide
from app.api.deps import (
    get_current_socket_user,
    get_current_user,
    get_current_user_or_guest,
)

from app.api.routes.general import SiteDetailView
from app.api.routes.auth import auth_handlers
from app.api.routes.profiles import profiles_handlers
from app.api.routes.chat import chat_handlers
from app.api.routes.feed import feed_handlers
from app.api.sockets.notification import NotificationSocketHandler

general_router = Router(
    path="/general",
    route_handlers=[SiteDetailView],
    tags=["General"],
)

auth_router = Router(
    path="/auth",
    route_handlers=auth_handlers,
    tags=["Auth"],
    dependencies={"user": Provide(get_current_user)},
)

profiles_router = Router(
    path="/profiles",
    route_handlers=profiles_handlers,
    tags=["Profiles"],
    dependencies={
        "user": Provide(get_current_user),
        "client": Provide(get_current_user_or_guest),
    },
)

chat_router = Router(
    path="/chats",
    route_handlers=chat_handlers,
    tags=["Chats"],
    dependencies={
        "user": Provide(get_current_user),
    },
)

feed_router = Router(
    path="/feed",
    route_handlers=feed_handlers,
    tags=["Feed"],
    dependencies={
        "user": Provide(get_current_user),
    },
)

socket_router = Router(
    path="/ws",
    route_handlers=[NotificationSocketHandler],
    tags=["Websocket"],
)

base_router = Router(
    path="/api/v5",
    route_handlers=[
        general_router,
        auth_router,
        profiles_router,
        chat_router,
        feed_router,
        socket_router,
    ],
)
