from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "users"}
