from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.admin_router import router as admin_router
from app.api.v1.routers.artist_router import router as artist_router
from app.api.v1.routers.system_router import router as system_router
from app.api.v1.routers.users_router import router as users_router
from app.core.database import init_db
from app.errors.middleware import Middleware
from sqlalchemy.exc import ProgrammingError

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
    except ProgrammingError as e:
        if "DuplicatePreparedStatement" not in str(e):
            raise
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Users Service", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(Middleware)
    app.include_router(system_router)
    app.include_router(users_router)
    app.include_router(artist_router)
    app.include_router(admin_router)

    return app


app = create_app()
