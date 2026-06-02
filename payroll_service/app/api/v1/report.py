from datetime import date

from app.clients.employee import EmployeeServiceClient
from app.core.config import settings
from app.core.db import SessionDep
from app.core.dependencies.auth import check_permission, oauth2_scheme
from app.models.payroll import PayrollRecord
from app.services.payroll import PayrollService
from app.services.report import PayrollReportService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/records/{payroll_id}/payslip")
async def download_payslip(
    payroll_id: str,
    request: Request,
    db: SessionDep,
    token: str = Depends(oauth2_scheme),
    current_user=Depends(check_permission("payroll:read")),
):
    """Download PDF payslip for a payroll record"""
    payroll = await PayrollService.get_payroll_record(db, payroll_id)
    if not payroll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found"
        )

    employee_client = EmployeeServiceClient(settings.EMPLOYEE_SERVICE_URL)
    employee = await employee_client.get_employee(payroll.employee_id, token)

    employee_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
    employee_code = employee.get("employee_code", "N/A")

    pdf_buffer = await PayrollReportService.generate_payslip_pdf(
        payroll, employee_name, employee_code
    )

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
    current_user=Depends(check_permission("payroll:read")),
):
    """Download PDF summary report for payroll period"""
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

    pdf_buffer = await PayrollReportService.generate_payroll_summary_pdf(
        list(payrolls), start_date, end_date
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=payroll_summary_{start_date}_to_{end_date}.pdf"
        },
    )
