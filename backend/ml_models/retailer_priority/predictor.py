"""
ml_models/retailer_priority/predictor.py

RetailerPriorityPredictor

Called exclusively from:
    app/services/ml_services.py  →  RetailerPriorityService

NEVER called directly from a resource/route.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from ml_models.base_predictor import BasePredictor

log = logging.getLogger("predictor.retailer_priority")

# ── Boost caps (keeps final score bounded) ────────────────────────────────────
WEATHER_BOOST_MAX  = 20.0
PEST_BOOST_MAX     = 15.0
NDVI_BOOST_MAX     = 15.0
INVENTORY_BOOST_MAX = 15.0
SALES_BOOST_MAX    = 12.0

# ── Hybrid score weights (must sum to 1.0) ────────────────────────────────────
WEIGHTS = {
    "ml":        0.60,
    "weather":   0.15,
    "pest":      0.12,
    "ndvi":      0.06,
    "inventory": 0.04,
    "sales":     0.03,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"


# ── Input dataclass (what the service passes in) ──────────────────────────────

@dataclass
class RetailerFeatures:
    # Geography
    state: str
    district: str
    tehsil: str
    # Sales
    weekly_sales_qty: float
    transactions: float
    avg_qty_per_txn: float
    sales_growth_rate: float
    # Inventory
    avg_inventory: float
    stockout_ratio: float
    # Visits
    weekly_visits: float
    days_since_last_visit: float
    # Grower
    avg_farm_size: float
    avg_grower_age: float
    scan_rate: float
    campaign_attendance_rate: float
    # Context (from live signals — set by service)
    temperature: float = 30.0
    humidity: float = 65.0
    rainfall_mm: float = 0.0
    ndvi_value: float = 0.45
    pest_risk: str = "medium"      # "high" | "medium" | "low"
    # Optional
    retailer_id: Optional[str] = None
    ndvi_override: Optional[float] = None


# ── Output dataclass ──────────────────────────────────────────────────────────

@dataclass
class PriorityResult:
    retailer_id: Optional[str]
    district: str
    tehsil: str
    ml_score: float
    weather_boost: float
    pest_boost: float
    ndvi_boost: float
    inventory_boost: float
    sales_boost: float
    final_priority_score: float
    priority_label: str           # CRITICAL / HIGH / MEDIUM / LOW
    reasons: list[str]
    next_best_action: str
    # Echo back context
    temperature: float
    humidity: float
    rainfall_mm: float
    ndvi_value: float
    pest_risk: str


# ── Predictor ─────────────────────────────────────────────────────────────────

class RetailerPriorityPredictor(BasePredictor):

    MODEL_NAME = "retailer_priority"
    ARTIFACT_FILENAME = "pipeline.pkl"

    def predict(self, features: RetailerFeatures) -> PriorityResult:
        ml_score = self._ml_score(features)

        w_boost, w_reasons = self._weather_boost(features)
        p_boost, p_reasons = self._pest_boost(features)
        n_boost, n_reasons = self._ndvi_boost(features)
        i_boost, i_reasons = self._inventory_boost(features)
        s_boost, s_reasons = self._sales_boost(features)

        final = float(np.clip(
            WEIGHTS["ml"]        * ml_score
            + WEIGHTS["weather"] * w_boost
            + WEIGHTS["pest"]    * p_boost
            + WEIGHTS["ndvi"]    * n_boost
            + WEIGHTS["inventory"] * i_boost
            + WEIGHTS["sales"]   * s_boost,
            0, 100
        ))

        all_reasons = w_reasons + n_reasons + p_reasons + i_reasons + s_reasons
        if not all_reasons:
            all_reasons = ["No major risk or opportunity signals detected."]

        return PriorityResult(
            retailer_id=features.retailer_id,
            district=features.district,
            tehsil=features.tehsil,
            ml_score=round(ml_score, 2),
            weather_boost=round(w_boost, 2),
            pest_boost=round(p_boost, 2),
            ndvi_boost=round(n_boost, 2),
            inventory_boost=round(i_boost, 2),
            sales_boost=round(s_boost, 2),
            final_priority_score=round(final, 2),
            priority_label=self.priority_label(final),
            reasons=all_reasons,
            next_best_action=self._next_best_action(features, final),
            temperature=features.temperature,
            humidity=features.humidity,
            rainfall_mm=features.rainfall_mm,
            ndvi_value=features.ndvi_value,
            pest_risk=features.pest_risk,
        )

    def predict_batch(self, feature_list: list[RetailerFeatures]) -> list[PriorityResult]:
        """Score multiple retailers, return sorted by final score desc."""
        results = [self.predict(f) for f in feature_list]
        return sorted(results, key=lambda r: r.final_priority_score, reverse=True)

    # ── ML inference ──────────────────────────────────────────

    def _ml_score(self, f: RetailerFeatures) -> float:
        pipeline = self._artifacts["pipeline"]
        p5  = self._artifacts["revenue_p5"]
        p95 = self._artifacts["revenue_p95"]

        row = pd.DataFrame([{
            "state": f.state,
            "district": f.district,
            "tehsil": f.tehsil,
            "weekly_sales_qty": f.weekly_sales_qty,
            "transactions": f.transactions,
            "avg_qty_per_txn": f.avg_qty_per_txn,
            "sales_growth_rate": f.sales_growth_rate,
            "avg_inventory": f.avg_inventory,
            "stockout_ratio": f.stockout_ratio,
            "weekly_visits": f.weekly_visits,
            "days_since_last_visit": f.days_since_last_visit,
            "avg_farm_size": f.avg_farm_size,
            "avg_grower_age": f.avg_grower_age,
            "scan_rate": f.scan_rate,
            "campaign_attendance_rate": f.campaign_attendance_rate,
        }])

        predicted_revenue = float(pipeline.predict(row)[0])
        return self.normalize_score(predicted_revenue, p5, p95)

    # ── Boost engines ─────────────────────────────────────────

    def _weather_boost(self, f: RetailerFeatures) -> tuple[float, list[str]]:
        boost, reasons = 0.0, []

        if f.humidity > 80:
            boost += 8
            reasons.append(f"High humidity ({f.humidity:.0f}%) → elevated fungal disease risk")
        elif f.humidity > 70:
            boost += 4
            reasons.append(f"Moderate humidity ({f.humidity:.0f}%) → watch for fungal conditions")

        if f.rainfall_mm > 20:
            boost += 10
            reasons.append(f"Heavy rain ({f.rainfall_mm}mm) → post-rain pesticide demand expected")
        elif f.rainfall_mm > 5:
            boost += 5
            reasons.append(f"Light rain ({f.rainfall_mm}mm) → moderate pesticide need likely")

        if f.temperature > 38:
            boost += 8
            reasons.append(f"Extreme heat ({f.temperature}°C) → severe crop stress risk")
        elif f.temperature > 35:
            boost += 5
            reasons.append(f"High temperature ({f.temperature}°C) → crop heat stress likely")
        elif f.temperature < 8:
            boost += 4
            reasons.append(f"Cold spell ({f.temperature}°C) → frost risk, sowing advisory needed")

        return min(boost, WEATHER_BOOST_MAX), reasons

    def _pest_boost(self, f: RetailerFeatures) -> tuple[float, list[str]]:
        if f.pest_risk == "high":
            return 15.0, ["High pest outbreak risk in district — urgent insecticide engagement"]
        elif f.pest_risk == "medium":
            return 8.0,  ["Moderate pest activity — proactive scouting recommended"]
        return 0.0, []

    def _ndvi_boost(self, f: RetailerFeatures) -> tuple[float, list[str]]:
        ndvi = f.ndvi_override if f.ndvi_override is not None else f.ndvi_value
        if ndvi < 0.25:
            return 15.0, ["Critical vegetation stress — immediate crop health intervention required"]
        elif ndvi < 0.40:
            return 8.0,  [f"Moderate crop stress (NDVI {ndvi:.2f}) — review fertilizer/pesticide regimen"]
        elif ndvi < 0.55:
            return 4.0,  [f"Below-average crop health (NDVI {ndvi:.2f})"]
        return 0.0, []

    def _inventory_boost(self, f: RetailerFeatures) -> tuple[float, list[str]]:
        boost, reasons = 0.0, []
        if f.stockout_ratio > 0.15:
            boost += 12
            reasons.append(f"Critical stockout risk ({f.stockout_ratio:.0%}) — immediate replenishment")
        elif f.stockout_ratio > 0.08:
            boost += 7
            reasons.append(f"Elevated stockout ratio ({f.stockout_ratio:.0%}) — monitor closely")
        if f.avg_inventory < 10:
            boost += 5
            reasons.append("Very low average inventory — replenishment discussion needed")
        return min(boost, INVENTORY_BOOST_MAX), reasons

    def _sales_boost(self, f: RetailerFeatures) -> tuple[float, list[str]]:
        boost, reasons = 0.0, []
        if f.sales_growth_rate > 0.30:
            boost += 8
            reasons.append(f"Strong sales momentum (+{f.sales_growth_rate:.0%}) — capitalize on growth")
        elif f.sales_growth_rate > 0.15:
            boost += 4
            reasons.append(f"Positive sales trend (+{f.sales_growth_rate:.0%})")
        elif f.sales_growth_rate < -0.10:
            boost += 6
            reasons.append(f"Declining sales ({f.sales_growth_rate:.0%}) — intervention required")

        if f.days_since_last_visit > 14:
            boost += 5
            reasons.append(f"Overdue visit ({f.days_since_last_visit:.0f} days) — relationship at risk")
        return min(boost, SALES_BOOST_MAX), reasons

    # ── Next best action ──────────────────────────────────────

    def _next_best_action(self, f: RetailerFeatures, score: float) -> str:
        if f.pest_risk == "high":
            return ("Urgent visit today. Lead with insecticide portfolio. "
                    "Run grower demo if footfall > 5.")
        if f.humidity > 80 or f.rainfall_mm > 10:
            return ("Post-rain visit recommended. Promote fungicide range "
                    "(Score 250 EC, Kavach). Check product availability.")
        if f.stockout_ratio > 0.12:
            return ("Inventory emergency. Coordinate with distributor for "
                    "same-day dispatch. Confirm order quantities before visit.")
        if f.sales_growth_rate > 0.25:
            return ("High-growth retailer — prioritize relationship visit. "
                    "Introduce new SKUs, discuss co-promotion.")
        if f.days_since_last_visit > 14:
            return "Long gap since last contact. Reconnect with product update and seasonal advisory."
        if score >= 60:
            return "Schedule visit within 48 hours. Bring product catalog and crop advisory."
        return "Routine check-in. Maintain engagement frequency."