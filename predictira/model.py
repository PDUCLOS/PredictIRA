"""Modèle de prédiction : LightGBM (format texte) + standardisation (JSON), sans pickle."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd


@dataclass
class IRAModel:
    booster: lgb.Booster
    features: list[str]
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def from_repo(cls, root: str | Path) -> "IRAModel":
        root = Path(root)
        booster = lgb.Booster(model_file=str(root / "models" / "lightgbm_ira_24var.txt"))
        sc = json.loads((root / "models" / "scaler_24var.json").read_text(encoding="utf-8"))
        if sc["features"] != booster.feature_name():
            raise ValueError("Le scaler et le modèle n'ont pas les mêmes variables")
        return cls(booster, sc["features"], np.array(sc["mean"]), np.array(sc["scale"]))

    def predict_frame(self, df: pd.DataFrame) -> np.ndarray:
        """Prédit le nombre de passages IRA pour chaque ligne (colonnes = self.features)."""
        x = (df[self.features].to_numpy(dtype="float64") - self.mean) / self.scale
        return self.booster.predict(x)
