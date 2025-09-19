"""Template API endpoint for downloading Excel template."""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/template")
async def download_template() -> FileResponse:
    """
    Download Excel template file for investor data upload.

    Returns Excel template with proper headers and formatting.
    """
    # Look for template file in data directory
    template_path = Path("data/template/investor_data_template.xlsx")

    # Check if template exists
    if not template_path.exists():
        # If template doesn't exist, create a basic one
        import pandas as pd
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        # Create template directory if it doesn't exist
        template_path.parent.mkdir(parents=True, exist_ok=True)

        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Investor Data"

        # Define headers
        headers = [
            "Investor Name",
            "Investor Entity Type",
            "Investor Tax State",
            "Fund Code",
            "Period Quarter",
            "Period Year",
            "Jurisdiction",
            "Amount",
            "Composite Exemption",
            "Withholding Exemption"
        ]

        # Style for headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Add headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # Add example data row
        example_data = [
            "ABC Investment LLC",
            "LLC",
            "NY",
            "FUND001",
            "Q4",
            "2023",
            "STATE",
            "100000.00",
            "No",
            "Exemption"
        ]

        for col, value in enumerate(example_data, 1):
            ws.cell(row=2, column=col, value=value)

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 25)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Add instructions sheet
        instructions_ws = wb.create_sheet("Instructions")
        instructions = [
            "FundFlow Investor Data Template Instructions",
            "",
            "Column Descriptions:",
            "• Investor Name: Full legal name of the investor entity",
            "• Investor Entity Type: LLC, Corporation, Partnership, Individual, Trust",
            "• Investor Tax State: Two-letter state code (e.g., NY, CA, TX)",
            "• Fund Code: Internal fund identifier",
            "• Period Quarter: Q1, Q2, Q3, or Q4",
            "• Period Year: Four-digit year (e.g., 2023)",
            "• Jurisdiction: STATE, FOREIGN, or MUNICIPAL",
            "• Amount: Distribution amount in decimal format",
            "• Composite Exemption: 'Exemption' for exempt, any other value for non-exempt",
            "• Withholding Exemption: 'Exemption' for exempt, any other value for non-exempt",
            "",
            "File Requirements:",
            "• Maximum file size: 10MB",
            "• Supported formats: .xlsx, .xls",
            "• Data should start from row 2 (headers in row 1)",
            "",
            "Validation Rules:",
            "• All fields are required",
            "• Amount must be a valid number",
            "• State codes must be valid US states",
            "• Entity types must match allowed values",
            "• Period format must be exact (Q1-Q4 for quarter, YYYY for year)",
            "",
            "For support, contact: support@fundflow.com"
        ]

        for row, instruction in enumerate(instructions, 1):
            instructions_ws.cell(row=row, column=1, value=instruction)

        # Style instructions header
        instructions_ws.cell(row=1, column=1).font = Font(bold=True, size=14)

        # Auto-adjust instructions column width
        instructions_ws.column_dimensions['A'].width = 80

        # Save template
        wb.save(str(template_path))

    # Verify template file exists
    if not template_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Template file could not be created or found"
        )

    # Return file
    return FileResponse(
        path=str(template_path),
        filename="fundflow_investor_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=fundflow_investor_template.xlsx"}
    )