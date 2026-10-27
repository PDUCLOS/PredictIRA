"""Application Flask PredictIRA : formulaire prérempli par département / semaine.

Refonte 2026 : modèle chargé sans pickle (predictira.model), semaine encodée côté serveur,
variables manquantes ou non numériques refusées au lieu d'être silencieusement remplacées par NaN.
"""
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request
from pydantic import ValidationError

from predictira.data import DEPARTEMENTS, load_dataset, lookup
from predictira.model import IRAModel
from predictira.schemas import Features

ROOT = Path(__file__).resolve().parent

app = Flask(__name__)

df = load_dataset(ROOT)
model = IRAModel.from_repo(ROOT)

features = [
    {"name": "SYM1", "category": "symptomes", "label": "Symptome Douleur thoracique :", "tooltip": "Tendance de recherche des mots Douleur thoracique sur Google"},
    {"name": "SYM22", "category": "symptomes", "label": "Symptome Faiblesse :", "tooltip": "Tendance de recherche du mot Faiblesse sur Google"},
    {"name": "SYM23", "category": "symptomes", "label": "Symptome Toux :", "tooltip": "Tendance de recherche du mot Toux sur Google"},
    {"name": "SYM29", "category": "symptomes", "label": "Symptome Sifflements :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche du mot Sifflements sur Google"},
    {"name": "SYM3", "category": "symptomes", "label": "Symptome Essoufflement :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche du mot Essoufflement sur Google"},
    {"name": "SYM31", "category": "symptomes", "label": "Symptome Production de mucus :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche des mots Production de mucus sur Google"},
    {"name": "SYM34", "category": "symptomes", "label": "Symptome Maux de tête :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche des mots Maux de tête sur Google"},
    {"name": "SYM35", "category": "symptomes", "label": "Symptome Perte d'appétit :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche des mots Perte d'appétit sur Google"},
    {"name": "SYM5", "category": "symptomes", "label": "Symptome Nausées :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche du mot Nausées sur Google"},
    {"name": "SYM6", "category": "symptomes", "label": "Symptome Vomissements :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche du mot Vomissements sur Google"},
    {"name": "SYM68", "category": "symptomes", "label": "Symptome Frissons :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche du mot Frissons sur Google"},
    {"name": "SYM8", "category": "symptomes", "label": "Symptome Palpitations :", "tooltip": "Renseigner la valeur du symptome : Tendance de recherche du mot Palpitations sur Google"},
    {"name": "average_Co", "category": "polluants", "label": "Moyenne Monoxyde de carbone :", "tooltip": "Valeur moyenne du monoxyde de carbone sur la semaine de prédiction"},
    {"name": "average_IQA_global", "category": "polluants", "label": "Moyenne Indices polluants :", "tooltip": "Moyenne des indices de dangerosité des polluants sur la semaine de prédiction"},
    {"name": "average_No_2", "category": "polluants", "label": "Moyenne Dioxyde d'azote :", "tooltip": "Valeur moyenne du dioxyde d'azote sur la semaine de prédiction"},
    {"name": "average_O_3", "category": "polluants", "label": "Moyenne Ozone :", "tooltip": "Valeur moyenne de l'ozone sur la semaine de prédiction"},
    {"name": "average_Pm_2_5", "category": "polluants", "label": "Moyenne particules très fines (PM 2.5) :", "tooltip": "Valeur Moyenne des particules fines sur la semaine de prédiction"},
    {"name": "average_So_2", "category": "polluants", "label": "Moyenne Dioxyde de soufre :", "tooltip": "Valeur Moyenne du Dioxyde de soufre sur la semaine de prédiction"},
    {"name": "avg_pressure", "category": "divers", "label": "Pression atmosphérique moyenne :", "tooltip": "Moyenne de la pression atmosphérique de la semaine de prédiction"},
    {"name": "avg_temperature_max", "category": "divers", "label": "Moyenne Température Maximum :", "tooltip": "Moyenne de la température maximum de la semaine de prédiction"},
    {"name": "dept", "category": "entete", "label": "Département : ", "tooltip": "Numéro du département"},
    {"name": "indice", "category": "divers", "label": "Indice de la grippe :", "tooltip": "Valeur de la grippe de la semaine"},
    {"name": "week_cos", "category": "entete", "label": "Cosinus de la semaine :", "tooltip": "Transformation de la semaine sous forme trigonométrique"},
    {"name": "year", "category": "entete", "label": "Année :", "tooltip": "Année de la prédiction"}
]

feature_names = [f["name"] for f in features]
assert feature_names == model.features


@app.route("/")
def home():
    return render_template("homepage.html")


@app.route("/predict")
def predict_page():
    return render_template("prediction.html", features=features, departements=DEPARTEMENTS)


# Valeurs du jeu de démonstration pour un département / une année / une semaine
@app.route("/get_data/<int:dept>/<int:year>/<int:week>")
def get_data(dept, year, week):
    row = lookup(df, dept, year, week)
    if row is None:
        return jsonify({"error": "Aucune donnée trouvée pour ces paramètres"}), 404
    return jsonify(row)


@app.route("/predict", methods=["POST"])
def predict():
    missing = [f for f in feature_names if not request.form.get(f)]
    if missing:
        return jsonify({"error": f"Features manquantes : {missing}"}), 400
    try:
        data = Features(**{f: request.form[f] for f in feature_names})
    except ValidationError as e:
        return jsonify({"error": "; ".join(f"{err['loc'][0]} : {err['msg']}" for err in e.errors())}), 422
    prediction = float(model.predict_frame(pd.DataFrame([data.model_dump()]))[0])
    return jsonify({"prediction": round(prediction, 2)})


if __name__ == "__main__":
    app.run(port=5050)
