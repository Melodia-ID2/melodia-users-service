from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers.system_router import router as system_router
from app.api.v1.routers.users_router import router as users_router
from app.core.database import init_db
from app.errors.middleware import Middleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
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

    return app


app = create_app()
