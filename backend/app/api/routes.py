from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List
import os
import uuid
from datetime import datetime

from app.core.config import settings
from app.models.schemas import UploadResponse, CalculationResult, SessionInfo
from app.services.file_service import FileService
from app.services.calculation_service import CalculationService

router = APIRouter()

# Initialize services
file_service = FileService()
calculation_service = CalculationService()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload portfolio Excel file and start SALT calculation
    """
    try:
        # Validate file
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are supported")
        
        if file.size and file.size > settings.max_upload_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        file_path = await file_service.save_upload(file, session_id)
        
        # Start calculation (synchronous for prototype)
        result = await calculation_service.calculate_salt(file_path, session_id)
        
        return UploadResponse(
            session_id=session_id,
            filename=file.filename,
            status="completed" if result else "failed",
            message="SALT calculation completed successfully" if result else "Calculation failed"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{session_id}", response_model=CalculationResult)
async def get_results(session_id: str):
    """
    Get calculation results for a session
    """
    try:
        result = await calculation_service.get_results(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{session_id}/download")
async def download_results(session_id: str):
    """
    Download calculation results as Excel file
    """
    try:
        file_path = await calculation_service.get_results_file(session_id)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Results file not found")
        
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"salt_results_{session_id}.xlsx"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template")
async def download_template():
    """
    Download standard portfolio template
    """
    try:
        template_path = os.path.join(settings.templates_dir, "portfolio_template.xlsx")
        if not os.path.exists(template_path):
            # Create basic template if it doesn't exist
            await file_service.create_template(template_path)
        
        return FileResponse(
            template_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="portfolio_template.xlsx"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """
    List all calculation sessions (for development)
    """
    try:
        sessions = await calculation_service.list_sessions()
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))