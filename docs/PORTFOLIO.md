# PredictIRA — fiche portfolio vérifiée (27 octobre 2026)

Source de vérité pour l'intégration au portfolio pduclos.github.io (slug `predictira`).
Tous les chiffres ci-dessous ont été **mesurés pendant cette session** sur la machine de démonstration
(Windows 11, Ryzen 9 3900X, 32 Go, Python 3.12.3, LightGBM 4.7.0). Ce qui n'a pas pu être exécuté est signalé comme tel.

- Dépôt principal : https://github.com/PDUCLOS/PredictIRA — branche `feat/vitrine-predictira`
- Dépôt associé : https://github.com/PDUCLOS/industrialisation — branche `feat/vitrine-predictira`
- Vitrine : `docs/index.html` (GitHub Pages, dossier `docs/`)
- Mesures brutes : `docs/metrics.json`, prédictions ligne à ligne : `docs/predictions_2024.csv`

## En une phrase

Prédiction hebdomadaire des passages aux urgences pour infections respiratoires aiguës (IRA) par département
(LightGBM, 24 variables : recherches Google de symptômes, pollution, météo, indice grippal), projet d'équipe de formation
relancé en 2026 : mesuré sur 2024, six défauts reproduits et corrigés, API FastAPI validée, Docker et Kubernetes.

## Ce qui a été fait dans cette session

1. Clonage, lecture du code, lancement local (Python 3.12, uvicorn sur le port 18765).
2. **Audit de sécurité des pickles** : désassemblage `pickletools` (classes numpy, scikit-learn `StandardScaler`, LightGBM
   uniquement), lecture via un unpickler à liste blanche, export en **format texte LightGBM + JSON** ; l'exécution ne charge plus aucun pickle.
3. **Évaluation** (`scripts/evaluate.py`) sur le découpage temporel disponible, comparée à une référence naïve.
4. **Corrections** de l'application Flask (voir « Défauts trouvés »).
5. **API FastAPI** (`predictira/api.py`) avec schéma Pydantic (24 champs obligatoires, bornes physiques, champs inconnus refusés),
   lot de 1 à 1 000 lignes, Swagger ; l'interface Flask d'origine est montée sur `/` dans la même application (a2wsgi).
6. **13 tests pytest** (dont un test qui rejoue l'ancien filtre défectueux, un test qui vérifie le refus d'un pickle malveillant).
7. **Dockerfile** (python:3.12-slim, non-root, healthcheck) et **deploy/k8s** kustomize (base + overlays `local` et `cloud`).
8. **docs/architecture.drawio** (4 pages) + exports PNG vérifiés ; captures réelles ; vitrine ; vidéo narrée.
9. Dépôt `industrialisation` : client HTML corrigé, API à contrôle strict des variables, README des mesures.

## Données et découpage temporel

- Le projet **ne cite aucune source de données** et ne contient ni données ni code d'entraînement. **Aucun téléchargement n'a été effectué.**
- Jeu de test présent dans le dépôt : `df_Test_Indust.csv`, 440 lignes = 11 départements d'Auvergne-Rhône-Alpes
  (01, 03, 07, 15, 26, 38, 42, 43, 69, 73, 74) × 2024-S01 → S39, plus une ligne 2023-S52 par département.
- Le `StandardScaler` livré a été ajusté sur **2 733 lignes** dont l'année moyenne est **2021,9** (écart-type 1,38) :
  2024 est donc, selon toute vraisemblance, hors entraînement. Cela n'a **pas pu être prouvé** (données d'entraînement absentes).
- Évaluation sur les **429 lignes 2024** ; la ligne 2023-S52 sert uniquement de point de départ à la persistance.
- La semaine n'est encodée que par `week_cos` (pas de sinus) : elle est reconstruite par le rang des lignes puis contrôlée par le cosinus.

## Tableau de mesures

Test : 2024-S01 → S39, 11 départements, 429 semaines. Cible moyenne observée : 256,7 passages / semaine.

