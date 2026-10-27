"""Latence HTTP de bout en bout de POST /api/predict (serveur uvicorn local déjà lancé)."""
import json
import statistics
import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:18765"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 300


def call(path, body=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


row = call("/api/donnees/69/2024/5")
feats = {k: v for k, v in row.items() if k not in ("nb_passage_IRA", "week") and k in call("/api/openapi.json")["components"]["schemas"]["Features"]["properties"]}
for _ in range(20):
    call("/api/predict", feats)
t = []
for _ in range(N):
    t0 = time.perf_counter()
    out = call("/api/predict", feats)
    t.append((time.perf_counter() - t0) * 1000)
t.sort()
print(json.dumps({"requetes": N, "p50_ms": round(statistics.median(t), 2), "p95_ms": round(t[int(.95 * N)], 2),
                  "debit_seq_req_s": round(N / (sum(t) / 1000), 1), "exemple": out,
                  "observe": row["nb_passage_IRA"]}, ensure_ascii=False))
