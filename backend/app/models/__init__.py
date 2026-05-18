"""
Centralised import for all SQLAlchemy models.
Import this module (not individual files) so that Base.metadata is always
fully populated before create_all() or Alembic autogenerate runs.
"""
from app.models.territory import Territory                          # noqa: F401
from app.models.rep import Rep                                      # noqa: F401
from app.models.retailer import Retailer                            # noqa: F401
from app.models.grower import Grower                                # noqa: F401
from app.models.visit import Visit                                  # noqa: F401
from app.models.retailer_inventory_weekly import RetailerInventoryWeekly  # noqa: F401
from app.models.retailer_pos import RetailerPOS                    # noqa: F401
from app.models.digital_funnel_weekly import DigitalFunnelWeekly   # noqa: F401
from app.models.whatsapp_message_log import WhatsAppMessageLog     # noqa: F401
 
__all__ = [
    "Territory",
    "Rep",
    "Retailer",
    "Grower",
    "Visit",
    "RetailerInventoryWeekly",
    "RetailerPOS",
    "DigitalFunnelWeekly",
    "WhatsAppMessageLog",
]