# Doux Planning

Moteur de planning restaurant (cycle 14 jours, salle / cuisine).

**[Planning exemple](https://1mbc.github.io/doux-planning/)**

## Chez toi (2 terminaux)

Prérequis : Docker Desktop (Postgres), Python 3.12 + `uv`, Node 20+.

```bash
# une fois
docker compose up -d db
uv sync --extra dev
uv run alembic upgrade head
cd web && npm install && cd ..
```

```bash
# terminal 1 — API (127.0.0.1:8000)
export DATABASE_URL=postgresql+psycopg://doux:doux@127.0.0.1:5432/doux_planning
uv run uvicorn doux_planning.api.app:app --reload --host 127.0.0.1 --port 8000
```

```bash
# terminal 2 — front (127.0.0.1:5173, proxy /v1 → API)
cd web && npm run dev
```

Ouvre [http://127.0.0.1:5173/](http://127.0.0.1:5173/).

Sans Postgres / sans `DATABASE_URL` : login → **503** `Base indisponible.`  
L’exemple seul : [http://127.0.0.1:5173/exemple](http://127.0.0.1:5173/exemple) (API sans `DATABASE_URL` OK).

Raccourci tout-en-un (background) : `./scripts/dev` — stop : `./scripts/dev stop`.

## Tests

```bash
uv run pytest
```
