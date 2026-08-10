from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a lightweight service readiness signal."""
    return {"status": "ok"}
