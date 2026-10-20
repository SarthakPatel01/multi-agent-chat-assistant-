
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


class ReportResponse(BaseModel):
    id: int
    topic: str
    report: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
