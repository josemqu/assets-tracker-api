from pydantic import BaseModel
from typing import Optional, Dict


class SelectorConfig(BaseModel):
    ars: Optional[str] = None
    usd: Optional[str] = None


class ConfigSiteCreate(BaseModel):
    name: str
    urlPattern: str
    selectors: SelectorConfig
    investment: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Banco Nación",
                "urlPattern": "https://hb.redlink.com.ar/*",
                "selectors": {"ars": ".saldo-total"},
                "investment": "Plazo Fijo"
            }
        }


class ConfigSiteUpdate(BaseModel):
    name: Optional[str] = None
    urlPattern: Optional[str] = None
    selectors: Optional[SelectorConfig] = None
    investment: Optional[str] = None
