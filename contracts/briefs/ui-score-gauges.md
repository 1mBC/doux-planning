# Brief — coller dans le chat **UI**

Le tech lead : globale à gauche + cadre contrasté + jauge horizontale sur chaque note. **Attends le land Core** (`master has score-gauges landed`). Relis `contracts/domain/score.md` (section UI).

`git fetch origin` ; si `origin/score-gauges/core` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`score-gauges/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `score-gauges/ui` toi-même**. Message : `feat(web): score gauges global left v0.27.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.27.0`**, note FR : globale à gauche, jauges, libellés occupées.

**Pas de brief Infra** : `resumes` déjà émis ; les nouvelles chaînes viennent de Core.

## Comportement

- `/planning` company **et** `/exemple` : **Globale /10 en premier à gauche.** Cadre contrasté (bordure plus épaisse, fond plus saturé, même HSL). Pas de résumé sous la globale.
- **Jauge horizontale** sous le chiffre, sur les 5 axes **et** la globale : largeur de remplissage = `note / 10`. Même `hue = 12 × note`. `null` → jauge vide, neutre.
- `resumes` : afficher les `\n` (`white-space: pre-line`). Occupation = heures puis indispos à la ligne.
- Libellés inchangés (Occupation /10, etc.). Parser `resumes` déjà là.
- Pas de cartes stats. Tableaux légal / souhaits sous la grille.

## Vérif

Build. Planning + exemple : globale à gauche et plus marquée ; jauge sur chaque pastille ; Occupation montre `occupées` et indispos à la ligne ; Rôles montre `affectés` / sous-rôle. Barre **v0.27.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI score-gauges pushed @ <sha>, v0.27.0`
