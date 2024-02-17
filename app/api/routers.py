from litestar import Router
from litestar.di import Provide

from app.api.routes.general import general_handlers
general_router = Router(
    path="/api/v5/general",
    route_handlers=general_handlers,
    tags=["General"],
)

all_routers = [
    general_router,
]