from contextlib import asynccontextmanager

from fastapi import FastAPI

from basicvids_favorites.db import create_db_and_tables
from basicvids_favorites.routers.favorites import router as favorites_router
from basicvids_favorites.routers.root import router as root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="BasicVids Favorites", lifespan=lifespan)

app.include_router(favorites_router, prefix="/api/v1")
app.include_router(root_router)
