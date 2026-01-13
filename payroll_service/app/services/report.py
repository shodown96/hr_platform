from io import BytesIO
from typing import List
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from models.payroll import PayrollRecord, SalaryComponent


class PayrollReportService:
    
    @staticmethod
    async def generate_payslip_pdf(
        payroll_record: PayrollRecord,
        employee_name: str,
        employee_code: str,
        company_name: str = "Your Company Name"
    ) -> BytesIO:
        """
        Generate a PDF payslip for an employee
        Returns BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12
        )
        
        # Title
        title = Paragraph(f"{company_name}<br/>PAY SLIP", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Employee Info Table
        employee_data = [
            ['Employee Name:', employee_name, 'Employee Code:', employee_code],
            ['Pay Period:', f"{payroll_record.pay_period_start} to {payroll_record.pay_period_end}", 
             'Payment Date:', str(payroll_record.payment_date or 'Pending')],
            ['Payment Method:', payroll_record.payment_method or 'N/A', 
             'Reference:', payroll_record.payment_reference or 'N/A']
        ]
        
        employee_table = Table(employee_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(employee_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Earnings & Deductions Heading
        earnings_heading = Paragraph("Earnings & Deductions", heading_style)
        elements.append(earnings_heading)
        
        # Components Table
        component_data = [['Description', 'Type', 'Amount']]
        
        total_earnings = 0
        total_deductions = 0
        
        for component in payroll_record.salary_components:
            amount = float(component.amount)
            component_data.append([
                component.description or component.component_type.value.replace('_', ' ').title(),
                component.component_type.value.replace('_', ' ').title(),
                f"${amount:,.2f}"
            ])
            
            if component.component_type.value in ['deduction', 'tax']:
                total_deductions += amount
            else:
                total_earnings += amount
        
        # Add totals
        component_data.append(['', '', ''])  # Spacer
        component_data.append(['Total Earnings', '', f"${total_earnings:,.2f}"])
        component_data.append(['Total Deductions', '', f"${total_deductions:,.2f}"])
        
        component_table = Table(component_data, colWidths=[3*inch, 2*inch, 2*inch])
        component_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -4), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Total rows
            ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#E8F8F5')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FADBD8')),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -2), (-1, -1), 11),
            
            # Grid
            ('GRID', (0, 0), (-1, -4), 0.5, colors.grey),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.grey),
        ]))
        
        elements.append(component_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Net Pay (Big and Bold)
        net_pay_data = [[
            'NET PAY',
            f"${float(payroll_record.net_salary):,.2f}"
        ]]
        
        net_pay_table = Table(net_pay_data, colWidths=[5*inch, 2*inch])
        net_pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(net_pay_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        footer_text = f"""
        <i>This is a computer-generated document. No signature is required.</i><br/>
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        footer = Paragraph(footer_text, footer_style)
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    async def generate_payroll_summary_pdf(
        payroll_records: List[PayrollRecord],
        period_start: date,
        period_end: date,
        company_name: str = "Your Company Name"
    ) -> BytesIO:
        """
        Generate a summary PDF for multiple payroll records (for HR/Finance)
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Title
        title = Paragraph(
            f"{company_name}<br/>PAYROLL SUMMARY REPORT<br/>"
            f"<font size=12>{period_start} to {period_end}</font>",
            title_style
        )
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Summary Statistics
        total_employees = len(payroll_records)
        total_gross = sum(float(p.gross_salary) for p in payroll_records)
        total_deductions = sum(float(p.total_deductions) for p in payroll_records)
        total_net = sum(float(p.net_salary) for p in payroll_records)
        
        summary_data = [
            ['Total Employees', str(total_employees)],
            ['Total Gross Salary', f"${total_gross:,.2f}"],
            ['Total Deductions', f"${total_deductions:,.2f}"],
            ['Total Net Salary', f"${total_net:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Individual Records
        record_data = [['Employee ID', 'Period', 'Gross', 'Deductions', 'Net', 'Status']]
        
        for record in payroll_records:
            record_data.append([
                record.employee_id[:8] + '...',
                f"{record.pay_period_start}",
                f"${float(record.gross_salary):,.2f}",
                f"${float(record.total_deductions):,.2f}",
                f"${float(record.net_salary):,.2f}",
                record.payment_status.value.upper()
            ])
        
        record_table = Table(record_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch])
        record_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        
        elements.append(record_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
