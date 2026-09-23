# Brief — coller dans le chat **UI**

Le tech lead : dictionnaire `kind` → FR + **clic notes = miss puis hit**. File Infra score-facts close (`master has score-facts landed` côté Infra). Relis **`contracts/domain/score-facts.md`** (gagne) + `score.md` UI.

`git fetch origin` ; si `origin/score-facts/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score-facts/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `score-facts/ui` toi-même**. Message : `feat(web): score facts dictionary clickable notes v0.30.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.30.0`**, note FR : détail notes = manques puis points tenus.

## Comportement

- Parser : `facts[]` (`axis`, `kind`, `polarity`, `payload`). Cells `{ ok, kind, payload }`. `score` **sans** `resumes` (si `resumes` traîne : ignorer). Plus de `warning.message` requis.
- Dictionnaire `score-facts.md` : titre + gabarit. Kind inconnu → `kind` + payload brut, **ne pas inventer**.
- Pastilles `/planning` + `/exemple` : **clic** → une liste, misses de l’axe **puis** hits. Globale = tous les facts (y compris `role_gap`).
- Liste alertes sous la grille : misses evaluate seulement (`kind != role_gap`).
- Résumés sous pastille : composés UI (plus `score.resumes`).
- Tableaux légal / souhaits : rendre depuis payload (Diane `30h · 29h / 39h`).
- Overlay sandbox : `impact` facts via le même dictionnaire. `contract` / `role_fit` inchangés.
- Admin hover + export JSON : `facts`. Vieux log avec `message` et payload vide : afficher `message`.
- Banc compare : ne pas crasher si `warnings` legacy ; préférer `facts`.

## Vérif

Build. `/exemple` : 17 alertes dictionnaire ; clic Occupation / Globale → misses puis hits ; Diane cellule 30h · 29h / 39h ; Théo 11h–16h ; notes /10 encore là.  
`/planning` : mêmes pastilles cliquables, switch effort = facts **de ce** slot. Overlay édition : plus de `message` brut.  
`/admin` hover facts. Barre **v0.30.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI score-facts pushed @ <sha>, v0.30.0`
