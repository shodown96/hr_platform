from fastapi import APIRouter
from app.api.v1 import employee, position, department, health

router = APIRouter(prefix="/v1")
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(employee.router, prefix="/employees", tags=["Employees"])
router.include_router(position.router, prefix="/positions", tags=["Positions"])
router.include_router(department.router, prefix="/departments", tags=["Departments"])
