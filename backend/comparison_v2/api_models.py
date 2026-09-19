from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class CompareV2Request(BaseModel):
    title: str = Field(min_length=1)
    price: Optional[float] = Field(default=None, ge=0)
    query: Optional[str] = None
    retailers: Optional[list[str]] = None
    limit_per_retailer: int = Field(default=20, ge=1, le=50)

class RetailerStatusResponse(BaseModel):
    retailer: str
    available: bool
    returned: int
    error: Optional[str] = None
    status: str = "AVAILABLE"

class CompareV2ResultResponse(BaseModel):
    retailer: str
    title: str
    url: str
    price: Optional[float] = None
    price_text: Optional[str] = None
    classification: str
    score: int
    reasons: list[str]
    savings: Optional[float] = None

class CompareV2Response(BaseModel):
    tracked_title: str
    tracked_price: Optional[float]
    query: str
    retailers: list[RetailerStatusResponse]
    results: list[CompareV2ResultResponse]
    rejected_count: int
