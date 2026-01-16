from fastapi import APIRouter
from app.api.v1 import payroll, health
from payroll_service.app.api.v1 import payroll

router = APIRouter(prefix="/v1")
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])
router.include_router(payroll.router, prefix="/reports", tags=["Reports"])
