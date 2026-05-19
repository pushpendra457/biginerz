"""
ml_models/registry.py
 
ModelRegistry loads every trained .pkl artifact once at startup
and exposes them as typed attributes.
 
Adding a new model:
  1. Create ml_models/<name>/  with train.py + predictor.py
  2. Add an entry to REGISTRY_MAP below
  3. Done — the predictor is auto-exposed as model_registry.<name>
"""
 
import logging
from pathlib import Path
from typing import Optional
 
log = logging.getLogger("ml_registry")
 
# Root of ml_models/ folder (same dir as this file)
ML_ROOT = Path(__file__).parent
 
# ──────────────────────────────────────────────────────────────
# REGISTRY MAP
# key          → subfolder name inside ml_models/
# value        → Predictor class to instantiate
# ──────────────────────────────────────────────────────────────
REGISTRY_MAP = {
    "retailer_priority":       "ml_models.retailer_priority.predictor:RetailerPriorityPredictor",
    "grower_engagement":       "ml_models.grower_engagement.predictor:GrowerEngagementPredictor",
    "territory_optimizer":     "ml_models.territory_optimizer.predictor:TerritoryOptimizerPredictor",
    "campaign_roi":            "ml_models.campaign_roi.predictor:CampaignROIPredictor",
    "whatsapp_effectiveness":  "ml_models.whatsapp_effectiveness.predictor:WhatsappEffectivenessPredictor",
}
 
 
def _import_class(dotted_path: str):
    """Import a class from a 'module.path:ClassName' string."""
    module_path, class_name = dotted_path.split(":")
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
 
 
class ModelRegistry:
    """
    Lazy-loads each model predictor on first attribute access.
    If the .pkl doesn't exist yet (model not trained), returns None
    and logs a warning instead of crashing the whole app.
    """
 
    def __init__(self):
        self._cache: dict = {}
 
    def _load(self, name: str):
        if name in self._cache:
            return self._cache[name]
 
        if name not in REGISTRY_MAP:
            raise AttributeError(f"No ML model registered as '{name}'")
 
        try:
            cls = _import_class(REGISTRY_MAP[name])
            instance = cls()          # each predictor loads its own .pkl in __init__
            self._cache[name] = instance
            log.info(f"[ML] Loaded model: {name}")
            return instance
        except FileNotFoundError as e:
            log.warning(f"[ML] Model '{name}' not trained yet: {e}")
            self._cache[name] = None
            return None
        except Exception as e:
            log.error(f"[ML] Failed to load model '{name}': {e}")
            self._cache[name] = None
            return None
 
    # ── Typed accessors (IDE autocomplete works) ──────────────
 
    @property
    def retailer_priority(self):
        return self._load("retailer_priority")
 
    @property
    def grower_engagement(self):
        return self._load("grower_engagement")
 
    @property
    def territory_optimizer(self):
        return self._load("territory_optimizer")
 
    @property
    def campaign_roi(self):
        return self._load("campaign_roi")
 
    @property
    def whatsapp_effectiveness(self):
        return self._load("whatsapp_effectiveness")
 
    def health(self) -> dict:
        """Returns load status of all models — used by /health endpoint."""
        statuses = {}
        for name in REGISTRY_MAP:
            inst = self._cache.get(name, "not_loaded")
            if inst == "not_loaded":
                statuses[name] = "not_loaded"
            elif inst is None:
                statuses[name] = "error_or_untrained"
            else:
                statuses[name] = "ok"
        return statuses
 
    def preload_all(self):
        """Call at app startup to eagerly load every model."""
        for name in REGISTRY_MAP:
            self._load(name)