from pydantic import BaseModel
from typing import Optional, List


class InvestmentCreate(BaseModel):
    timestamp: int
    entidad: str
    monto_ars: Optional[float] = None
    monto_usd: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1704067200000,
                "entidad": "Banco Nación",
                "monto_ars": 150000.50,
                "monto_usd": None
            }
        }


class InvestmentUpdate(BaseModel):
    monto_ars: Optional[float] = None
    monto_usd: Optional[float] = None


class BulkInvestmentRequest(BaseModel):
    records: List[InvestmentCreate]
