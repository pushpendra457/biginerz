# app/services/ml_services.py

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Import database models matching your ERD schema mapping
from app.models.rep import Rep
from app.models.retailer import Retailer
from ml_models import model_registry
from ml_models.retailer_priority.predictor import RetailerFeatures, PriorityResult

# Initialize robust logger references
logger = logging.getLogger("services.ml_services")
log = logger  # Dual alias to prevent 'log is not defined' scoping issues


class RetailerPriorityService:

    # ── 1. SINGLE RETAILER INFERENCE (For Detail View) ────────────────────────
    @staticmethod
    async def get_live_priority_score(
        db: AsyncSession, 
        retailer_id: int, 
        live_temp: float, 
        live_humidity: float, 
        live_rain: float, 
        live_ndvi: float, 
        live_pest: str
    ) -> Optional[PriorityResult]:
        """
        Calculates comprehensive hybrid predictions for a targeted retailer dashboard.
        """
        predictor = model_registry.retailer_priority
        if not predictor:
            logger.error("[ML] Retailer priority model instance not loaded in registry.")
            return None

        # Fetch individual retailer row details from DB
        stmt = select(Retailer).where(Retailer.id == retailer_id)
        result = await db.execute(stmt)
        retailer = result.scalars().first()
        
        if not retailer:
            raise ValueError(f"Retailer record with ID {retailer_id} not found.")

        # Build feature container payload using dynamic row properties
        input_data = RetailerFeatures(
            retailer_id=str(retailer_id),
            state=getattr(retailer, "state", "Unknown") or "Unknown",
            district=getattr(retailer, "district", "Unknown") or "Unknown",
            tehsil=getattr(retailer, "tehsil", "Unknown") or "Unknown",
            weekly_sales_qty=48.2,   # Baseline fallbacks for unmapped metrics
            transactions=14.0,
            avg_qty_per_txn=3.44,
            sales_growth_rate=0.18,
            avg_inventory=15.0,
            stockout_ratio=0.05,
            weekly_visits=1.5,
            days_since_last_visit=6.0,
            avg_farm_size=5.4,
            avg_grower_age=42.1,
            scan_rate=0.35,
            campaign_attendance_rate=0.22,
            # Hot dynamic live parameters
            temperature=live_temp,
            humidity=live_humidity,
            rainfall_mm=live_rain,
            ndvi_value=live_ndvi,
            pest_risk=live_pest
        )

        return predictor.predict(input_data)


    # ── 2. BATCH TERRITORY INFERENCE (For List/Master View) ───────────────────
    @staticmethod
    async def get_batch_territory_priorities(db: AsyncSession, rep_id: str) -> list[dict]:
        """
        Traverses the many-to-many territory bridge to load, score, and sort
        all retailers belonging to a rep's assigned region boundary.
        """
        predictor = model_registry.retailer_priority
        if not predictor:
            raise ValueError("ML priority inference pipeline asset is unavailable.")

        # Step 1: Query representative table to extract target territory boundary ID
        rep_stmt = select(Rep).where(Rep.rep_id == rep_id)
        rep_result = await db.execute(rep_stmt)
        representative = rep_result.scalars().first()

        if not representative:
            logger.warning(f"[ML Batch] Representative query empty for identifier: '{rep_id}'")
            return []

        target_territory_id = representative.territory_id

        # Step 2: Extract retailers sharing the same territory integer assignment
        stmt = select(Retailer).where(Retailer.territory_id == target_territory_id)
        result = await db.execute(stmt)
        retailers = result.scalars().all()

        if not retailers:
            logger.info(f"[ML Batch] No retailers mapped inside territory boundary index: {target_territory_id}")
            return []

        # Step 3: Establish localized territory environment metrics context
        live_temp = 36.5
        live_humidity = 82.0
        live_rain = 5.0
        live_ndvi = 0.34
        live_pest = "medium"

        feature_list = []
        retailer_name_map = {} 

        # Step 4: Map operational records securely into feature list matrix rows
        for r in retailers:
            # Map name correctly utilizing your schema-explicit 'shop_name' attribute property
            shop_name = getattr(r, "shop_name", f"Retailer #{r.id}") or f"Retailer #{r.id}"
            retailer_name_map[str(r.id)] = shop_name
            
            features = RetailerFeatures(
                retailer_id=str(r.id),
                state=getattr(r, "state", "Unknown") or "Unknown",
                district=getattr(r, "district", "Unknown") or "Unknown",
                tehsil=getattr(r, "tehsil", "Unknown") or "Unknown",
                weekly_sales_qty=48.2, 
                transactions=14.0,
                avg_qty_per_txn=3.44,
                sales_growth_rate=0.18,
                avg_inventory=15.0,
                stockout_ratio=0.05,
                weekly_visits=1.5,
                days_since_last_visit=6.0,
                avg_farm_size=5.4,
                avg_grower_age=42.1,
                scan_rate=0.35,
                campaign_attendance_rate=0.22,
                temperature=live_temp,
                humidity=live_humidity,
                rainfall_mm=live_rain,
                ndvi_value=live_ndvi,
                pest_risk=live_pest
            )
            feature_list.append(features)

        # Step 5: Execute fast matrix calculation loop inside your scikit-learn ensemble pipeline
        batch_results = predictor.predict_batch(feature_list)

        # Step 6: Format standard structure output array optimized for your Vue view templates
        ui_payload = []
        for res in batch_results:
            ui_payload.append({
                "id": res.retailer_id,
                "name": retailer_name_map.get(res.retailer_id, "Unknown"),
                "tehsil": res.tehsil,
                "score": res.final_priority_score,
                "label": res.priority_label,
                "action": res.next_best_action
            })

        return ui_payload