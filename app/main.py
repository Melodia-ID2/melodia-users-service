from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.routers.users_router import router as users_router
from app.routers.system_router import router as system_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Users Service", lifespan=lifespan)
    app.include_router(system_router)
    app.include_router(users_router)

    return app


app = create_app()
