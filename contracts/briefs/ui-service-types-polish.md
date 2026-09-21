# Brief — agent UI neuf (cloud) · change **service-types-polish**

Le tech lead : polish **Services types** (`/context`). Relis `contracts/domain/wizard-ui.md` (sections ordre d’affichage, Services types, cadran, réordonnancement). **Gagne** sur ce fichier. Tu ne le modifies pas.

Instance **neuve** (pas le chat UI historique). Branche **`cursor/service-types-ui-2843`** depuis la branche freeze (déjà checkoutee si le facteur t’a lancé dessus ; sinon `git fetch` + checkout de cette base, puis `git checkout -b cursor/service-types-ui-2843`). **Ne merge pas** Python / `master`.

`/opsx-update` **`build-planning-ui`**. Pas de mega-change. Pas d’archive / sync.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.52.0`**, note FR : `Services types : PDJ d’abord, Départ, cadran d’heure`.

**Process** : IronBee (parcours réel, pas un screenshot) + `npm run build` → **commit + push ta branche**. Titre commit : `feat(web): service types order, depart, time dial v0.52.0`. Pas de merge `master`. Signal le SHA.

## Comportement

- Sous-onglets Services types (et colonnes **semaine type**, même freeze déjà cassé) : **Petit-déjeuner → Déjeuner → Dîner** parmi les services **offerts**. `CONTEXT_SERVICES.filter(...)`. **Jamais** `services.map` pour l’ordre d’affichage. Persist `services[]` inchangé.
- Table types : **Départ** à la place de **Sortie** (cellule + thead « après départ »). JSON `departures` / clés moteur **intouchables**. « Ajouter un départ » déjà bon.
- **Ajouter une arrivée / un départ** : dialog cadran **avant** d’insérer. Prérempli 11h00 / 16h00. Annuler / Escape / backdrop = pas de ligne. Clic sur l’heure du stepper = même cadran (édition). Heure : boutons 0–23 **ou** saisie 0–23. Minutes : 00 / 15 / 30 / 45 **ou** saisie 0–59. Valider off si invalide. `time_minutes >= 1440` à l’édition : conserver le palier 24h (voir freeze). ±15 inchangé.
- Réordre chrono après changement d’heure : anim **≥ 500 ms**, visible ; fond focus sur la ligne éditée jusqu’à la prochaine édition d’heure. `prefers-reduced-motion` : snap + focus. Pas d’anim sur les ± niveaux. Pas de nouvelle dep.

Hors freeze : `SERVICE_ROWS` Matin/Soir du joujou planning, overlay sandbox, HTTP, moteur.

## Vérif (IronBee obligatoire)

`npm run build`. `/context` company, équipe avec au moins PDJ+déj+dîner **cochés dans un autre ordre** (déj d’abord) → onglets types **PDJ puis déj puis dîner** ; semaine type : mêmes colonnes. Ligne **Départ** (plus Sortie). Ajouter arrivée → cadran → valider 8h07 → ligne à 8h07. ±15 qui croise une autre ligne → glisse ≥ 0,5 s + fond focus. Escape sur cadran d’ajout = pas de ligne. Barre **v0.52.0**. `/exemple` inchangé.

Tâches cochées + build vert + IronBee → **commit + push** → stop.  
Signal : `UI service-types-polish pushed @ <sha>, v0.52.0`
