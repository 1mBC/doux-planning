from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response

from doux_planning.api.examples import ExampleNotFound, LegalContextNotFound, example_payload
from doux_planning.planning import EmptyHistoryError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.environ.get("DATABASE_URL"):
        from doux_planning.api.seed import seed_from_files

        seed_from_files()
    yield


app = FastAPI(title="doux-planning", version="0.1.0", lifespan=lifespan)


@app.post("/v1/auth/register", status_code=201)
def auth_register(body: dict[str, Any]) -> dict:
    from doux_planning.api.auth import register

    return register(body)


@app.post("/v1/auth/login")
def auth_login(body: dict[str, Any]) -> dict:
    from doux_planning.api.auth import login

    return login(body)


@app.post("/v1/auth/logout", status_code=204)
def auth_logout(authorization: str | None = Header(default=None)) -> Response:
    from doux_planning.api.auth import logout

    logout(authorization)
    return Response(status_code=204)


@app.get("/v1/me")
def auth_me(authorization: str | None = Header(default=None)) -> dict:
    from doux_planning.api.auth import me

    return me(authorization)


@app.get("/v1/invites/{company_code}")
def auth_invites(company_code: str) -> dict:
    from doux_planning.api.auth import list_invites

    return list_invites(company_code)


@app.post("/v1/staff/{employee_id}/invite-token")
def auth_rotate_invite_token(
    employee_id: str, authorization: str | None = Header(default=None)
) -> dict:
    from doux_planning.api.auth import rotate_invite_token

    return rotate_invite_token(employee_id, authorization)


@app.get("/v1/context")
def get_context(authorization: str | None = Header(default=None)) -> dict:
    from doux_planning.api.context import get_context as read_context

    return read_context(authorization)


@app.patch("/v1/context")
def patch_context(
    body: dict[str, Any], authorization: str | None = Header(default=None)
) -> dict:
    from doux_planning.api.context import patch_context as write_context

    return write_context(authorization, body)


@app.get("/v1/examples/{example_id}")
def get_example(example_id: str) -> dict:
    try:
        return example_payload(example_id)
    except ExampleNotFound:
        raise HTTPException(status_code=404, detail=f"unknown example: {example_id}") from None
    except LegalContextNotFound as exc:
        raise HTTPException(status_code=500, detail=f"missing legal context: {exc}") from None


@app.post("/v1/sandbox/enter")
def sandbox_enter() -> dict:
    from doux_planning.api.sandbox import enter_sandbox_state

    return enter_sandbox_state()


@app.get("/v1/sandbox")
def sandbox_get() -> dict:
    from doux_planning.api.sandbox import current_sandbox_state

    try:
        return current_sandbox_state()
    except LookupError:
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None


@app.post("/v1/sandbox/preview")
def sandbox_preview(body: dict[str, Any]) -> dict:
    from doux_planning.api.sandbox import preview
    from doux_planning.planning import IdentityRetuneError, OccupiedSlotError

    try:
        return preview(body)
    except KeyError:
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None
    except RuntimeError:
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None
    except IdentityRetuneError:
        raise HTTPException(status_code=400, detail="Ces horaires sont déjà ceux du créneau.") from None
    except OccupiedSlotError:
        raise HTTPException(status_code=409, detail="Cette case est déjà occupée.") from None
    except ValueError as exc:
        message = str(exc)
        if "not in the sandbox" in message or "missing shift" in message:
            raise HTTPException(status_code=404, detail="Ce créneau n'est pas dans le brouillon.") from None
        if "unknown gesture" in message:
            raise HTTPException(status_code=400, detail="Geste inconnu.") from None
        if "min_shift_hours" in message:
            raise HTTPException(status_code=400, detail="La durée est inférieure au minimum du salarié.") from None
        if "15-minute grid" in message:
            raise HTTPException(status_code=400, detail="Les horaires doivent être sur la grille de 15 minutes.") from None
        if "closed" in message.lower():
            raise HTTPException(status_code=400, detail="Ce service est fermé.") from None
        raise HTTPException(status_code=400, detail="Champs manquants pour ce geste.") from None


@app.post("/v1/sandbox/commit")
def sandbox_commit(body: dict[str, Any]) -> dict:
    from doux_planning.api.sandbox import commit
    from doux_planning.planning import IdentityRetuneError, OccupiedSlotError

    try:
        return commit(body)
    except LookupError as exc:
        if str(exc) == "no proposal":
            raise HTTPException(status_code=400, detail="Proposition introuvable.") from None
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None
    except (RuntimeError, KeyError):
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None
    except IdentityRetuneError:
        raise HTTPException(status_code=400, detail="Ces horaires sont déjà ceux du créneau.") from None
    except OccupiedSlotError:
        raise HTTPException(status_code=409, detail="Cette case est déjà occupée.") from None
    except ValueError as exc:
        message = str(exc)
        if "not in the sandbox" in message or "missing shift" in message:
            raise HTTPException(status_code=404, detail="Ce créneau n'est pas dans le brouillon.") from None
        if "unknown gesture" in message:
            raise HTTPException(status_code=400, detail="Geste inconnu.") from None
        if "min_shift_hours" in message:
            raise HTTPException(status_code=400, detail="La durée est inférieure au minimum du salarié.") from None
        if "15-minute grid" in message:
            raise HTTPException(status_code=400, detail="Les horaires doivent être sur la grille de 15 minutes.") from None
        if "closed" in message.lower():
            raise HTTPException(status_code=400, detail="Ce service est fermé.") from None
        raise HTTPException(status_code=400, detail="Champs manquants pour ce geste.") from None


@app.post("/v1/sandbox/undo")
def sandbox_undo() -> dict:
    from doux_planning.api.sandbox import undo

    try:
        return undo()
    except EmptyHistoryError:
        raise HTTPException(status_code=409, detail="Aucune modification à annuler.") from None
    except (LookupError, RuntimeError, KeyError):
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None


@app.post("/v1/sandbox/discard")
def sandbox_discard() -> dict:
    from doux_planning.api.sandbox import discard_sandbox_state

    try:
        return discard_sandbox_state()
    except LookupError:
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None
    except (RuntimeError, KeyError):
        raise HTTPException(status_code=404, detail="Aucun bac à sable n'est ouvert.") from None
