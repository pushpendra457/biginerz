# app/resources/rep_resources.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession # <-- Ensure typing matches main
from app.database import get_db
from app.services.ml_services import RetailerPriorityService
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rep-tools", tags=["Sales Rep Operations"])

@router.get("/priority/{retailer_id}")
async def get_retailer_priority_dashboard(retailer_id: int, db: AsyncSession = Depends(get_db)):   

    try:
       
        result = await RetailerPriorityService.get_live_priority_score(
            db=db, 
            retailer_id=retailer_id
        )
        
        if not result:
            raise HTTPException(status_code=503, detail="ML Pipeline unavailable")
            
        return {"status": "success", "data": result.__dict__}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/my-retailers")
async def get_my_territory_retailers(
    rep_id: str = "REP_0001", 
    db: AsyncSession = Depends(get_db)
):
    try:
        results = await RetailerPriorityService.get_batch_territory_priorities(db=db, rep_id=rep_id)
        return {
            "status": "success",
            "data": results,
            "count": len(results)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # This will print the exact line numbers and error logs to your python terminal window
        logger.error(f"Batch processing error trace:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Database or Attribute Error: {str(e)}")