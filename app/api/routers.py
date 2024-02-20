from litestar import Router
from litestar.di import Provide
from app.api.deps import get_current_user

from app.api.routes.general import SiteDetailView
from app.api.routes.auth import auth_handlers

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

base_router = Router(path="/api/v5", route_handlers=[general_router, auth_router])
