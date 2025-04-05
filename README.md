<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/ya-repillez/IRA_Project">
    <img src="static/images/LogoTrans.png" alt="Logo" width="128" height="128">
  </a>
  
  <h3 align="center">API-IRA-PREDICTION</h3>

  <p align="center">
    Une application pour analyser et prédire les Infections Respiratoires Aiguës (IRA) à l'aide d'un modèle de Machine Learning.
    <br />
    <a href="https://github.com/PDUCLOS/PREDICTIRA/"><strong>Explorer la documentation »</strong></a>
    <br />
    <br />
  </p>
</p>

<!-- TABLE OF CONTENTS -->
## Table des matières

- [À propos du projet](#a-propos-du-projet)
- [Démarrage rapide](#démarrage-rapide)
- [Structure du projet](#structure-du-projet)
- [Utilisation](#utilisation)
- [Contribuer](#contribuer)
- [Contact](#contact)
- [Licence](#licence)

---

##  À propos du projet

PredictIRA est une API conçue pour analyser et prédire les infections respiratoires aiguës en utilisant le modèle LightGBM. 

###  Technologies utilisées


- **Flask** - Framework rapide pour les API avec Python
- **LightGBM** - Modèle de Machine Learning pour la classification et régression
- **Bootstrap** - Framework CSS pour un design moderne et réactif

---
---

##  Démarrage rapide

Pour obtenir une copie locale et exécuter l'application, suivez ces étapes :

1. Clonez le dépôt
```bash
git clone ya-repillez/IRA_Project
cd API-PredictionIRA
```
2. Installez les dépendances
```bash
pip install -r requirements.txt
```
3. Lancez l'application
```bash
python app.py
```
4. Accédez à l'application à `http://127.0.0.1:5000/`

---

##  Structure du projet

```bash
API-PredictionIRA/
├── static/
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   └── style.css
│   └── images/
│       ├── GoogleTrends.png
│       ├── image.png
│       ├── LogoTrans.png
│       ├── Pollution.png
│       └── Statistiques.png
├── templates/
│   ├── homepage.html
│   └── prediction.html
├── app.py
├── favicon.ico
├── lightgbm_model_ML_OK.pkl
├── standard_scaler.pkl
├── requirements.txt
```

---

##  Utilisation

L'application offre plusieurs fonctionnalités :
- Interface utilisateur responsive
- Prédiction des infections respiratoires aiguës
- Chargement et analyse du fichier CSV
- API REST rapide avec documentation automatique Swagger

---

##  Contribuer

Les contributions sont les bienvenues !
1. Forkez le projet
2. Créez une branche (`git checkout -b feature-nouvelle-fonctionnalité`)
3. Commitez vos modifications (`git commit -m 'Ajout d'une nouvelle fonctionnalité'`)
4. Poussez sur la branche (`git push origin feature-nouvelle-fonctionnalité`)
5. Ouvrez une Pull Request

---

##  Contact

- **Nom :** Equipe : Sarra ABBASSI​ && Mohammed ABUSARAR​ && Patrice DUCLOS​ && Yannick REPILLEZ​
- **Email :** m2iformationhopital@gmail.com

---

##  Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.