| Modèle | MAE | RMSE | R² | MAPE | WAPE | Biais moyen |
|---|---:|---:|---:|---:|---:|---:|
| LightGBM 24 variables + scaler (application Flask) | **41,2** | 69,5 | **0,926** | 21,2 % | 16,1 % | −2,5 |
| Référence : persistance S-1 (valeur observée la semaine précédente) | 39,5 | 67,8 | 0,930 | 18,7 % | 15,4 % | +11,4 |
| Exploratoire : moyenne 50/50 modèle + persistance (aucun paramètre ajusté) | **30,6** | 50,0 | **0,962** | 16,2 % | 11,9 % | +4,5 |
| LightGBM 28 variables du dépôt « industrialisation » | 510,3 | 534,7 | −3,358 | 461,3 % | 198,8 % | +487,5 |

MAE par période :

| Période | LightGBM | Persistance | Moyenne 50/50 |
|---|---:|---:|---:|
| S01–S13 (hiver) | 65,9 | 68,7 | 48,3 |
| S14–S39 (printemps-été) | 28,9 | 24,9 | 21,7 |

MAE du LightGBM par département : de 16,4 (Cantal, 15) à 121,3 (Rhône, 69).

Importance (gain) du LightGBM : département 31,5 %, NO₂ 25,5 %, pression 7,4 %, indice grippal 7,0 %, SO₂ 6,0 %,
SYM22 (faiblesse) 2,9 %, SYM23 (toux) 2,6 %, O₃ 2,5 %.

Latence (CPU, Ryzen 9 3900X) :

| Mesure | p50 | p95 |
|---|---:|---:|
| Inférence, 1 ligne (scaler + LightGBM) | 0,431 ms | 0,657 ms |
| Inférence, lot de 429 lignes | 0,878 ms | 1,36 ms |
| Inférence, modèle « industrialisation », 1 ligne | 0,716 ms | 0,882 ms |
| HTTP de bout en bout `POST /api/predict` (500 appels séquentiels, uvicorn 1 worker, local) | 7,05 ms | 8,89 ms |

Débit séquentiel HTTP mesuré : 139,3 requêtes/s (client Python `urllib`, un seul fil).

**Lecture honnête** : seul, le modèle ne bat pas la persistance sur l'ensemble de 2024 (MAE 41,2 contre 39,5) ;
il fait mieux en hiver, moins bien au printemps-été. Les erreurs sont complémentaires : la moyenne non ajustée des deux réduit
la MAE de 26 %. La moyenne 50/50 a été choisie a priori, mais elle est évaluée sur la même période que celle qui l'a suggérée :
c'est une piste, pas un résultat validé. Prochaine étape naturelle : réentraîner avec la valeur S-1 comme variable.

## Défauts trouvés (reproduits) et corrigés

| # | Constat | Correction |
|---|---|---|
| 1 | Préremplissage `/get_data` par égalité exacte de `week_cos` : rejoué sur 2024 (identique pour les 11 départements), **9 semaines sur 39 sans résultat** (S10, 11, 14, 16, 23, 28, 37, 38, 39 — arrondi flottant) et **S27 → S25, S29 → S23** (même cosinus pour s et 52 − s). | Semaine reconstruite par le rang + contrôle du cosinus ; test qui rejoue l'ancien filtre. |
| 2 | Champ caché `week_cos` rempli avec le numéro de semaine brut (ex. 10) ; seul un préremplissage réussi le corrigeait. | Cosinus calculé dans le navigateur ; erreur 404 affichée. |
| 3 | Puy-de-Dôme (63) proposé dans l'interface, absent des données. | Liste des départements générée depuis les données. |
| 4 | Champ vide → `None` → NaN : une prédiction était quand même renvoyée (le contrôle des champs manquants ne pouvait jamais se déclencher). | Pydantic : 400 (champ vide), 422 (non numérique / hors bornes / inconnu). |
| 5 | Dépôt `industrialisation` : le client HTML envoie `week`, `year`, `indice`, `SYM5`, `SYM24` (inconnus du modèle) et omet `SYM1`, `SYM28`, `SYM31`, `SYM35`, `average_O_3` ; LightGBM prédit par position (1 115 passages, valeur sans signification). | Client corrigé ; l'API renvoie 422 avec la liste des variables manquantes / inconnues. |
| 6 | Modèles livrés en pickle (exécution de code possible au chargement) ; `bootstrap.min.css` local vide (0 octet, non utilisé : les pages chargent Bootstrap depuis un CDN). | Export texte LightGBM + JSON, unpickler à liste blanche ; CSS vide laissé en l'état. |

