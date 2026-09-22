# Export jeu + versions par origine (file 74)

Freeze **Infra + UI**. **Pas de Core.**  
Gagne sur `bench.md` (`scope=dataset` / GET `/versions`) et complète `admin-ui-pass.md` (`origin` déjà là sur run/export).

Deux bugs vus sur Railway (Banc Manuels) :

1. **Exporter ce jeu** → 404 `Aucun run pour ce jeu.` alors que le tableau montre des cellules. Cause : l’export dataset ne prenait que les last-run du **`engine_ref` VERSION**. Un import copie les computes resto sous **leur** `engine_ref` (souvent ≠ VERSION) ; un lancer depuis le sélecteur aussi. Les 4 runs existent, mais pas sous VERSION.
2. **Banc Manuels** lent : `GET /versions` charge **tout** le catalogue (50 jeux, tous les `bench_runs` JSONB, contextes importés) puis l’UI filtre `origin=imported`.

## Décisions figées

1. `GET …/export?scope=dataset` exporte **tous** les last-run de **ce** jeu, **tous** les `engine_ref` (même forme que `scope=bank` pour une ligne). 404 `Aucun run pour ce jeu.` **seulement** s’il n’existe **aucun** `bench_runs` pour ce couple. Copied import (`trace=null`) **comptent**.
2. `scope=below_manuel` reste last-run du **VERSION courant** seulement (inchangé).
3. `GET /v1/admin/bench/versions?origin=catalogue|imported` : listings **et** runs **déjà filtrés**. Absent / `null` / `""` → les deux (Stats banc). Inconnu → 400 `Champs invalides.`
4. Banc IA envoie `origin=catalogue`. Banc Manuels envoie `origin=imported`. Stats **sans** `origin`.
5. Chemin versions : **ne pas** charger `bench_runs.assignments` / `warnings` / `trace`, ni `bench_imported_datasets.context`.

## Export dataset

```
GET /v1/admin/bench/export?scope=dataset&category=&dataset_id=
```

- Jeu inconnu (ni listing, ni tombstone utile) → 404 `Jeu introuvable.`
- Jeu connu, **0** row `bench_runs` → 404 `Aucun run pour ce jeu.`
- Sinon 200 : **un** dataset, `efforts` = chaque last-run `(engine_ref, search_effort)` qui existe (ordre registre puis effort, comme `bank`). `engine_ref` sur chaque effort. `context` = snapshot importé (JSONB) ou `context.json` catalogue. `manual` = CycleSlice expected.
- Copied runs import (`app_version` = `slot.engine_ref` resto, `trace=null`) : inclus s’ils sont le last-run de ce quad.
- Query `origin` **ignorée** (le couple identifie le jeu) — déjà file 73.

Implémentation attendue : réutiliser `_latest_runs_by_quad` + `_bank_pack_entry` (ou équivalent). **Ne plus** passer par `_latest_current_runs_map` pour `scope=dataset`.

## GET versions

```
GET /v1/admin/bench/versions
GET /v1/admin/bench/versions?origin=catalogue
GET /v1/admin/bench/versions?origin=imported
```

JSON **inchangé** (mêmes clés). `origin` query :

- `catalogue` → datasets `origin=catalogue` seulement ; SQL `bench_runs.category != 'imported'` (ou `IN` catégories catalogue). **Ne pas** appeler `list_imported_rows` / lire contextes importés.
- `imported` → datasets importés seulement ; SQL `bench_runs.category = 'imported'`. **Ne pas** parcourir `data/bench/**` (`list_bench_datasets` skip).
- absent → comportement actuel (catalogue ∪ importés) pour Stats.

`engine_ref` / `engine_refs` : `list_engine_refs()` **complet** (le sélecteur lance n’importe quel moteur) ∪ extras vus dans les runs **de ce filtre**.

Payload cellules : `run_id`, `global`, `deltas`, `duration_seconds` seulement — **load_only** / SELECT ciblé, pas les JSONB lourds.

Importés : pour `manual` / `comment` / `override`, SELECT colonnes utiles (`id`, `name`, `challenge_fr`, `comment`, `manual_score_override`, `expected`) — **pas** `context`.

Tombstones inchangés.

## UI

- `loadBenchVersions({ origin })` : Banc IA `catalogue`, Banc Manuels `imported`.
- Stats : `loadBenchVersions()` sans query.
- Exporter ce jeu : **même** GET qu’aujourd’hui (plus de 404 si des runs existent, quel que soit VERSION). Afficher `detail` si vraiment 0 run.
- **`0.60.0`**, note : `Export jeu, banc manuels plus rapide`.

## Tests

Infra (`skipif` sans `DATABASE_URL`) :

- Import resto avec computes publiés dont `engine_ref` ≠ VERSION, **sans** relancer VERSION → `scope=dataset` **200**, `efforts` non vide, au moins un `engine_ref` ≠ VERSION. Plus de 404.
- Jeu catalogue sans aucun run → 404 `Aucun run pour ce jeu.`
- `versions?origin=imported` : aucun dataset `origin=catalogue` ; `versions?origin=catalogue` : aucun `imported`.
- `origin=nope` → 400 `Champs invalides.`
- Sans `origin` : les deux origines encore là.
- 403 non-admin.

UI : `npm run build`. Barre 0.60.0. Network Banc Manuels : query `origin=imported`.

## Hors freeze

Stats banc plus rapide. Pagination runs. Éditer un jeu importé. Solve cuisine.
