"""Banc d'évaluation PredictIRA — rejoue les modèles livrés sur le jeu de test du dépôt.

Découpage temporel : le jeu `df_Test_Indust.csv` couvre 2024-S01 → 2024-S39 (11 départements
d'Auvergne-Rhône-Alpes) ; le scaler livré a été ajusté sur 2 733 lignes de moyenne d'année
2021,9 : les modèles n'ont donc (a priori) jamais vu 2024. La ligne 2023-S52 de chaque
département sert uniquement de point de départ à la référence « persistance ».

Usage : python scripts/evaluate.py  → docs/metrics.json + docs/img/eval_*.png
"""
from __future__ import annotations

import json
import platform
import statistics
import sys
import time
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

from predictira.data import load_dataset  # noqa: E402
from predictira.model import IRAModel  # noqa: E402


def metrics(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    err = p - y
    return {
        "MAE": round(float(np.mean(np.abs(err))), 1),
        "RMSE": round(float(np.sqrt(np.mean(err**2))), 1),
        "R2": round(float(1 - np.sum(err**2) / np.sum((y - y.mean()) ** 2)), 3),
        "MAPE_%": round(float(np.mean(np.abs(err) / y) * 100), 1),
        "WAPE_%": round(float(np.sum(np.abs(err)) / np.sum(y) * 100), 1),
        "biais_moyen": round(float(np.mean(err)), 1),
    }


def load_test() -> pd.DataFrame:
    return load_dataset(ROOT).sort_values(["dept", "year", "week"]).reset_index(drop=True)


def latency(fn, n=300) -> dict:
    for _ in range(20):
        fn()
    t = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        t.append((time.perf_counter() - t0) * 1000)
    t.sort()
    return {"p50_ms": round(statistics.median(t), 3), "p95_ms": round(t[int(0.95 * n)], 3)}


def main() -> None:
    df = load_test()
    test = df[df["year"] == 2024].copy()
    y = test["nb_passage_IRA"].to_numpy()

    flask_model = IRAModel.from_repo(ROOT)  # modèle de l'application Flask (24 variables + scaler)
    test["pred_flask"] = flask_model.predict_frame(test)

    # modèle du dépôt « industrialisation » (28 variables, sans scaler), exporté en texte
    indus = lgb.Booster(model_file=str(ROOT / "models" / "lightgbm_indus_28var.txt"))
    indus_feats = indus.feature_name()
    test["pred_indus"] = indus.predict(test[indus_feats])

    # Référence naïve : la valeur observée la semaine précédente dans le même département
    df["persistance"] = df.groupby("dept")["nb_passage_IRA"].shift(1)
    test["pred_persist"] = df.loc[test.index, "persistance"].to_numpy()
    # Exploratoire : moyenne 50/50 modèle + persistance (aucun paramètre ajusté sur le test)
    test["pred_blend"] = (test["pred_flask"] + test["pred_persist"]) / 2

    res = {
        "jeu_de_test": {
            "fichier": "df_Test_Indust.csv",
            "lignes": int(len(test)),
            "departements": sorted(int(d) for d in test["dept"].unique()),
            "periode": "2024-S01 → 2024-S39",
            "cible_moyenne": round(float(y.mean()), 1),
        },
        "modeles": {
            "flask_lightgbm_24var": metrics(y, test["pred_flask"]),
            "industrialisation_lightgbm_28var": metrics(y, test["pred_indus"]),
            "reference_persistance_S-1": metrics(y, test["pred_persist"]),
            "exploratoire_moyenne_flask_persistance": metrics(y, test["pred_blend"]),
        },
    }

    # Erreur par département (modèle Flask) et par saison
    res["mae_par_departement_flask"] = {
        int(d): round(float(np.mean(np.abs(g["pred_flask"] - g["nb_passage_IRA"]))), 1)
        for d, g in test.groupby("dept")
    }
    hiver = test["week"] <= 13
    res["par_periode"] = {
        "S01-S13 (hiver)": {k: metrics(test.loc[hiver, "nb_passage_IRA"], test.loc[hiver, c])["MAE"]
                            for k, c in [("flask", "pred_flask"), ("persistance", "pred_persist"), ("moyenne", "pred_blend")]},
        "S14-S39 (printemps-été)": {k: metrics(test.loc[~hiver, "nb_passage_IRA"], test.loc[~hiver, c])["MAE"]
                                   for k, c in [("flask", "pred_flask"), ("persistance", "pred_persist"), ("moyenne", "pred_blend")]},
    }

    # Importance des variables (gain) du modèle Flask
    b = flask_model.booster
    gain = b.feature_importance("gain")
    res["importance_gain_top8_flask"] = {
        f: round(float(g / gain.sum() * 100), 1)
        for f, g in sorted(zip(b.feature_name(), gain), key=lambda x: -x[1])[:8]
    }

    # Latence d'inférence (CPU, mono-ligne et lot complet)
    row = test.iloc[[0]]
    res["latence"] = {
        "flask_model_1_ligne": latency(lambda: flask_model.predict_frame(row)),
        "flask_model_lot_429": latency(lambda: flask_model.predict_frame(test), n=100),
        "industrialisation_1_ligne": latency(lambda: indus.predict(row[indus_feats])),
        "machine": f"{platform.processor()} · Python {platform.python_version()}",
    }
    out = ROOT / "docs" / "metrics.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    test.to_csv(ROOT / "docs" / "predictions_2024.csv", index=False,
                columns=["dept", "year", "week", "nb_passage_IRA", "pred_flask", "pred_indus", "pred_persist", "pred_blend"])
    print(json.dumps(res, indent=2, ensure_ascii=False))
    plot(test)


def plot(test: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), dpi=110)
    for ax, d, name in zip(axes, [69, 38, 15], ["Rhône (69)", "Isère (38)", "Cantal (15)"]):
        g = test[test["dept"] == d]
        ax.plot(g["week"], g["nb_passage_IRA"], "-o", ms=3, color="#111827", label="observé")
        ax.plot(g["week"], g["pred_flask"], "-", lw=2, color="#2563eb", label="LightGBM (Flask)")
        ax.plot(g["week"], g["pred_persist"], "--", lw=1.4, color="#f59e0b", label="persistance S-1")
        ax.set_title(f"{name} — 2024", fontsize=11)
        ax.set_xlabel("semaine")
        ax.grid(alpha=.3)
    axes[0].set_ylabel("passages aux urgences IRA / semaine")
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "img" / "eval_series.png")

    fig, ax = plt.subplots(figsize=(5.2, 5), dpi=110)
    ax.scatter(test["nb_passage_IRA"], test["pred_flask"], s=12, alpha=.6, color="#2563eb")
    m = test["nb_passage_IRA"].max() * 1.05
    ax.plot([0, m], [0, m], color="#9ca3af", lw=1)
    ax.set_xlabel("observé")
    ax.set_ylabel("prédit (LightGBM Flask)")
    ax.set_title("2024-S01→S39, 11 départements, 429 semaines")
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(ROOT / "docs" / "img" / "eval_scatter.png")


if __name__ == "__main__":
    main()
