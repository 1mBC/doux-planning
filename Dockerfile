FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY data /app/data
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn doux_planning.api.app:app --host 0.0.0.0 --port 8000"]
