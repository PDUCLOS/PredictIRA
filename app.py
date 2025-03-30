import joblib
import pandas as pd
import numpy as np
from math import cos, pi
from flask import Flask, render_template, request, jsonify
 
app = Flask(__name__)
 
# Charger le fichier CSV
csv_path = "df_Test_Indust.csv"
df = pd.read_csv(csv_path)
 
# Charger le modèle Machine Learning
model_path = "lightgbm_model_ML_OK.pkl"
try:
    with open(model_path, "rb") as file:
        model = joblib.load(file)
    print("Modèle chargé avec succès")
except (FileNotFoundError, joblib.externals.loky.process_executor.TerminatedWorkerError) as e:
    print(f"Erreur lors du chargement du modèle : {e}")
 
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
 
# Extraire uniquement les noms des features pour éviter les erreurs
feature_names = [f["name"] for f in features]
 
# Route principale qui affiche la page HTML avec le formulaire
@app.route("/")
def home():
    return render_template("homepage.html")
 
@app.route("/predict")
def predict_page():
    return render_template("prediction.html", features=features, data=df.to_dict(orient="records"))
 
# API pour récupérer les valeurs du CSV selon l'année, la semaine et le département
@app.route("/get_data/<int:dept>/<int:year>/<int:week>")
def get_data(year, week, dept):
    week_cos = cos(2 * pi * week / 52)
    print (week_cos)
    # Filtrer le DataFrame
    filtered_df = df[(df["year"] == year) & (df["week_cos"] == week_cos) & (df["dept"] == dept)]
    print (filtered_df)
 
    if not filtered_df.empty:
        # Retourner la première correspondance
        return jsonify(filtered_df.iloc[0].to_dict())
    return jsonify({"error": "Aucune donnée trouvée pour ces paramètres"})
 
@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Récupérer les valeurs du formulaire et les afficher
        input_data = {feature: request.form.get(feature) for feature in feature_names}
 
        # Vérifier les features manquantes
        missing_features = [f for f in feature_names if f not in input_data]
        if missing_features:
            print("Features manquantes :", missing_features)
            return jsonify({"error": f"Features manquantes : {missing_features}"})
 
        # Conversion en DataFrame et en float puis standardisation
        input_df = pd.DataFrame([input_data])
        input_df = input_df.astype('float64')
  
        if input_df.shape[1] != len(feature_names):
            return jsonify({"error": f"Nombre de features incorrect : {input_df.shape[1]} au lieu de {len(feature_names)}."})
 
        # Vérifier les types de données avant la standardisation
        for column in input_df.columns:
            if not np.issubdtype(input_df[column].dtype, np.number):
                return jsonify({"error": f"Type de donnée incorrect pour la feature : {column}"})
 
        scaler = joblib.load('standard_scaler.pkl')
        input_df = scaler.transform(input_df)

        # Faire la prédiction avec le modèle
        prediction = model.predict(input_df)[0]
        return jsonify({"prediction": round(prediction, 2)})
 
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)})
 
if __name__ == "__main__":
    app.run() 