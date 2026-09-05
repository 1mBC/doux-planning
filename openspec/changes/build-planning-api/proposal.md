## Why

Le moteur, le domaine (y compris invites / `PlanningStore`) et `GET /v1/examples/saint-cloud` existent, mais rien n’est encore un contrat HTTP authentifié ni une source de vérité Postgres. Sans ça, ni le client React ni un futur mobile ne peuvent générer, publier, ou laisser un employé lire *son* planning publié.

## What Changes

- Persister le **contexte live** (`GET` / `PATCH /v1/context`) et les **cycles publiés par équipe** (`POST /v1/generate` + `GET /v1/cycles`, `contracts/http/v1-generate.md`) : wrappe Core `generate_team`, persist JSONB `published_cycles`. Sync, pas de jobs / worker. Publish semaine / `/me/shifts` restent plus tard. Les fichiers `data/` restent le seed figé.
- Seeder au boot / migrate l’exemple Saint-Cloud (resto + snapshot planning + `legal_context` france). `GET /v1/examples/saint-cloud` reste **public**, lit le snapshot stocké, et ne lance ni `generate_cycle` ni job.
- Le légal France est un contexte pays (`legal_contexts`), pas une propriété du restaurant (`legal_context: "france"`).
- Auth unifiée (`contracts/http/v1-auth.md`) : `POST /v1/auth/register` (`kind: company` | `employee`) et un seul `POST /v1/auth/login`. `kind: company` crée une **nouvelle** entreprise vide (nom `""`), un restaurateur, pas Saint-Cloud. `kind: employee` wrappe `redeem_invite` (QR ou manuel). Pas d’OAuth, pas de magic link. Les vieilles routes `/v1/auth/restaurateur/*` et `/v1/auth/employee/*` ne s’implémentent pas.
- Droits : restaurateur (`kind: company`) = config, generate, sandbox, publish (plus tard). Employé = lecture du publié seulement. Routes resto scopées au `restaurant_id` de la session. Un restaurateur par entreprise live. Sandbox et exemple restent publics dans la tranche auth.
- `POST /v1/generate` synchrone → `generate_team` → 200 `{ team, search_effort, published }`. `GET /v1/cycles` relit le persisté. Sandbox **live** : `/v1/live/sandbox/{team}/…` wrappe Core enter/preview/apply/undo/discard/publish, persist `live_sandboxes` (pas la table joujou). `GET /v1/me/planning` (Bearer employee) wrappe `employee_board` — grille publiée de son équipe, pas `/me/shifts`. Pas de table `jobs`, pas de worker. evaluate / swap / rank restent plus tard.
- Wrap HTTP de la forme Core `Wellbeing` : `GET`/`PATCH /v1/context` et `GET /v1/me/planning` exposent l’objet wellbeing, les indispos `{ weekday, service_id }`, `week_labels` (`week_label_scheme`), et les souhaits `{ kind, held, … }` (`BoardWish`). Persist JSONB objet. Plus de liste de clés, plus de `every_*`, plus de `WellbeingPreference`.
- Persist / GET `wellbeing.weekend_rest_day` (bool Core, défaut `false` si clé absente). GET context expose toujours le bool. `GET /v1/me/planning` inclut `{ kind: "weekend_rest_day", held }` si la case est posée. `at_least_one_weekend_rest_day` → 400, pas d’alias. Pas d’Alembic.
- `POST /v1/context/seed-example` (Bearer company, pas de body) wrappe Core `seed_example_context` : smash du contexte live depuis le fichier Saint-Cloud (services, hours, ladders, types, typical_week, fiches + tokens Core). Vide `published_cycles`, `live_sandboxes`, `linked_employee_ids` et les comptes salariés de **cette** company. Garde `id` / `name` / `invite_code` / `legal_context_id`. Pas de 409 fiche liée. Pas de `hydrate_delivered_cycle`. Exemple public 92 inchangé.
- Un seul chemin de score : appeler le moteur, sérialiser `EngineResult`. Pas de Redis/Celery. Pas de React. Pas de modification du moteur hors `api/` sauf blocage.
- Ne pas archiver `define-planning-core`. Ne pas synchroniser ses deltas vers les specs principales.

## Capabilities

### New Capabilities

- `planning-examples`: contrat public de l’exemple Saint-Cloud, split légal / resto, seed Postgres, lecture snapshot sans compute.
- `planning-auth`: comptes restaurateur et employé, sessions, isolation `restaurant_id`, droits.
- `planning-persistence`: Postgres comme source de vérité live pour le domaine déjà specké.
- `generation-jobs`: jobs asynchrones pour `generate_cycle` (effort, ETA, polling).
- `planning-adapters`: routes HTTP synchrones (evaluate, swap, rank, sandbox, persist CRUD) qui adaptent vers le moteur / `PlanningStore`.

### Modified Capabilities

- (aucune — le comportement moteur reste dans `define-planning-core` ; ce change n’ajoute que le contrat HTTP, l’auth, la persistance et le wrapping job)

## Impact

Nouveau : schéma Postgres / migrations, Docker Compose (`db` + `api` + `worker`), routes FastAPI sous `/v1`, hashing mot de passe, table `jobs`. Dépendances : driver Postgres, outil de migration. Fichiers existants : `src/doux_planning/api/` (étendre), tests existants (`tests/test_planning.py` pour l’exemple). Hors scope : `web/`, `src/doux_planning/` hors `api/` (sauf blocage), notifications, extras, multi-resto, OAuth, contraintes saisies par l’employé.
