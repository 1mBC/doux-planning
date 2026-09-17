# Brief — coller dans le chat **Infra**

Le tech lead : **annuler batch banc** — route pour annuler les jobs en attente. Relis **`contracts/domain/bench.md`** section POST cancel batch.

`git pull origin master` ; branche **depuis `master`**.

**Process** : tâches + pytest vert → **commit + push toi-même**. Titre : `feat(api): POST cancel bench batch`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `src/doux_planning/` hors `api/`, `contracts/`.

## Comportement

### Route

`POST /v1/admin/bench/batches/{batch_id}/cancel`

Bearer admin. Passe les jobs `queued` du batch → statut `cancelled`. Les jobs `running` **continuent** (pas de kill).

### Réponse

200 :
```json
{
  "batch_id": "abc123",
  "cancelled_count": 42
}
```

- Batch inconnu → 404
- Batch sans jobs queued → 200 `{ cancelled_count: 0 }`
- 403 / 401 / 503 comme le reste

### Implémentation

```python
@app.post("/v1/admin/bench/batches/{batch_id}/cancel")
def cancel_bench_batch(batch_id: str, authorization: str | None = Header(default=None)) -> dict:
    from doux_planning.api.bench import cancel_batch
    return cancel_batch(authorization, batch_id)
```

Dans `bench.py` :
```python
def cancel_batch(authorization: str | None, batch_id: str) -> dict:
    _require_admin(authorization)
    with session_scope() as db:
        result = db.execute(
            update(BenchJob)
            .where(BenchJob.batch_id == batch_id)
            .where(BenchJob.status == "queued")
            .values(status="cancelled")
        )
        count = result.rowcount
    if count == 0:
        # Vérifier si le batch existe
        with session_scope() as db:
            exists = db.scalar(select(BenchJob.id).where(BenchJob.batch_id == batch_id).limit(1))
            if exists is None:
                raise HTTPException(status_code=404, detail="batch introuvable")
    return {"batch_id": batch_id, "cancelled_count": count}
```

### Statut `cancelled`

Le worker ignore les jobs `cancelled` (il ne prend que `queued`). Pas de changement au worker.

`get_batch` : compter `cancelled` dans les stats si besoin (optionnel — `pct` peut rester basé sur `done + failed`).

## Tests

- `POST cancel` sur batch avec 5 queued → 200 `{ cancelled_count: 5 }`
- `POST cancel` sur batch vide ou déjà annulé → 200 `{ cancelled_count: 0 }`
- `POST cancel` sur batch inconnu → 404
- Jobs `running` ne sont **pas** annulés
- Pytest vert

Signal : `Infra bench-cancel pushed @ <sha>`
