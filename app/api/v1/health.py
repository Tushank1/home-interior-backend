from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok"}