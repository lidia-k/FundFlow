from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CalculationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    session_id: str
    filename: str
    status: CalculationStatus
    message: str
    created_at: datetime = datetime.now()


class PortfolioCompany(BaseModel):
    name: str
    state: str
    revenue: float
    tax_allocation: Dict[str, float]  # state -> amount


class LPAllocation(BaseModel):
    lp_name: str
    ownership_percentage: float
    salt_allocation: Dict[str, float]  # state -> amount
    total_allocation: float


class CalculationResult(BaseModel):
    session_id: str
    filename: str
    status: CalculationStatus
    portfolio_companies: List[PortfolioCompany]
    lp_allocations: List[LPAllocation]
    total_salt_amount: float
    calculation_summary: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None


class SessionInfo(BaseModel):
    session_id: str
    filename: str
    status: CalculationStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# Database Models (SQLAlchemy schemas)
class UserCreate(BaseModel):
    email: str
    company_name: str


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    company_name: str
    created_at: datetime


class SALTRule(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    state: str
    tax_rate: float
    apportionment_formula: str
    effective_date: datetime