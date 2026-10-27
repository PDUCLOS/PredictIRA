import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from predictira.api import app, dataset, model  # noqa: E402
from predictira.data import week_cos  # noqa: E402
from predictira.schemas import Features  # noqa: E402

client = TestClient(app)


def _row(dept=69, week=5):
    r = client.get(f"/api/donnees/{dept}/2024/{week}").json()
    return r, {k: r[k] for k in model.features}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["variables"] == 24


def test_week_reconstruction_matches_cos():
    for w in (1, 13, 26, 39):
        sub = dataset[(dataset.year == 2024) & (dataset.week == w)]
        assert len(sub) == 11
        assert np.allclose(sub.week_cos, week_cos(w))


def test_every_dept_has_39_weeks_in_2024():
    counts = dataset[dataset.year == 2024].groupby("dept").week.nunique()
    assert (counts == 39).all() and len(counts) == 11


def test_dataset_fits_schema_bounds():
    for rec in dataset[model.features].to_dict(orient="records"):
        Features(**rec)


def test_predict_matches_model_and_is_plausible():
    row, feats = _row()
    r = client.post("/api/predict", json=feats)
    assert r.status_code == 200
    pred = r.json()["prediction"]
    assert 0 < pred < 3000
    assert abs(pred - row["nb_passage_IRA"]) / row["nb_passage_IRA"] < 0.6


def test_predict_rejects_missing_and_extra_fields():
    _, feats = _row()
    bad = dict(feats)
    bad.pop("indice")
    assert client.post("/api/predict", json=bad).status_code == 422
    assert client.post("/api/predict", json={**feats, "foo": 1}).status_code == 422
    assert client.post("/api/predict", json={**feats, "week_cos": 10}).status_code == 422


def test_batch():
    _, feats = _row()
    r = client.post("/api/predict/batch", json=[feats, feats])
    assert r.status_code == 200 and len(r.json()) == 2


def test_unknown_dept_returns_404():
    assert client.get("/api/donnees/63/2024/5").status_code == 404


def test_flask_ui_routes():
    assert client.get("/").status_code == 200
    page = client.get("/predict").text
    assert "[69, \"Rh" in page and "[63," not in page  # liste issue des données (tojson)
    assert client.get("/get_data/69/2024/5").json()["dept"] == 69
    assert client.get("/get_data/63/2024/5").status_code == 404


def test_flask_predict_form_and_validation():
    _, feats = _row()
    r = client.post("/predict", data={k: str(v) for k, v in feats.items()})
    assert r.status_code == 200 and r.json()["prediction"] > 0
    form = {k: str(v) for k, v in feats.items()}
    form["indice"] = ""
    assert client.post("/predict", data=form).status_code == 400
    form["indice"] = "abc"
    assert client.post("/predict", data=form).status_code == 422


@pytest.mark.skipif(not (ROOT / "docs" / "metrics.json").exists(), reason="lancer scripts/evaluate.py")
def test_published_metrics_regression_guard():
    """Garde-fou sur les chiffres publiés dans docs/PORTFOLIO.md (mesurés le 2026-10-27)."""
    m = json.loads((ROOT / "docs" / "metrics.json").read_text(encoding="utf-8"))["modeles"]
    assert m["flask_lightgbm_24var"]["R2"] > 0.9
    assert m["flask_lightgbm_24var"]["MAE"] < 45
    # constat documenté : la persistance S-1 reste une référence très forte
    assert m["reference_persistance_S-1"]["MAE"] < 45

def test_original_cos_lookup_was_ambiguous():
    """Régression : l'ancien /get_data filtrait sur week_cos == cos(2π·w/52) et renvoyait
    la 1re ligne trouvée — pour S27→S39 c'était la semaine 52-w (S25→S13)."""
    w = 30
    sub = dataset[(dataset.dept == 69) & (dataset.year == 2024)
                  & np.isclose(dataset.week_cos, week_cos(w))]
    assert sorted(sub.week) == [22, 30]
    assert sub.iloc[0].week == 22  # ce que l'ancienne version renvoyait
    assert client.get(f"/get_data/69/2024/{w}").json()["week"] == 30  # version corrigée
