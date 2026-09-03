from __future__ import annotations

from fastapi import FastAPI, HTTPException

from doux_planning.api.examples import ExampleNotFound, LegalContextNotFound, example_payload

app = FastAPI(title="doux-planning", version="0.1.0")


@app.get("/v1/examples/{example_id}")
def get_example(example_id: str) -> dict:
    try:
        return example_payload(example_id)
    except ExampleNotFound:
        raise HTTPException(status_code=404, detail=f"unknown example: {example_id}") from None
    except LegalContextNotFound as exc:
        raise HTTPException(status_code=500, detail=f"missing legal context: {exc}") from None