## Écarts avec la fiche actuelle du portfolio (`build/projects.py`, slug `predictira`)

| Affirmation actuelle | Constat | Proposition |
|---|---|---|
| KPI « 28 variables » | Le modèle de l'application Flask utilise **24** variables ; le modèle à 28 variables est celui du dépôt `industrialisation`, qui est non exploitable (MAE 510, biais +488). | « 24 variables » ; mentionner que le modèle à 28 variables a été écarté après mesure. |
| Lead : « Modèle LightGBM servi par Flask, puis industrialisé en API FastAPI conteneurisée » | Exact historiquement, mais l'API FastAPI d'origine sert un **autre** modèle (28 var., sans département) que l'application Flask. | Préciser ; la v2 sert le modèle à 24 variables dans une seule application. |
| Contexte : « Anticiper la charge d'une à deux semaines » ; titre « avant la vague » | Le modèle utilise les signaux **de la semaine estimée** (nowcasting), pas un horizon de 1 à 2 semaines. | « Estimer la charge de la semaine en cours, avant la consolidation des données hospitalières. » |
| Extrait de code `industrialisation/api.py` | L'original contient un `try/except` qui renvoie `{"error": ...}` ; l'extrait de la fiche est simplifié. | Remplacer par un extrait exact (ci-dessous). |
| « Projet d'équipe de formation (M2i / Jedha) » | Le README mentionne M2i (adresse m2iformationhopital) ; « Jedha » n'apparaît dans aucun des deux dépôts. | Non vérifiable ici ; garder « M2i » seul ou faire confirmer. |
| Limites : « pas de tests, de validation de schéma ni de métriques publiées » | Vrai pour l'état d'origine ; **corrigé** en v2 : 13 tests, Pydantic, métriques publiées. | Mettre à jour la matrice : `tests=y`, `docker=y` (Dockerfile écrit, build non vérifié), `orch=y` (kustomize validé). |
| `langs` « HTML / CSS 70, Python 30 » | Non vérifié (l'API GitHub n'a pas été interrogée) ; la v2 ajoute surtout du Python. | À recalculer depuis GitHub après fusion. |

Chiffres reproduits : les 4 équipiers (README), LightGBM, Flask puis FastAPI, image `python:3.9` + uvicorn dans `industrialisation` — conformes.
Le portfolio n'annonçait aucune métrique de performance : il n'y avait rien d'autre à reproduire.

## Ce qui n'a pas pu être vérifié

- **`docker build` / `docker run`** : le moteur Docker Desktop était arrêté pendant la session (pipe `dockerDesktopLinuxEngine` absent) ;
  il n'a pas été démarré pour ne pas perturber les autres travaux. À la place, le contenu exact de l'image (fichiers copiés + `requirements.txt` seul,
  sans scikit-learn) a été installé dans un environnement Python 3.12 vierge et servi avec `WEB_CONCURRENCY=2` : `/health` et l'interface répondent (HTTP 200).
