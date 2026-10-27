"""Génère docs/architecture.drawio (4 pages) — mise en page en grille, flèches orthogonales.

    python scripts/build_drawio.py
    drawio -x -f png -p <n> -o docs/img/architecture-<n>.png docs/architecture.drawio
"""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parents[1] / "docs" / "architecture.drawio"
ATTR = {'"': "&quot;", "\n": "&#xa;"}

C = {  # remplissage, contour
    "src": ("#dae8fc", "#6c8ebf"), "proc": ("#fff2cc", "#d6b656"), "ml": ("#e1d5e7", "#9673a6"),
    "serve": ("#d5e8d4", "#82b366"), "user": ("#ffffff", "#666666"), "warn": ("#f8cecc", "#b85450"),
    "k8s": ("#ffe6cc", "#d79b00"), "zone": ("#f5f5f5", "#999999"),
}


class Page:
    def __init__(self, pid: str, name: str, w=1400, h=800):
        self.pid, self.name, self.w, self.h, self.cells, self.n = pid, name, w, h, [], 0

    def _id(self):
        self.n += 1
        return f"{self.pid}-{self.n}"

    def _vertex(self, x, y, w, h, text, style):
        i = self._id()
        value = escape(text, ATTR).replace("&#xa;", "&lt;br&gt;")
        self.cells.append(f'<mxCell id="{i}" value="{value}" style="{style}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    def box(self, x, y, w, h, text, kind="user", bold=False, size=12, align="center"):
        fill, stroke = C[kind]
        st = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={size};"
              f"align={align};verticalAlign=middle;spacing=6;" + ("fontStyle=1;" if bold else ""))
        return self._vertex(x, y, w, h, text, st)

    def zone(self, x, y, w, h, title, kind="zone"):
        fill, stroke = C[kind]
        st = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};dashed=1;fontSize=13;"
              "fontStyle=1;verticalAlign=top;align=left;spacingLeft=10;spacingTop=4;arcSize=4;")
        return self._vertex(x, y, w, h, title, st)

    def text(self, x, y, w, h, text, size=12, bold=False, color="#333333", align="left"):
        st = (f"text;html=1;whiteSpace=wrap;fontSize={size};align={align};verticalAlign=middle;fontColor={color};"
              + ("fontStyle=1;" if bold else ""))
        return self._vertex(x, y, w, h, text, st)

    def edge(self, a, b, label="", dashed=False, exit_=None, entry=None):
        i = self._id()
        st = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor=#555555;"
              "fontSize=11;labelBackgroundColor=#ffffff;" + ("dashed=1;" if dashed else ""))
        if exit_:
            st += f"exitX={exit_[0]};exitY={exit_[1]};exitDx=0;exitDy=0;"
        if entry:
            st += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        self.cells.append(f'<mxCell id="{i}" value="{escape(label, ATTR)}" style="{st}" edge="1" parent="1" '
                          f'source="{a}" target="{b}"><mxGeometry relative="1" as="geometry"/></mxCell>')

    def xml(self):
        return (f'<diagram id="{self.pid}" name="{escape(self.name, ATTR)}"><mxGraphModel dx="1400" dy="800" grid="1" '
                f'gridSize="10" guides="1" page="1" pageWidth="{self.w}" pageHeight="{self.h}" background="#ffffff">'
                '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(self.cells)
                + "</root></mxGraphModel></diagram>")


