# Brief — coller dans le chat **Infra** (suite, pas une première intro)

Le tech lead a lu ta proposition `build-planning-api` et **valide le plan** (tes 7 points), y compris : snapshot exemple figé, un resto seedé, Bearer opaque, jobs plus tard, `legal_rows` / `wish_rows` uniquement sur l’exemple, moteur hors `api/` intouché.

**Mais tu n’appliques pas tout le change maintenant.** Tranche 0 seulement.

**Contrat HTTP figé (lire, ne pas modifier) :** `contracts/http/v1-examples.md`  
Tes specs restent le *quoi*. Ce fichier fige le 200 Saint-Cloud. Conflit de forme → le contrat gagne.

**`/opsx-apply` : uniquement les tâches 1.1 → 1.4** (Compose/Postgres/Alembic + seed + pointer `GET /v1/examples/{id}` sur le store). **Stop.** Auth, persist live hors exemple, jobs, adapters = tranches 1–2, tu attends le prochain brief.

Séquençage (ça ne change pas l’état cible « Postgres = vérité live ») : tant que l’UI tranche 0 n’est pas signée, si `DATABASE_URL` est **absent**, `uvicorn doux_planning.api.app:app --reload` doit encore servir le snapshot **fichier**. Avec `DATABASE_URL`, même JSON (seed, jamais un solve). Pas un deuxième runtime produit — un fallback local le temps du parallèle.

Même interdits qu’au premier message : pas d’archive, pas de `/opsx-sync`, pas de React, pas de `web/`, pas de commit. Si le 200 ne peut pas être tenu : stop.
