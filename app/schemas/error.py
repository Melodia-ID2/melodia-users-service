from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Schema for error responses following the RFC 7807 specification."""

    type: Optional[str] = "about:blank"
    title: Optional[str] = None
    status: Optional[int] = None
    detail: Optional[str] = None
    instance: Optional[str] = None
