"""
Pydantic/Motor document models for PNG Transparency Monitor.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


# ── Helpers ───────────────────────────────────────────────────────────────────

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


# ── Reserved Activities List ──────────────────────────────────────────────────

RAL_SECTORS: set[str] = {
    "retail trade",
    "wholesale trade",
    "small-scale agriculture",
    "passenger transport",
    "real estate agency",
    "cleaning services",
    "security services",
    "trade store",
    "market vendor",
    "bakery",
    "passenger boat transport",
    "fresh produce market",
    "scrap metal",
}

# ── Core document model ───────────────────────────────────────────────────────

class BusinessRecord(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    record_id: str                          # SHA-256 dedup key
    source: str                             # IPA | Gazette | NPC | News
    company_name: str
    registration_number: Optional[str] = None
    directors: list[str] = []
    registered_office: Optional[str] = None
    sector: Optional[str] = None
    province: Optional[str] = None
    is_foreign: Optional[bool] = None
    foreign_certificate_number: Optional[str] = None
    gazette_notice_type: Optional[str] = None
    trend_category: Optional[str] = None   # Local Growth / Foreign Takeover / Skills Gap
    ral_violation: bool = False
    raw_text: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class FrontingCluster(BaseModel):
    trigger: str                            # shared_director | shared_address
    shared_value: str
    companies: list[str]
    company_ids: list[str]
    sectors: list[str]
    risk_score: int
    sa_confidence: int
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class RegAlert(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    company: str
    cert_number: str
    sector: str
    province: Optional[str] = None
    priority: str                           # critical | high | medium | low
    dismissed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ── API response shapes ───────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    foreign_entities: int
    ral_violations: int
    fronting_clusters: int
    local_businesses: int
    foreign_delta_pct: float
    ral_delta_pct: float
    fronting_delta_pct: float
    local_delta_pct: float


class ProvincePoint(BaseModel):
    id: str
    name: str
    x: float
    y: float
    violations: int
    total: int


class TrendItem(BaseModel):
    headline: str
    category: str
    source: str
    time_ago: str
    scraped_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ScrapeStatus(BaseModel):
    running: bool
    last_run: Optional[datetime] = None
    records_today: int = 0
    errors: list[str] = []

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
