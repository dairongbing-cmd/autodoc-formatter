import sys
from pathlib import Path

# Allow running as python3 app/main.py directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from contextlib import asynccontextmanager

import aiofiles
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    CLEANUP_INTERVAL_SECONDS,
    OUTPUT_DIR,
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOAD_DIR,
)
from app.services.storage import StorageService

storage = StorageService()


async def cleanup_loop():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            storage.cleanup_stale()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(cleanup_loop())
    yield
    task.cancel()


app = FastAPI(title="AutoDocFormatter", version="0.1.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    index_path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        async with aiofiles.open(index_path, encoding="utf-8") as f:
            content = await f.read()
        return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>AutoDocFormatter</h1>", status_code=200)


from app.routes import documents, presets, upload
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(presets.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
