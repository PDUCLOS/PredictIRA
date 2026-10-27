# ===========================================================================
# PredictIRA — API FastAPI (/api, /health) + interface Flask (/) dans une image
#
#   docker build -t predictira:2.0.0 .
#   docker run -p 18765:8000 predictira:2.0.0   →  http://127.0.0.1:18765/
#
# Le modèle est embarqué au format texte LightGBM + JSON (aucun pickle chargé à
# l'exécution) : l'image n'a besoin ni de scikit-learn ni de joblib.
# ===========================================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# LightGBM a besoin de la bibliothèque OpenMP (libgomp) ; curl sert au HEALTHCHECK.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY predictira ./predictira
COPY models ./models
COPY templates ./templates
COPY static ./static
COPY app.py df_Test_Indust.csv favicon.ico ./

RUN useradd --uid 10001 --no-create-home app
USER 10001

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# Nombre de workers : variable WEB_CONCURRENCY (lue par uvicorn, fixée par la ConfigMap Kubernetes)
CMD ["uvicorn", "predictira.api:app", "--host", "0.0.0.0", "--port", "8000"]
