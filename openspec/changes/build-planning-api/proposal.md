## Why

Le moteur, le domaine (y compris invites / `PlanningStore`) et `GET /v1/examples/saint-cloud` existent, mais rien n’est encore un contrat HTTP authentifié ni une source de vérité Postgres. Sans ça, ni le client React ni un futur mobile ne peuvent générer, publier, ou laisser un employé lire *son* planning publié.

## What Changes

- Persister le domaine live dans PostgreSQL (staff, structures, hours, cycle, weeks, sandbox, intents, contextes légaux, jobs). Les fichiers `data/` restent la source du seed et le contrat figé, pas un second runtime.
- Seeder au boot / migrate l’exemple Saint-Cloud (resto + snapshot planning + `legal_context` france). `GET /v1/examples/saint-cloud` reste **public**, lit le snapshot stocké, et ne lance ni `generate_cycle` ni job.
- Le légal France est un contexte pays (`legal_contexts`), pas une propriété du restaurant (`legal_context: "france"`).
- Auth restaurateur : email + mot de passe. Auth employé : compte créé avec le code d’invitation déjà specké, puis email + mot de passe. Pas d’OAuth, pas de magic link.
- Droits : restaurateur = config, generate, sandbox, publish. Employé = lecture du publié seulement (ses shifts, pas la grille équipe). Routes resto scopées au `restaurant_id` de la session. Un resto, un restaurateur.
- `POST generate` → job Postgres (`job_id`, `status`, `search_effort`, `estimated_seconds`). `GET job` pour poller. evaluate / swap / rank et sandbox enter/edit/discard/publish restent synchrones.
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
