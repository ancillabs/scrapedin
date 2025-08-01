from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Employee(BaseModel):
    """Employee information."""

    name: Optional[str] = None
    position: Optional[str] = None
    profile_url: Optional[HttpUrl] = None


class Company(BaseModel):
    """LinkedIn company profile."""

    linkedin_url: Optional[HttpUrl] = None
    name: Optional[str] = None
    about_us: Optional[str] = None
    specialties: List[str] = Field(default_factory=list)
    website: Optional[HttpUrl] = None
    headquarters: Optional[str] = None
    founded: Optional[int] = Field(None, ge=1800, le=2030)
    company_type: Optional[str] = None
    company_size: Optional[int] = Field(default=None, ge=0)
    company_size_text: Optional[str] = None
    industry: Optional[str] = None
    employees: List[Employee] = Field(default_factory=list)