def page_app():
    p = Page("app", "1. Architecture applicative", 1400, 600)
    p.text(40, 20, 1300, 30, "PredictIRA v2 — un conteneur, deux interfaces, un modèle sans pickle", 18, True)
    nav = p.box(40, 160, 170, 80, "Navigateur\n(personnel hospitalier,\nanalyste)")
    cli = p.box(40, 340, 170, 80, "Client HTTP / SI\n(JSON)")
    p.zone(260, 80, 720, 480, "Conteneur predictira:2.0.0 — uvicorn (FastAPI, ASGI)")
    flask = p.box(300, 145, 260, 110, "Interface Flask « / »\nformulaire prérempli\ndépartement × semaine\n(montée via a2wsgi)", "serve")
    api = p.box(300, 325, 260, 110, "API FastAPI « /api »\nPOST /predict · /predict/batch\nGET /donnees · /departements\nSwagger /api/docs", "serve")
    p.box(300, 480, 260, 50, "GET /health (sondes Kubernetes)", "serve")
    val = p.box(650, 175, 290, 100, "Validation Pydantic\n24 variables, bornes physiques\nchamp manquant / inconnu → 4xx", "proc")
    mdl = p.box(650, 380, 290, 100, "IRAModel\n(x − μ) / σ  puis  LightGBM\n100 arbres · 24 variables", "ml")
    art = p.box(1040, 365, 320, 130, "Artefacts versionnés\nmodels/lightgbm_ira_24var.txt\nmodels/scaler_24var.json\n(exportés des .pkl d'origine\nvia une liste blanche de classes)", "ml", size=11)
    data = p.box(1040, 135, 320, 130, "Jeu de démonstration\ndf_Test_Indust.csv\n11 départements Auvergne-Rhône-Alpes\n2024-S01 → S39 (+ 2023-S52)", "src", size=11)
    p.edge(nav, flask, "HTML")
    p.edge(cli, api, "JSON")
    p.edge(flask, val, "", exit_=(1, 0.45), entry=(0, 0.3))
    p.edge(api, val, "", exit_=(1, 0.25), entry=(0, 0.85))
    p.edge(val, mdl, "")
    p.edge(art, mdl, "chargés au démarrage")
    p.edge(data, flask, "préremplissage", exit_=(0.5, 0), entry=(0.5, 0))
    return p


def page_data():
    p = Page("data", "2. Données, modèle et évaluation", 1400, 720)
    p.text(40, 20, 1300, 30, "Du tableau hebdomadaire à une mesure honnête sur 2024", 18, True)
    srcs = [("Google Trends\n12 symptômes (SYM*)", "src"), ("Qualité de l'air\nCO, NO₂, O₃, PM2.5, SO₂, IQA", "src"),
            ("Météo\npression, T° max", "src"), ("Indice grippal\nde la semaine", "src"),
            ("Passages aux urgences IRA\n(cible nb_passage_IRA)", "warn")]
    ids = [p.box(40, 70 + i * 70, 240, 56, t, k, size=11) for i, (t, k) in enumerate(srcs)]
    tab = p.box(350, 180, 230, 110, "Table hebdomadaire\ndépartement × semaine\n+ week_cos = cos(2π·s/52)", "proc")
    for i in ids:
        p.edge(i, tab, "", entry=(0, 0.5))
    sc = p.box(650, 180, 190, 110, "StandardScaler\n(2 733 lignes\nd'entraînement)", "proc")
    lgbm = p.box(910, 180, 190, 110, "LightGBM\n100 arbres\nlr 0,06 · L1 = L2 = 2", "ml")
    pred = p.box(1170, 180, 190, 110, "Passages IRA\nestimés pour\nla semaine", "serve")
    p.edge(tab, sc, "")
    p.edge(sc, lgbm, "")
    p.edge(lgbm, pred, "")
    z = p.zone(40, 450, 1320, 240, "Évaluation (scripts/evaluate.py) — test 2024-S01 → S39, 11 départements, 429 semaines hors entraînement")
    p.box(80, 500, 280, 160, "LightGBM 24 variables\n(application Flask)\n\nMAE 41,2 · R² 0,926\nWAPE 16,1 %", "ml", bold=True)
    p.box(395, 500, 280, 160, "Référence : persistance S-1\n(valeur observée\nla semaine précédente)\n\nMAE 39,5 · R² 0,930", "proc")
    p.box(710, 500, 280, 160, "Moyenne 50/50\nmodèle + persistance\n(exploratoire, sans ajustement)\n\nMAE 30,6 · R² 0,962", "serve", bold=True)
    p.box(1025, 500, 300, 160, "Modèle « industrialisation »\n28 variables, sans département\n\nMAE 510 · biais +488\n→ non exploitable en l'état", "warn")
    p.edge(pred, z, "comparé à l'observé", exit_=(0.5, 1), entry=(0.955, 0))
    return p


