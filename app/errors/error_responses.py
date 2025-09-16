from app.schemas.error import ErrorResponse


def error_responses(*codes: int):
    """
    Generates a reusable dictionary of error responses for endpoints, based on the provided status codes.
    """
    descriptions = {
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }
    return {
        code: {"model": ErrorResponse, "description": descriptions.get(code, "Error")}
        for code in codes
    }


def create_error_response(status_code: int, title: str, detail: str, instance: str):
    return ErrorResponse(
        title=title, status=status_code, detail=detail, instance=instance
    ).model_dump()