- **Déploiement Kubernetes réel** : seul le rendu `kubectl kustomize` a été validé (base : 7 objets, overlay local : 7, overlay cloud : 8).
- **Réentraînement** : impossible sans les données d'entraînement ; les hyperparamètres affichés sont ceux lus dans les modèles livrés.
- **Provenance des colonnes** (Google Trends, qualité de l'air, indice grippal, passages aux urgences) : aucune source citée par le projet.
- **Absence de 2024 dans l'entraînement** : très probable (année moyenne 2021,9 du scaler), non démontrable.
- Le dépôt `industrialisation` : l'image `python:3.9` n'a pas été reconstruite.

## Médias produits

| Fichier | Contenu |
|---|---|
| `docs/index.html` | Vitrine GitHub Pages (clair/sombre, mobile vérifié à 375 px sans défilement horizontal) |
| `docs/video/predictira.mp4` + `docs/video/poster.png` | Vidéo narrée (voix Windows Hortense, 1920×1080, H.264 + AAC) : **1 min 59 s (118,9 s), 11,6 Mo** ; générée par `scripts/promo_video.py` |
| `docs/architecture.drawio` | 4 pages : architecture applicative, données/modèle/évaluation, déploiement Kubernetes, audit |
| `docs/img/architecture-1..4.png` | Exports PNG des 4 pages (draw.io CLI, échelle 1,5) |
| `docs/img/cap_prediction.png` | Capture réelle : Rhône 2024-S05, 1 363,57 prédits, 1 738 observés |
| `docs/img/cap_swagger.png`, `docs/img/cap_accueil.png` | Swagger de l'API v2, page d'accueil d'origine |
| `docs/img/eval_series.png`, `docs/img/eval_scatter.png` | Séries 2024 observé / modèle / persistance (69, 38, 15) ; nuage observé–prédit |

Scripts : `scripts/evaluate.py`, `scripts/bench_http.py`, `scripts/export_models.py`, `scripts/build_drawio.py`, `scripts/promo_video.py`.

## Extraits de code exacts

`predictira/data.py` — la correction du défaut n° 1 :

```python
def load_dataset(root: str | Path) -> pd.DataFrame:
    df = pd.read_csv(Path(root) / "df_Test_Indust.csv")
    # week_cos seul est ambigu : cos(2π·w/52) = cos(2π·(52-w)/52), donc S30 et S22 sont
    # indiscernables. Le fichier est trié chronologiquement par département (2024-S01→S39,
    # puis la ligne 2023-S52) : on reconstruit la semaine par le rang, puis on vérifie le cosinus.
    df["week"] = df.groupby(["dept", "year"]).cumcount() + 1
    df.loc[df["year"] == 2023, "week"] = 52
    expected = np.cos(2 * np.pi * df["week"] / 52)
    if not np.allclose(expected, df["week_cos"], atol=1e-9):
        raise ValueError("Ordre des semaines incohérent avec week_cos")
    return df
```

`predictira/safe_load.py` — lecture des pickles hérités sous liste blanche :

```python
class _AllowListUnpickler(numpy_pickle.NumpyUnpickler):
    def find_class(self, module, name):
        if (module, name) not in ALLOWED:
            raise pickle.UnpicklingError(f"classe interdite dans le pickle : {module}.{name}")
        return super().find_class(module, name)
```

`predictira/api.py` — l'endpoint de prédiction validé :

```python
@api.post("/predict", response_model=Prediction)
def predict(features: Features) -> Prediction:
    value = float(model.predict_frame(pd.DataFrame([features.model_dump()]))[0])
    return Prediction(prediction=round(value, 1), modele=MODEL_NAME)
```

Code d'origine (branche `main`, `app.py`) — le filtre défectueux :

```python
def get_data(year, week, dept):
    week_cos = cos(2 * pi * week / 52)
    print (week_cos)
    # Filtrer le DataFrame
    filtered_df = df[(df["year"] == year) & (df["week_cos"] == week_cos) & (df["dept"] == dept)]
```

## Limites

- Nowcasting : le modèle estime la semaine courante à partir de ses propres signaux ; ce n'est pas une prévision à J+7.
- Seul, il ne bat pas la persistance S-1 sur 2024 ; la combinaison des deux est la piste d'amélioration.
- 11 départements d'Auvergne-Rhône-Alpes seulement ; le département est une variable numérique (31,5 % du gain) : aucune généralisation possible à d'autres départements.
- 39 semaines de test, dont 13 d'hiver : estimation de l'erreur hivernale fragile.
- Encodage de la semaine sans sinus : les semaines s et 52 − s sont indiscernables pour le modèle.

## Proposition de texte pour la fiche

- **Titre** : PredictIRA — estimer les passages aux urgences respiratoires
- **Lead** : Estimation hebdomadaire des passages aux urgences pour infections respiratoires aiguës, par département, à partir des
  recherches Google de symptômes, de la pollution, de la météo et de l'indice grippal. Projet d'équipe relancé en 2026 : mesuré
  sur 429 semaines de 2024, six défauts corrigés, API FastAPI validée, déployable sur Kubernetes.
- **KPIs** : `R² 0,926` (2024, hors entraînement) · `MAE 41` passages/semaine · `24` variables · `13` tests
- **Point fort recruteur** : comparaison honnête à une référence naïve (et la piste qu'elle ouvre), audit qui transforme un projet de formation en service fiable.
