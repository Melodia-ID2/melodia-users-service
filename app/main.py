from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.controllers.users_controller import UsersController
from app.core.database import init_db
from app.repositories.users_repository import UsersRepository
from app.routers.users_router import UsersRouter
from app.services.users_service import UsersService


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Users Service", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "users"}
    
    users_repository = UsersRepository()
    users_service = UsersService(repository=users_repository)
    users_controller = UsersController(service=users_service)
    users_router = UsersRouter(controller=users_controller)

    app.include_router(users_router.get_router())
    return app


app = create_app()
