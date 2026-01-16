from datetime import date
from typing import List, Optional

from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission
from app.models.payroll import PayrollRecord
from app.services.payroll import PayrollService
from clients.employee import EmployeeServiceClient
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from services.report import PayrollReportService
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from hr_shared.auth.jwt_utils import TokenData

router = APIRouter()


@router.get("/records/{payroll_id}/payslip")
async def download_payslip(
    db: SessionDep,
    payroll_id: str,
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Download PDF payslip for a payroll record"""
    # Get payroll record with components
    payroll = await PayrollService.get_payroll_record(db, payroll_id)

    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found"
        )

    # Get employee info from Employee Service
    from app.core.config import settings

    employee_client = EmployeeServiceClient(settings.EMPLOYEE_SERVICE_URL)

    # Extract token from request header
    from fastapi import Request

    request: Request = ...  # This would be injected
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1] if auth_header else ""

    employee = await employee_client.get_employee(payroll.employee_id, token)

    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
    employee_code = employee.get("employee_code", "N/A")

    # Generate PDF
    pdf_buffer = await PayrollReportService.generate_payslip_pdf(
        payroll, employee_name, employee_code
    )

    # Return as downloadable file
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=payslip_{employee_code}_{payroll.pay_period_start}.pdf"
        },
    )


@router.get("/reports/summary")
async def download_payroll_summary(
    db: SessionDep,
    start_date: date,
    end_date: date,
    current_user: TokenData = Depends(check_permission("payroll:read")),
):
    """Download PDF summary report for payroll period"""
    # Get all payroll records for period
    stmt = (
        select(PayrollRecord)
        .where(
            and_(
                PayrollRecord.pay_period_start >= start_date,
                PayrollRecord.pay_period_end <= end_date,
            )
        )
        .options(selectinload(PayrollRecord.salary_components))
    )

    result = await db.execute(stmt)
    payrolls = result.scalars().all()

    if not payrolls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payroll records found for this period",
        )

    # Generate PDF
    pdf_buffer = await PayrollReportService.generate_payroll_summary_pdf(
        payrolls, start_date, end_date
    )

    # Return as downloadable file
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=payroll_summary_{start_date}_to_{end_date}.pdf"
        },
    )
