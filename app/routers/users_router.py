from fastapi import APIRouter

from app.controllers.users_controller import UsersController


class UsersRouter:
    def __init__(self, controller: UsersController):
        self.controller = controller
        self.router = APIRouter(prefix="/users", tags=["users"])
        self._setup_routes()

    def get_router(self) -> APIRouter:
        return self.router

    def _setup_routes(self):
        self.router.get("/")(self.controller.get_all_users)
