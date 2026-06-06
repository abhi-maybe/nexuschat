"""FastAPI application factory."""

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from server.database.manager import DatabaseManager
from server.routes.chat import router as chat_router
from server.routes.models import router as models_router
from server.routes.auth import router as auth_router
from server.routes.settings import router as settings_router
from server.routes.health import router as health_router
from server.providers.registry import ProviderRegistry
from server.middleware.cors import setup_cors

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

db_manager = DatabaseManager()
provider_registry = ProviderRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    await db_manager.initialize()
    provider_registry.discover_providers()
    yield
    await db_manager.close()


def create_app() -> FastAPI:
    """Application factory."""
    setup_cors(app)

    app = FastAPI(
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        title="NexusChat",
        description="ChatGPT-like interface for local and cloud AI models",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Mount static files
    # Serve CSS, JS, and images
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Templates
    # Jinja2 template engine
    app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Store references
    app.state.db = db_manager
    app.state.providers = provider_registry

    # Include routers
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
    app.include_router(models_router, prefix="/api/models", tags=["models"])
    app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
    app.include_router(health_router, prefix="/api", tags=["health"])

    # Root route serves the SPA
    from fastapi.responses import FileResponse

    @app.get("/")
    async def index():
        return FileResponse(str(TEMPLATES_DIR / "index.html"))

    @app.get("/login")
    async def login_page():
        return FileResponse(str(TEMPLATES_DIR / "login.html"))


    @app.get("/ping")
    @app.get("/version")
    async def version():
        return {"version": "1.0.0", "name": "NexusChat"}

    @app.get("/ping")
    async def ping():
        return {"pong": True}

    return app
