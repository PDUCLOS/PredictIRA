"""Vidéo promotionnelle (1080p) générée à partir des vraies captures du projet.

Chaîne : scènes HTML -> PNG 1920x1080 (Edge headless) -> narration française
(voix Windows Hortense, System.Speech) -> clips ffmpeg (zoom lent + fondus)
-> concaténation + fond sonore synthétisé (aucun fichier sous licence).

Adapté du générateur du projet LLMRAGlangchain. Tous les chiffres affichés ou prononcés
proviennent de docs/metrics.json (mesures du 2026-10-27).

Usage (Windows) :  python scripts/promo_video.py
Sortie : docs/video/predictira.mp4 (+ affiche docs/video/poster.png)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"
OUT = ROOT / "docs" / "video"
WORK = ROOT / "build" / "promo"  # intermédiaires, ignorés par git
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
_FF_DIR = (Path.home() / "AppData/Local/Microsoft/WinGet/Packages/"
           "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.2-full_build/bin")
FFMPEG = shutil.which("ffmpeg") or str(_FF_DIR / "ffmpeg.exe")
FFPROBE = shutil.which("ffprobe") or str(_FF_DIR / "ffprobe.exe")
FPS = 30
PAD_S = 0.9  # respiration après chaque phrase

CSS = """
:root { --navy:#0b2a2c; --ink:#e6f2f1; --muted:#9fbcbc; --accent:#5eead4; --good:#5cc78f; --warn:#fdba74; }
* { box-sizing:border-box; margin:0; }
html,body { width:1920px; height:1080px; overflow:hidden; background:var(--navy); color:var(--ink);
  font-family:"Source Sans 3",system-ui,sans-serif; }
.stage { width:1920px; height:1080px; padding:110px 140px; display:grid; align-content:center; gap:34px;
  background: radial-gradient(1200px 700px at 85% 15%, #135a57 0%, transparent 60%), var(--navy); }
.eyebrow { font:500 26px "JetBrains Mono",monospace; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); }
h1 { font:700 104px/1.02 "Source Serif 4",sans-serif; letter-spacing:-.015em; max-width:1500px; }
h1 em { font-style:normal; color:var(--warn); }
h2 { font:600 72px/1.08 "Source Serif 4",sans-serif; max-width:1500px; }
p.sub { font-size:38px; line-height:1.45; color:var(--muted); max-width:1450px; }
ul { list-style:none; padding:0; display:grid; gap:26px; }
li { font-size:44px; line-height:1.3; padding-left:56px; position:relative; }
li::before { content:""; position:absolute; left:0; top:22px; width:28px; height:4px; background:var(--accent); }
.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:2px; background:rgba(255,255,255,.14); border-radius:10px; overflow:hidden; }
.kpi { background:var(--navy); padding:40px 30px; display:grid; gap:10px; }
.kpi b { font:700 80px "Source Serif 4",sans-serif; color:#fff; }
.kpi span { font-size:28px; color:var(--muted); line-height:1.3; }
.shotstage { width:1920px; height:1080px; display:grid; grid-template-rows:1fr auto; background:var(--navy); }
.frame { display:grid; place-items:center; padding:48px 60px 26px; overflow:hidden; }
.frame img { max-width:100%; max-height:860px; border-radius:12px; box-shadow:0 30px 80px rgba(0,0,0,.5); border:1px solid rgba(255,255,255,.14); }
.frame.light img { background:#fff; padding:14px; }
.band { padding:26px 60px 40px; display:flex; gap:30px; align-items:baseline; }
.band .tag { font:500 24px "JetBrains Mono",monospace; color:var(--accent); letter-spacing:.12em; text-transform:uppercase; white-space:nowrap; }
.band .cap { font:500 40px/1.3 "Source Sans 3",sans-serif; }
.chips { display:flex; flex-wrap:wrap; gap:16px; }
.chip { font:500 30px "JetBrains Mono",monospace; border:1px solid rgba(255,255,255,.3); border-radius:6px; padding:10px 18px; }
.url { font:500 40px "JetBrains Mono",monospace; color:var(--accent); }
.vs { display:grid; grid-template-columns:repeat(3,1fr); gap:28px; }
.vs div { border:1px solid rgba(255,255,255,.2); border-radius:12px; padding:34px; display:grid; gap:12px; }
.vs div.win { border-color:var(--accent); background:rgba(94,234,212,.08); }
.vs b { font:700 76px "Source Serif 4",serif; }
.vs span { font-size:30px; color:var(--muted); line-height:1.3; }
"""
FONTS = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600;8..60,700'
    '&family=Source+Sans+3:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap">'
)


def page(body: str) -> str:
    return f'<!doctype html><html lang="fr"><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head><body>{body}</body></html>'


def card(eyebrow: str, title: str, sub: str = "", extra: str = "") -> str:
    sub_html = f'<p class="sub">{sub}</p>' if sub else ""
    return page(f'<div class="stage"><span class="eyebrow">{eyebrow}</span><h1>{title}</h1>{sub_html}{extra}</div>')


def shot(image: str, tag: str, caption: str, light: bool = False) -> str:
    src = (IMG / image).as_uri()
    cls = "frame light" if light else "frame"
    return page(
        f'<div class="shotstage"><div class="{cls}"><img src="{src}"></div>'
        f'<div class="band"><span class="tag">{escape(tag)}</span><span class="cap">{caption}</span></div></div>'
    )


KPIS = (
    '<div class="kpis">'
    + "".join(
        f'<div class="kpi"><b>{v}</b><span>{t}</span></div>'
        for v, t in [
            ("R² 0,926", "429 semaines de 2024 jamais vues"),
            ("MAE 41", "passages par semaine (moyenne : 257)"),
            ("0,43 ms", "par prédiction, sur CPU"),
            ("13", "tests automatisés verts"),
        ]
    )
    + "</div>"
)
VS = (
    '<div class="vs">'
    '<div><b>41,2</b><span>MAE du modèle LightGBM seul</span></div>'
    '<div><b>39,5</b><span>MAE de la persistance : « comme la semaine dernière »</span></div>'
    '<div class="win"><b>30,6</b><span>MAE de la moyenne des deux, sans aucun réglage (exploratoire)</span></div>'
    "</div>"
)

# (identifiant, html, narration, zoom final)
SCENES = [
    ("01-titre", card("PredictIRA · santé publique", "Anticiper la charge des <em>urgences respiratoires</em>.",
                      "Une estimation par département et par semaine."),
     "Chaque hiver, les infections respiratoires saturent les urgences. PredictIRA estime, département par département, "
     "combien de patients vont arriver cette semaine.", 1.04),
    ("02-signaux", card("Les signaux", "Ce que les gens cherchent, ce qu'ils respirent.",
                        extra="<ul><li>Recherches Google : toux, frissons, essoufflement…</li>"
                              "<li>Qualité de l'air : dioxyde d'azote, ozone, particules fines</li>"
                              "<li>Météo et indice grippal de la semaine</li></ul>"),
     "Le modèle combine les recherches Google de symptômes, la qualité de l'air, la météo et l'indice grippal. "
     "Vingt-quatre variables, un modèle LightGBM.", 1.03),
    ("03-demo", shot("cap_prediction.png", "Démo réelle", "Rhône, semaine 5 de 2024 : 1 364 prédits, 1 738 observés.", light=True),
     "On choisit un département et une semaine : le formulaire se remplit, et la prédiction s'affiche "
     "à côté de la valeur observée. Ici, un pic d'hiver dans le Rhône, sous-estimé. On le montre tel quel.", 1.10),
    ("04-chiffres", card("Mesuré sur 2024", "Les chiffres, sur des semaines jamais vues.", extra=KPIS),
     "Testé sur les trente-neuf premières semaines de 2024, dans onze départements, "
     "le modèle explique plus de quatre-vingt-douze pour cent de la variabilité, en moins d'une milliseconde par prédiction.", 1.03),
    ("05-honnete", card("Lecture honnête", "Battre la référence naïve ?", extra=VS),
     "Mais il faut battre la référence naïve : comme la semaine dernière. Seul, le modèle ne la bat pas. "
     "En revanche, la moyenne des deux réduit l'erreur d'un quart. C'est la piste pour la suite.", 1.03),
    ("06-series", shot("eval_series.png", "Évaluation", "Observé, modèle et persistance : Rhône, Isère, Cantal.", light=True),
     "Sur les courbes, le modèle anticipe mieux la reprise de septembre, mais réagit trop sur les petits départements.", 1.08),
    ("07-audit", shot("architecture-4.png", "Audit", "Six défauts reproduits : corrigés ou documentés.", light=True),
     "Relancer le projet a révélé six défauts. Le plus subtil : pour onze semaines sur trente-neuf, "
     "le préremplissage ne trouvait rien, ou chargeait une autre semaine. Tout est corrigé et testé.", 1.06),
    ("08-api", shot("architecture-1.png", "Architecture", "Interface Flask et API FastAPI validée, dans un seul conteneur.", light=True),
     "L'interface d'origine et une nouvelle API validée partagent un conteneur. Le modèle est chargé depuis un format texte, "
     "sans risque d'exécution de code.", 1.10),
    ("09-k8s", shot("architecture-3.png", "Déploiement", "Kustomize : base, overlays local et cloud.", light=True),
     "Enfin, des manifestes Kubernetes : pods non root, mise à l'échelle automatique, et politique réseau sans sortie.", 1.10),
    ("10-fin", card("PredictIRA", "Le code, les mesures et les limites sont publics.",
                    extra='<p class="url">github.com/PDUCLOS/PredictIRA</p>'
                          '<p class="sub">Projet d\'équipe · reprise et industrialisation : Patrice Duclos</p>'),
     "PredictIRA. Le code, les mesures, et les limites, sont sur GitHub.", 1.04),
]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render_png(html: str, png: Path) -> None:
    src = png.with_suffix(".html")
    src.write_text(html, encoding="utf-8")
    run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
         f"--user-data-dir={WORK / 'edge-profile'}", "--window-size=1920,1080",
         "--virtual-time-budget=4000", f"--screenshot={png}", src.as_uri()])


def narrate(text: str, wav: Path) -> None:
    txt = wav.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$s.SelectVoice('Microsoft Hortense Desktop'); $s.Rate = 0;"
        f"$s.SetOutputToWaveFile('{wav}');"
        f"$s.Speak([IO.File]::ReadAllText('{txt}', [Text.Encoding]::UTF8)); $s.Dispose()"
    )
    run(["powershell", "-NoProfile", "-Command", ps])


def duration(path: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(json.loads(out)["format"]["duration"])


def encoder() -> list[str]:
        # GPU partagé avec d'autres travaux : encodage CPU, réglé pour rester sous 15 Mo
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "26", "-tune", "stillimage"]


def clip(png: Path, wav: Path, zoom: float, mp4: Path) -> float:
    dur = duration(wav) + PAD_S
    frames = int(dur * FPS)
    step = (zoom - 1.0) / frames
    vf = (
        f"[0:v]scale=3840:2160,zoompan=z='min(1+{step:.6f}*on,{zoom})':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={FPS},"
        f"fade=t=in:st=0:d=0.45,fade=t=out:st={dur - 0.45:.2f}:d=0.45,format=yuv420p[v];"
        f"[1:a]adelay=350|350,apad,atrim=0:{dur:.2f},aformat=sample_rates=48000:channel_layouts=stereo[a]"
    )
    run([FFMPEG, "-y", "-loop", "1", "-i", str(png), "-i", str(wav), "-filter_complex", vf,
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.2f}", *encoder(), "-c:a", "aac", "-b:a", "128k", str(mp4)])
    return dur


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    clips, total = [], 0.0
    for name, html, text, zoom in SCENES:
        png, wav, mp4 = WORK / f"{name}.png", WORK / f"{name}.wav", WORK / f"{name}.mp4"
        render_png(html, png)
        narrate(text, wav)
        total += clip(png, wav, zoom, mp4)
        clips.append(mp4)
        print(f"  {name}: {total:5.1f} s")

    concat = WORK / "concat.txt"
    concat.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    joined = WORK / "joined.mp4"
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(joined)])

    # Nappe sonore synthétisée (accord de quinte, battement lent) mixée sous la voix.
    pad = (
        f"aevalsrc='0.05*sin(2*PI*110*t)*(0.6+0.4*sin(2*PI*0.08*t))+0.035*sin(2*PI*164.81*t)"
        f"+0.03*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.05*t+1))+0.02*sin(2*PI*329.63*t)':"
        f"s=48000:d={total:.2f},afade=t=in:d=2,afade=t=out:st={total - 3:.2f}:d=3,"
        f"lowpass=f=900,aformat=channel_layouts=stereo,volume=0.55[pad]"
    )
    final = OUT / "predictira.mp4"
    run([FFMPEG, "-y", "-i", str(joined), "-filter_complex",
         f"{pad};[0:a][pad]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-16:TP=-1.5[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", str(final)])
    shutil.copy(WORK / "01-titre.png", OUT / "poster.png")
    print(f"Vidéo : {final} ({total:.1f} s, {final.stat().st_size / 1e6:.1f} Mo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
