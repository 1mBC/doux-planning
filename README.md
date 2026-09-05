# Doux Planning

Moteur de planning de restaurant : cycle de 14 jours (salle / cuisine), postes à niveaux, contraintes légales et souhaits de bien-être.

## Rapport exemple (salle)

Le cycle généré à partir du classeur *Exemple de restau* est en HTML :

**[Ouvrir le planning 14 jours](https://1mbc.github.io/doux-planning/)**

## Prérequis

- Python 3.12 + [`uv`](https://docs.astral.sh/uv/) (recommandé) ou un venv
- Node.js 20+ (client Vite)
- Docker (Postgres via `docker-compose.yml`)

## Lancer en local (recommandé)

Une commande démarre Postgres, les migrations, l’API et le front :

```bash
./scripts/dev
```

Puis ouvre [http://127.0.0.1:5173/](http://127.0.0.1:5173/).

- **Connexion / inscription / mon restaurant / planning live** → besoin de Postgres (`DATABASE_URL`).
- **Voir l’exemple** ([/exemple](http://127.0.0.1:5173/exemple)) → marche aussi sans base (snapshot fichiers).

Stop API + Vite : `./scripts/dev stop`  
Logs : `/tmp/doux-planning-dev/api.log` et `web.log`

### Ce qui cassait en « HTTP 500 »

L’UI ouvre sur **Connexion**. Sans Postgres :

| Situation | Symptôme |
|---|---|
| Pas de `DATABASE_URL` | Auth / context → **503** `Base indisponible.` |
| `DATABASE_URL` pointant vers une base éteinte | L’API **refuse de démarrer** (seed au boot) |

Il faut donc Postgres **avant** l’API. `./scripts/dev` le gère.

## Détail manuel (si tu préfères 3 terminaux)

```bash
# 1) Postgres
docker compose up -d db

# 2) API
export DATABASE_URL=postgresql+psycopg://doux:doux@127.0.0.1:5432/doux_planning
uv sync --extra dev   # une fois
uv run alembic upgrade head
uv run uvicorn doux_planning.api.app:app --reload --host 127.0.0.1 --port 8000

# 3) Front (proxy /v1 → :8000)
cd web && npm install && npm run dev
```

Stack Docker API+DB (sans Vite) : `docker compose up --build`.

## Tests

```bash
uv run pytest
# tests Postgres (optionnel) :
DATABASE_URL=postgresql+psycopg://doux:doux@127.0.0.1:5432/doux_planning uv run pytest
```

## UI lecture seule sans base

Sans `DATABASE_URL`, l’exemple public et le sandbox fichier restent dispo :

```bash
uv run uvicorn doux_planning.api.app:app --reload
cd web && npm run dev
```

Ouvre [http://127.0.0.1:5173/exemple](http://127.0.0.1:5173/exemple) (pas `/` : la home demande une session).
