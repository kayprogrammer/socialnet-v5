from litestar import Router
from litestar.di import Provide

from app.api.routes.general import SiteDetailView
general_router = Router(
    path="/api/v5/general",
    route_handlers=[SiteDetailView],
    tags=["General"],
)

all_routers = [
    general_router,
]