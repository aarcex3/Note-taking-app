
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def app_health():
    return {"Message": "Service running"}