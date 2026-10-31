"""FLOW Studio Application Factory.

Assembles FastAPI application, registers domain routers,
configures CORS middleware, and mounts static asset directories.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from flow_studio.api.routes_chat import router as chat_router
from flow_studio.api.routes_openai import router as openai_router
from flow_studio.api.routes_telemetry import router as telemetry_router
from flow_studio.api.routes_ui import router as ui_router
from flow_studio.config import settings


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs",
        redoc_url=None,
    )

    # 1. CORS Configuration (Allows integration from Obsidian, Continue, Cursor)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Mount Static Asset Directory
    app.mount(
        "/static",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )

    # 3. Register Presentation Routers
    app.include_router(ui_router)
    app.include_router(telemetry_router)
    app.include_router(chat_router)
    app.include_router(openai_router)

    return app

