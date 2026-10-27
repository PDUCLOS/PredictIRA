"""Convertit les artefacts pickle hérités en formats non exécutables.

- lightgbm_model_ML_OK.pkl (Booster)          -> models/lightgbm_ira_24var.txt  (format texte LightGBM)
- standard_scaler.pkl (StandardScaler)        -> models/scaler_24var.json       (moyennes / écarts-types)
- ../industrialisation/LightGBM_best_model.pkl -> models/lightgbm_indus_28var.txt

Les pickles sont lus via une liste blanche de classes (predictira.safe_load).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from predictira.safe_load import safe_joblib_load  # noqa: E402

booster = safe_joblib_load(str(ROOT / "lightgbm_model_ML_OK.pkl"))
booster.save_model(str(ROOT / "models" / "lightgbm_ira_24var.txt"))

scaler = safe_joblib_load(str(ROOT / "standard_scaler.pkl"))
assert list(scaler.feature_names_in_) == booster.feature_name()
(ROOT / "models" / "scaler_24var.json").write_text(json.dumps({
    "features": list(scaler.feature_names_in_),
    "mean": scaler.mean_.tolist(),
    "scale": scaler.scale_.tolist(),
    "n_samples_seen": int(scaler.n_samples_seen_),
}, indent=1), encoding="utf-8")

indus_pkl = ROOT.parent / "industrialisation" / "LightGBM_best_model.pkl"
if indus_pkl.exists():
    safe_joblib_load(str(indus_pkl)).booster_.save_model(str(ROOT / "models" / "lightgbm_indus_28var.txt"))
print("exporté :", sorted(p.name for p in (ROOT / "models").iterdir()))
