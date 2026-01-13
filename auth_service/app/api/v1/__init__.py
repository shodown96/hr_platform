from fastapi import APIRouter
from app.api.v1 import users, auth, health

router = APIRouter(prefix="/v1")
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(users.router, prefix="/users", tags=["Users"])
