from litestar import Controller, get
from app.api.schemas.general import (
    SiteDetailResponseSchema,
)
from app.db.models.general import SiteDetail


class SiteDetailView(Controller):
    path = "/site-detail"

    @get(
        summary="Retrieve site details",
        description="This endpoint retrieves few details of the site/application",
    )
    async def retrieve_site_details(self) -> SiteDetailResponseSchema:
        sitedetail, created = await SiteDetail.get_or_create()
        return SiteDetailResponseSchema(message="Site Details fetched", data=sitedetail)
