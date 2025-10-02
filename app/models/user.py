from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    userId: str
    email: str
    name: Optional[str] = None
    token: str


class PreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    autoReplication: Optional[Dict[str, Any]] = None
    manualRecordReferences: Optional[Dict[str, Any]] = None
