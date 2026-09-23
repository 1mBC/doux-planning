# Brief — coller dans le chat **Core Engine**

Le tech lead : modèle bien-être + moteur. Relis `contracts/domain/wellbeing.md` (tu le suis, tu ne le modifies pas). `git pull origin master` ; branche **`wellbeing/core` depuis `master`**.

Nouveau change OpenSpec **`wellbeing-model`**. Skills → **propose puis `/opsx-apply`**. Pas de `/opsx-update` sandbox / generate / auth / employee-board (sauf le mapping `wishes` si le design du change le exige — le comportement board reste « publié + held via codes »). Pas d’archive / sync. Pas de commit tant que le facteur ne le demande pas.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Pas d’HTTP. Formules **légales** inchangées (11 h, 2 repos, coupure 5 h, min shift 4 h, tolérance contrat).

## Comportement

- `Wellbeing` + `Unavailability { weekday, service_id }` + `week_label_scheme` selon le freeze.
- Moteur : warnings **et** solveur alignés (repos consécutifs **par** semaine, we even/odd/every_two, max matin/midi/soir, max coupures y compris 0).
- Enum / clés listées comme **supprimées** : interdites (hydrate refuse).
- `employee_board.wishes` : nouvelle forme `{ kind, held, … }`.
- Adapter `data/examples/saint-cloud.json` (table du freeze). Recompute `planning` **seulement si** le solve change ; alors **remonter les nouveaux stats** au facteur, ne pas éditer le contrat exemple.

## Tests

Scénarios du freeze + pytest domaine / engine / hydrate / employee_board / generate verts.  
HTTP `api/` rouge à cause de l’ancien `wellbeing: []` → **stop liste**, ne pas patcher `api/`.

Tâches cochées + pytest (périmètre ci-dessus) vert → stop. Signal : `Core wellbeing done, pytest <n> passed, no commit.`
