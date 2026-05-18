"""
Grower request / response schemas.
"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from enum import Enum
from app.schemas.common import OrmBase


class DeviceType(str, Enum):
    SMARTPHONE = "smartphone"
    KEYPAD = "keypad"
    UNKNOWN = "unknown"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class GrowerCreate(BaseModel):
    grower_id: str
    state: str
    district: str
    tehsil: str
    language: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    grower_age: Optional[int] = None
    gender: Optional[Gender] = None
    grower_farm_size: Optional[float] = None
    grower_crop_calendar: Optional[Any] = None      # flexible JSONB
    product_scan: bool = False
    product_name: Optional[str] = None
    product_scan_datetime: Optional[datetime] = None
    offline_campaign_attended: bool = False
    campaign_attendance_date: Optional[datetime] = None


class GrowerUpdate(BaseModel):
    language: Optional[str] = None
    device_type: Optional[DeviceType] = None
    grower_age: Optional[int] = None
    gender: Optional[Gender] = None
    grower_farm_size: Optional[float] = None
    grower_crop_calendar: Optional[Any] = None
    product_scan: Optional[bool] = None
    product_name: Optional[str] = None
    product_scan_datetime: Optional[datetime] = None
    offline_campaign_attended: Optional[bool] = None
    campaign_attendance_date: Optional[datetime] = None


class GrowerResponse(OrmBase):
    id: int
    grower_id: str
    state: str
    district: str
    tehsil: str
    language: Optional[str] = None
    device_type: DeviceType
    grower_age: Optional[int] = None
    gender: Optional[Gender] = None
    grower_farm_size: Optional[float] = None
    grower_crop_calendar: Optional[Any] = None
    product_scan: bool
    product_name: Optional[str] = None
    product_scan_datetime: Optional[datetime] = None
    offline_campaign_attended: bool
    campaign_attendance_date: Optional[datetime] = None


class GrowerSummary(OrmBase):
    id: int
    grower_id: str
    state: str
    district: str
    tehsil: str
    device_type: DeviceType