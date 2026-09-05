FROM node:22-bookworm-slim AS web

WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY data /app/data
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY --from=web /web/dist /app/web/dist

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sh", "-c", "if [ -n \"$DATABASE_URL\" ]; then alembic upgrade head; fi; exec uvicorn doux_planning.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
