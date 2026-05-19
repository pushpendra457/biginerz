"""
ml_models/__init__.py
 
Central registry for all ML models.
Import from here everywhere in the app — never import a model file directly.
 
Usage:
    from ml_models import model_registry
    score = model_registry.retailer_priority.predict(data)
"""
 
from ml_models.registry import ModelRegistry
 
model_registry = ModelRegistry()
 
__all__ = ["model_registry"]