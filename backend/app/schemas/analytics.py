"""
Schemas for:
  - RetailerInventoryWeekly
  - RetailerPOS
  - DigitalFunnelWeekly
  - WhatsAppMessageLog
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum
from app.schemas.common import OrmBase


# ── Inventory ─────────────────────────────────────────────────────────────────

class InventoryCreate(BaseModel):
    retailer_id: int
    sku_id: str
    sku_name: str
    sku_qty: float = 0.0
    week_end_date: date   # must be a Sunday


class InventoryUpdate(BaseModel):
    sku_qty: Optional[float] = None


class InventoryResponse(OrmBase):
    id: int
    retailer_id: int
    sku_id: str
    sku_name: str
    sku_qty: float
    week_end_date: date

    @property
    def is_out_of_stock(self) -> bool:
        return self.sku_qty == 0


# ── POS Transactions ──────────────────────────────────────────────────────────

class POSCreate(BaseModel):
    retailer_id: int
    transaction_id: str
    sku_id: str
    sku_name: str
    sku_qty: float
    sku_price: float
    transaction_date: date


class POSResponse(OrmBase):
    id: int
    retailer_id: int
    transaction_id: str
    sku_id: str
    sku_name: str
    sku_qty: float
    sku_price: float
    transaction_date: date

    @property
    def line_total(self) -> float:
        return round(self.sku_qty * self.sku_price, 2)


# ── Digital Funnel ─────────────────────────────────────────────────────────────

class CampaignCrop(str, Enum):
    WHEAT = "wheat"
    MUSTARD = "mustard"
    CHICKPEA = "chickpea"
    POTATO = "potato"


class FunnelCreate(BaseModel):
    campaign_id: str = Field(..., example="CMP_RABI25_001")
    week_start_date: date
    social_post_impression: int = Field(..., ge=0)
    landing_page_visits: int = Field(..., ge=0)
    lead_form_submission: int = Field(..., ge=0)
    campaign_crop: CampaignCrop
    campaign_product: str


class FunnelUpdate(BaseModel):
    social_post_impression: Optional[int] = None
    landing_page_visits: Optional[int] = None
    lead_form_submission: Optional[int] = None


class FunnelResponse(OrmBase):
    id: int
    campaign_id: str
    week_start_date: date
    social_post_impression: int
    landing_page_visits: int
    lead_form_submission: int
    campaign_crop: str
    campaign_product: str


# ── WhatsApp Message Log ───────────────────────────────────────────────────────

class WhatsAppCreate(BaseModel):
    message_row_id: str = Field(..., example="WAM_RABI25_00001")
    grower_id: int
    campaign_product: str
    campaign_crop: str
    message_sent_date: date
    delivered_status: bool = False
    opened_status: bool = False
    clicked_status: bool = False


class WhatsAppResponse(OrmBase):
    id: int
    message_row_id: str
    grower_id: int
    campaign_product: str
    campaign_crop: str
    message_sent_date: date
    delivered_status: bool
    opened_status: bool
    clicked_status: bool