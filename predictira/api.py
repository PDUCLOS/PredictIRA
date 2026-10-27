"""API FastAPI PredictIRA + interface Flask montée sur « / » (un seul conteneur).

    uvicorn predictira.api:app --port 18765
    → /api/docs (Swagger), /api/predict, /api/donnees/{dept}/{year}/{week}, /health, / (formulaire)
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, HTTPException

from .data import DEPARTEMENTS, load_dataset, lookup
from .model import IRAModel
from .schemas import Features, Prediction

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "lightgbm_ira_24var"

model = IRAModel.from_repo(ROOT)
dataset = load_dataset(ROOT)

api = FastAPI(
    title="PredictIRA API",
    version="2.0.0",
    description="Estimation hebdomadaire des passages aux urgences pour infections respiratoires "
                "aiguës (IRA) par département — modèle LightGBM à 24 variables.",
    docs_url="/docs",
)


@api.get("/departements")
def departements() -> dict[int, str]:
    return DEPARTEMENTS


@api.get("/donnees/{dept}/{year}/{week}")
def donnees(dept: int, year: int, week: int) -> dict:
    """Variables observées (jeu de démonstration 2024) + valeur réelle nb_passage_IRA."""
    row = lookup(dataset, dept, year, week)
    if row is None:
        raise HTTPException(404, "Aucune donnée pour ces paramètres")
    return row


@api.post("/predict", response_model=Prediction)
def predict(features: Features) -> Prediction:
    value = float(model.predict_frame(pd.DataFrame([features.model_dump()]))[0])
    return Prediction(prediction=round(value, 1), modele=MODEL_NAME)


@api.post("/predict/batch", response_model=list[Prediction])
def predict_batch(items: list[Features]) -> list[Prediction]:
    if not items or len(items) > 1000:
        raise HTTPException(422, "Entre 1 et 1000 lignes")
    values = model.predict_frame(pd.DataFrame([f.model_dump() for f in items]))
    return [Prediction(prediction=round(float(v), 1), modele=MODEL_NAME) for v in values]


app = FastAPI(title="PredictIRA", docs_url=None, redoc_url=None)
_started = time.time()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "modele": MODEL_NAME, "variables": len(model.features),
            "uptime_s": round(time.time() - _started, 1)}


app.mount("/api", api)

from app import app as flask_app  # noqa: E402  (interface historique)

app.mount("/", WSGIMiddleware(flask_app))
