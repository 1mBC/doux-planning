# Recette Railway (même origine)

Une URL HTTPS qui suit **`master`**. Pas de preview par branche d’ownership.

## Plateforme

**Railway** : un service web (Dockerfile existant) + plugin **Postgres 16**.  
`DATABASE_URL` injecté par le plugin. Auto-deploy GitHub → `master` (clic Bastien, pas de GitHub Action).

Render écarté : free web **dort** (premier clic après un landing = « c’est down ? »). Vercel écarté : pas OR-Tools / generate 30 s / Alembic.

## Topologie

```
navigateur  →  https://<railway-domain>/
                 ├── /v1/*     FastAPI (auth, context, generate, live, me/planning, exemple, sandbox joujou)
                 └── /*        SPA (web/dist) + fallback index.html (/planning, /login, …)
```

Même origine : le front continue d’appeler `/v1` (déjà le cas). Pas de CORS. Pas de second service front.

Local inchangé : Compose Postgres + uvicorn hôte + Vite proxy. Ne pas imposer le port `18080` (conf Bastien).

## Env

| Variable | Où | Notes |
|---|---|---|
| `DATABASE_URL` | Railway (plugin) | SQLAlchemy `postgresql+psycopg://…` ; adapter si Railway donne `postgres://` |
| `PORT` | Railway | uvicorn écoute `$PORT` (défaut 8000 en local / image) |

Pas d’autre secret en v1 (auth actuelle = email/mdp en base).

## Image

Multi-stage : `npm run build` dans `web/` → copier `dist` dans l’image Python.  
`CMD` : `alembic upgrade head` puis uvicorn `0.0.0.0:$PORT`.  
Si `dist` absent (dev API seule) : les routes `/v1` restent OK, pas de 500.

## Ce que Bastien fait à la main (une fois)

1. Compte Railway, projet lié au repo `1mBC/doux-planning`, branche **`master`**.
2. Plugin Postgres. Vérifier `DATABASE_URL` sur le service web.
3. Generate domain. Premier deploy après merge du slice Infra.

Pas de token à coller dans le repo. Pas de CI GitHub obligatoire.
