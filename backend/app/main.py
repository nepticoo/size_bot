from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import PROJECT_ROOT

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.jobs.runner import start_job_runner, stop_job_runner

    task = await start_job_runner()
    yield
    await stop_job_runner(task)


def create_app() -> FastAPI:
    app = FastAPI(title="Size", lifespan=lifespan)

    from app.api import auth, buyer, operator, seller

    app.include_router(auth.router, prefix="/api")
    app.include_router(buyer.router, prefix="/api")
    app.include_router(seller.router, prefix="/api")
    app.include_router(operator.router, prefix="/api")

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    if FRONTEND_DIST.exists():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        async def spa(full_path: str):
            candidate = FRONTEND_DIST / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(FRONTEND_DIST / "index.html")

    return app


app = create_app()
