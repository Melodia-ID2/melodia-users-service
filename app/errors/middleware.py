from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.errors.exceptions import (
    ValidationError,
    NotFoundError,
    DatabaseError,
    AuthenticationError,
    FileUploadError
)
from app.errors.error_responses import create_error_response


class Middleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response | JSONResponse:

        try:
            response = await call_next(request)
            return response

        except ValidationError as exc:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    400, "Bad request error", str(exc), str(request.url.path)
                ),
            )

        except NotFoundError as exc:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    404, "Resource Not Found", str(exc), str(request.url.path)
                ),
            )

        except AuthenticationError as exc:
            return JSONResponse(
                status_code=401,
                content=create_error_response(
                    401, "Authentication Error", str(exc), str(request.url.path)
                ),
            )

        except FileUploadError as exc:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    500, "File Upload Error", str(exc), str(request.url.path)
                ),
            )
            
        except DatabaseError as exc:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    500, "Internal Server Error", str(exc), str(request.url.path)
                ),
            )

        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    500, "Internal Server Error", str(exc), str(request.url.path)
                ),
            )