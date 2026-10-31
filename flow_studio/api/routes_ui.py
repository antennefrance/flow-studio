"""UI Presentation Router.

Delivers the primary single-page HTML application and static assets.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from flow_studio.config import settings

router = APIRouter(tags=["UI"])


@router.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = settings.static_dir / "index.html"
    return FileResponse(index_file)

