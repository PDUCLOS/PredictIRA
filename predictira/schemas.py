"""Schéma d'entrée validé : les 24 variables du modèle, avec des bornes physiques larges."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_TREND = dict(ge=0, le=100, description="Indice Google Trends (0-100)")


class Features(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {
        "SYM1": 90, "SYM22": 68, "SYM23": 72, "SYM29": 33, "SYM3": 48, "SYM31": 72, "SYM34": 70,
        "SYM35": 0, "SYM5": 59, "SYM6": 42, "SYM68": 53, "SYM8": 57, "average_Co": 196.1,
        "average_IQA_global": 1.33, "average_No_2": 8.34, "average_O_3": 49.5, "average_Pm_2_5": 9.44,
        "average_So_2": 0.67, "avg_pressure": 989.1, "avg_temperature_max": 7.28, "dept": 1,
        "indice": 226.3, "week_cos": 0.9927, "year": 2024}})

    SYM1: float = Field(**_TREND)
    SYM22: float = Field(**_TREND)
    SYM23: float = Field(**_TREND)
    SYM29: float = Field(**_TREND)
    SYM3: float = Field(**_TREND)
    SYM31: float = Field(**_TREND)
    SYM34: float = Field(**_TREND)
    SYM35: float = Field(**_TREND)
    SYM5: float = Field(**_TREND)
    SYM6: float = Field(**_TREND)
    SYM68: float = Field(**_TREND)
    SYM8: float = Field(**_TREND)
    average_Co: float = Field(ge=0, le=5000)
    average_IQA_global: float = Field(ge=0, le=10)
    average_No_2: float = Field(ge=0, le=500)
    average_O_3: float = Field(ge=0, le=500)
    average_Pm_2_5: float = Field(ge=0, le=500)
    average_So_2: float = Field(ge=0, le=500)
    avg_pressure: float = Field(ge=500, le=1100, description="hPa")
    avg_temperature_max: float = Field(ge=-40, le=50, description="°C")
    dept: int = Field(ge=1, le=976, description="Numéro de département")
    indice: float = Field(ge=0, le=5000, description="Indice grippal de la semaine")
    week_cos: float = Field(ge=-1, le=1, description="cos(2π·semaine/52)")
    year: int = Field(ge=2015, le=2035)


class Prediction(BaseModel):
    prediction: float = Field(description="Passages aux urgences pour IRA estimés sur la semaine")
    modele: str
