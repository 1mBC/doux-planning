## 1. Image and Railway builder

- [x] 1.1 Rewrite the Dockerfile as multi-stage (Node `web/` build → copy `dist` into the Python image), allow `web/` in `.dockerignore`, listen on `$PORT` (default 8000), and run `alembic upgrade head` only when `DATABASE_URL` is set. Verify `docker compose` file ports are unchanged
- [x] 1.2 Add `railway.toml` with Dockerfile builder only, and verify there is no GitHub Action and no Railway HTTP client in tests

## 2. API same-origin and URL normalize

- [x] 2.1 Serve `web/dist` + SPA fallback without capturing `/v1`, and verify TestClient `GET /v1/examples/saint-cloud` is 200 / 92 when `dist` is absent (no 500)
- [x] 2.2 Normalize `postgres://` to `postgresql+psycopg://` in `api/` (`database_url`), point Alembic at that helper, and verify a unit test on the rewritten URL. Dual-read without `DATABASE_URL` stays intact
- [x] 2.3 Add an optional TestClient `GET /planning` that expects `index.html` when `dist` exists (skip if absent). Run existing pytest green
