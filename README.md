# Doux Planning

Moteur de planning de restaurant : cycle de 14 jours (salle / cuisine), postes à niveaux, contraintes légales et souhaits de bien-être.

## Rapport exemple (salle)

Le cycle généré à partir du classeur *Exemple de restau* est en HTML :

**[Ouvrir le planning 14 jours](https://1mbc.github.io/doux-planning/)**

## Moteur (Python 3.12)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## UI lecture seule (exemple Saint-Cloud)

Deux processus, sans `DATABASE_URL` (snapshot fichiers) :

```bash
# API — GET /v1/examples/saint-cloud
source .venv/bin/activate
uvicorn doux_planning.api.app:app --reload
```

```bash
# Client React (proxy /v1 → http://127.0.0.1:8000)
cd web
npm install
npm run dev
```

Ouvrir [http://127.0.0.1:5173/](http://127.0.0.1:5173/). Écran français, lecture seule : grille 14 jours, warnings moteur, stats du JSON, tableaux légal et souhaits. Une seule route HTTP.
