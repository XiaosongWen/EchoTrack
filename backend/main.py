import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from core.logger import setup_logging
from core.setup import AppSetup
from routers.pursuits import router as pursuits_router
from routers.health import router as health_router
from routers.user import router as user_router
from routers.test import router as test_router
from routers.labels import router as labels_router
from routers.weather import router as weather_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()
    yield


app = FastAPI(title="MyWorld API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AppSetup.init_app(app)

app.include_router(health_router)
app.include_router(pursuits_router)
app.include_router(user_router)
app.include_router(test_router)
app.include_router(labels_router)
app.include_router(weather_router)

# Serve static frontend files if directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return None
        # Prevent path traversal: normalize and verify path stays within static_dir
        safe_path = os.path.normpath(os.path.join(static_dir, full_path))
        if not safe_path.startswith(os.path.normpath(static_dir) + os.sep) and safe_path != os.path.normpath(static_dir):
            return FileResponse(os.path.join(static_dir, "index.html"))
        if os.path.exists(safe_path) and os.path.isfile(safe_path):
            return FileResponse(safe_path)
        return FileResponse(os.path.join(static_dir, "index.html"))


