# Brief — coller dans le chat **UI**

Le tech lead : chrome notes — Occupation, résumés, couleur linéaire, plus d’anciennes cartes. **Attends le land Infra** (`master has score-chrome landed` Infra). Relis `contracts/domain/score.md` (section UI).

`git fetch origin` ; si `origin/score-chrome/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score-chrome/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `score-chrome/ui` toi-même**. Message : `feat(web): score chrome occupation resumes v0.26.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.26.0`**, note FR : notes Occupation + résumés, plus d’anciennes cartes.

## Comportement

- `/planning` company **et** `/exemple` : rangée `CycleScoreNotes` **au-dessus** de la grille. **Retirer** `CycleStats` / `Stats` (shifts, vides, alertes, sous-rôle, % heures, souhaits).
- Tableaux légal + souhaits **inchangés**, **sous** la grille.
- Libellé `contrat` : **Occupation /10**. Clé JSON `contrat` inchangée (parser).
- Parser : exiger `resumes` (5 clés, `string | null`). Payload sans `resumes` → pas de notes (ou omit), pas de crash.
- Sous chaque pastille d’axe : `resumes[clé]` tel quel. Globale : pas de sous-ligne.
- Couleur linéaire 0→10 : `hue = 12 × note` (HSL, 0 rouge → 120 vert). `null` → tiret, neutre.
- Pas d’édition des poids. Pas de bench.

## Vérif

Build. Planning + exemple : notes en premier, Occupation (plus « Contrat »), résumé sous chaque note, plus de cartes stats. Switch d’effort = notes + resumes de **ce** slot. Barre **v0.26.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI score-chrome pushed @ <sha>, v0.26.0`
