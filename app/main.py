import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import router as sites_router
from app.services import start_monitoring
from app.auth_router import router as auth_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    task = asyncio.create_task(start_monitoring())
    yield

    task.cancel()

app = FastAPI(lifespan=lifespan)
app.include_router(sites_router)
app.include_router(auth_router)

@app.get("/")
async def home():
    return {"status": "api is alive", "message": "Hello World"}