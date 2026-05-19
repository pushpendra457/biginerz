"""
ml_models/base_predictor.py

BasePredictor: every model's Predictor class inherits from this.

Provides:
  - Standard .pkl load/save at a consistent path
  - Abstract predict() that subclasses must implement
  - Shared calibration helpers (normalize_score, percentile_scale)
  - Metadata dict so /health can report version + training date
"""

import abc
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd

log = logging.getLogger("ml_base")

ML_ROOT = Path(__file__).parent


class BasePredictor(abc.ABC):
    """
    Inherit from this for every model.

    Subclass minimal contract:
        MODEL_NAME = "retailer_priority"          # matches subfolder name
        ARTIFACT_FILENAME = "pipeline.pkl"        # saved by train.py

        def predict(self, data: pd.DataFrame) -> Any:
            ...
    """

    MODEL_NAME: str = ""
    ARTIFACT_FILENAME: str = "pipeline.pkl"

    def __init__(self):
        self._artifacts: dict = {}
        self._metadata: dict = {}
        self._load_artifacts()

    # ── Path helpers ───────────────────────────────────────────

    @property
    def model_dir(self) -> Path:
        return ML_ROOT / self.MODEL_NAME

    @property
    def artifact_path(self) -> Path:
        return self.model_dir / self.ARTIFACT_FILENAME

    # ── Load ──────────────────────────────────────────────────

    def _load_artifacts(self):
        if not self.artifact_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {self.artifact_path}\n"
                f"Run:  python ml_models/{self.MODEL_NAME}/train.py"
            )
        bundle = joblib.load(self.artifact_path)
        # bundle is a dict saved by train.py — unpack it
        self._artifacts = bundle
        self._metadata = bundle.get("metadata", {})
        log.info(f"[{self.MODEL_NAME}] Loaded artifact: {self.artifact_path}")

    # ── Subclass must implement ────────────────────────────────

    @abc.abstractmethod
    def predict(self, data: pd.DataFrame) -> Any:
        """Run inference and return a result dict or list of dicts."""
        ...

    # ── Shared helpers ─────────────────────────────────────────

    def normalize_score(
        self,
        value: float,
        p5: float,
        p95: float,
        lo: float = 0.0,
        hi: float = 100.0,
    ) -> float:
        """Map a raw value to [lo, hi] using percentile anchors from training."""
        if p95 == p5:
            return lo
        normalized = (value - p5) / (p95 - p5) * (hi - lo) + lo
        return float(np.clip(normalized, lo, hi))

    def priority_label(self, score: float) -> str:
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        return "LOW"

    @property
    def metadata(self) -> dict:
        return {
            "model": self.MODEL_NAME,
            "artifact": str(self.artifact_path),
            **self._metadata,
        }