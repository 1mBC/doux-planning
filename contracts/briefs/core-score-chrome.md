# Brief — coller dans le chat **Core**

Le tech lead : **chrome notes** — occupation asymétrique (sur-occupation ×2) + `resumes` FR sur `CycleScore`. File notes /10 landed (`master has score landed` @ `bd67508` ou plus récent). Relis `contracts/domain/score.md` — tu le suis, tu ne le modifies pas.

`git pull origin master` (doit contenir ce brief) ; branche **`score-chrome/core` depuis `master`**.

`/opsx-update` le change OpenSpec **`cycle-score`** (déjà existant). Pas de nouveau change. Pas d’archive / sync.

**Process** : tâches + pytest vert → **commit + push `score-chrome/core` toi-même**. Message : `feat(core): asymmetric occupation score and resumes`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`, `saint-cloud.json`. **Pas** de HTTP.  
`SEARCH_CALENDAR_LIMITS` / `SEARCH_SECONDS` / `_attempt_key` / `generate_cycle` keep-best **inchangés**.

## Comportement

- `CycleScore.resumes` : 5 clés, `null` ssi la note l’est. Formes exactes de `score.md`.
- Heures (`notes.contrat`) : `pen` sous = `|écart|/C`, sur = `2×écart/C` ; `note_i = 10 × max(0, 1 − pen_i / 2)`.
- Indispo reste **dans** cet axe. Moyenne des sous-notes présentes. Les deux absentes → `contrat` null.
- Couverture / légal / wellbeing / rôles / poids / globale : **inchangés** (sauf émettre `resumes`).
- Clé JSON `contrat` inchangée.

## Tests

Sur-occupation vs même sous-occupation : note heures **plus basse**. Pile contrat → 10.  
`resumes.couverture` contient `postes tenus` ; `resumes.contrat` contient `contrat` et/ou `indispos tenues` selon les parties.  
`generate_cycle` déterministe inchangé. Pytest engine / recap / board verts.

Tâches cochées + pytest vert → **commit + push** → stop.  
Signal : `Core score-chrome pushed @ <sha>`
