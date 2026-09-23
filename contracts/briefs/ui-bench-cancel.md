# Brief — coller dans le chat **UI**

Le tech lead : **bouton annuler batch banc**. Relis **`contracts/domain/bench.md`** section UI loader.

`git pull origin master` ; branche **depuis `master`**.

**Process** : tâches → **commit + push toi-même**. Titre : `feat(web): bench cancel batch button v0.49.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/`, `contracts/`. Attendre que la route Infra soit landée.

## Comportement

### Loader batch (existant)

Actuellement :
```
[##########----------] 50% · ~ 5 min
```

### Ajout bouton Annuler

```
[##########----------] 50% · ~ 5 min  [Annuler]
```

- Bouton **« Annuler »** à droite du loader
- Style : bouton secondaire / discret (pas rouge agressif, juste un lien ou bouton outline)
- Au clic :
  1. Appeler `POST /v1/admin/bench/batches/{batch_id}/cancel`
  2. Arrêter le polling
  3. Refresh versions
  4. Masquer le loader

### API

```typescript
export async function cancelBenchBatch(batchId: string): Promise<{ batch_id: string; cancelled_count: number }> {
  const res = await sendAuth("POST", `/v1/admin/bench/batches/${batchId}/cancel`);
  if (!res.ok) {
    throw new ApiHttpError(res.status, await res.text());
  }
  return res.json();
}
```

### UX

- Pendant l'appel cancel : bouton disabled, texte "Annulation..."
- Après cancel : le loader disparaît, les jobs en cours finissent en background (pas grave)
- Si erreur : afficher dans `setError`

## Version

`web/src/release.ts` → `version: "0.49.0"`, `note: "Bouton annuler sur le banc"`.  
`web/package.json` → `"version": "0.49.0"`.

## Tests

- Bouton visible quand un batch est actif
- Clic → appel POST cancel → loader disparaît
- Pas de bouton quand pas de batch actif

Signal : `UI bench-cancel pushed @ <sha>`