def page_k8s():
    p = Page("k8s", "3. Déploiement Kubernetes", 1400, 640)
    p.text(40, 20, 1300, 30, "deploy/k8s — kustomize : base + overlays local / cloud (rendu validé par kubectl kustomize)", 18, True)
    u = p.box(40, 255, 140, 70, "Utilisateurs")
    ing = p.box(220, 240, 220, 100, "Ingress NGINX + TLS\n(overlay cloud)\nou NodePort 30765\n(overlay local)", "k8s", size=11)
    p.zone(480, 70, 880, 540, "Namespace predictira")
    svc = p.box(520, 255, 170, 70, "Service\npredictira-api :80", "k8s")
    pod1 = p.box(770, 130, 260, 100, "Pod API #1\nuvicorn · WEB_CONCURRENCY=2\nnon-root · FS en lecture seule", "serve", size=11)
    pod2 = p.box(770, 350, 260, 100, "Pod API #2\nsondes /health\nreadiness + liveness", "serve", size=11)
    cm = p.box(1110, 125, 220, 50, "ConfigMap\nWEB_CONCURRENCY", "proc", size=11)
    hpa = p.box(1110, 185, 220, 50, "HPA 2 → 6 répliques\n(CPU 70 %)", "proc", size=11)
    pdb = p.box(1110, 345, 220, 50, "PodDisruptionBudget\nminAvailable 1", "proc", size=11)
    np_ = p.box(1110, 405, 220, 50, "NetworkPolicy\nentrée :8000, sortie : aucune", "warn", size=11)
    p.box(520, 520, 810, 60, "Image predictira:2.0.0 — python:3.12-slim + libgomp1, modèle embarqué (≈ 550 Ko de texte LightGBM + JSON)", "ml", size=11)
    p.edge(u, ing, "HTTPS")
    p.edge(ing, svc, "")
    p.edge(svc, pod1, "", exit_=(1, 0.3), entry=(0, 0.5))
    p.edge(svc, pod2, "", exit_=(1, 0.7), entry=(0, 0.5))
    p.edge(cm, pod1, "", dashed=True, exit_=(0, 0.5), entry=(1, 0.2))
    p.edge(hpa, pod1, "", dashed=True, exit_=(0, 0.5), entry=(1, 0.8))
    p.edge(pdb, pod2, "", dashed=True, exit_=(0, 0.5), entry=(1, 0.2))
    p.edge(np_, pod2, "", dashed=True, exit_=(0, 0.5), entry=(1, 0.8))
    return p


def page_audit():
    p = Page("audit", "4. Audit 2026 : constats et corrections", 1400, 720)
    p.text(40, 20, 1300, 30, "Ce que la remise en route a révélé — et ce qui a été corrigé", 18, True)
    rows = [
        ("Préremplissage par égalité exacte du cosinus de la semaine : 9 semaines sur 39 sans résultat (arrondi flottant), "
         "S27 et S29 chargeaient S25 et S23 (même cosinus pour s et 52 − s)",
         "Semaine reconstruite par le rang puis contrôlée par le cosinus ; un test rejoue l'ancien filtre sur les 39 semaines"),
        ("Champ caché week_cos rempli avec le numéro brut de la semaine (ex. 10) quand le préremplissage échouait",
         "Cosinus calculé dans le navigateur ; erreur 404 affichée à l'utilisateur"),
        ("Département 63 proposé dans l'interface mais absent des données",
         "Liste des départements générée à partir des données"),
        ("Champ vide → NaN silencieux : une prédiction était rendue quand même",
         "Validation Pydantic : erreurs 400 / 422 explicites"),
        ("Client HTML du dépôt « industrialisation » : 5 variables inconnues du modèle, 5 manquantes ; LightGBM prédit par position",
         "Constat reproduit et documenté ; l'API v2 refuse tout champ inconnu"),
        ("Modèles livrés en pickle : exécution de code possible au chargement",
         "Export LightGBM texte + JSON ; lecture des pickles sous liste blanche"),
    ]
    p.text(40, 65, 640, 30, "Constat (mesuré ou reproduit)", 14, True, "#b85450")
    p.text(760, 65, 600, 30, "Correction livrée", 14, True, "#2d7d46")
    for i, (a, b) in enumerate(rows):
        y = 105 + i * 100
        ia = p.box(40, y, 640, 80, a, "warn", size=12, align="left")
        ib = p.box(760, y, 600, 80, b, "serve", size=12, align="left")
        p.edge(ia, ib, "")
    return p


pages = [page_app(), page_data(), page_k8s(), page_audit()]
OUT.write_text('<mxfile host="drawio" version="24.7.17">' + "".join(pg.xml() for pg in pages) + "</mxfile>",
               encoding="utf-8")
print("écrit", OUT)
