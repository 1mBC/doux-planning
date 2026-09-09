# Brief — coller dans le chat **UI**

Le tech lead : **pastille Contrat**, titres gras, **tableau 4 col**, matrices **Légal & Contrat** + **Bien-être**. File bench-pack close (`master has bench-pack landed` @ `705668b` ou plus récent). Relis **`contracts/domain/score-facts.md`** (gagne, pastille + tableaux) + `score.md` UI.

`git pull origin master` (doit contenir ce brief) ; branche **`score-tables/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `score-tables/ui` toi-même**. Message : `feat(web): score tables contrat legal wellbeing v0.32.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.32.0`**, note FR : Contrat en gras, détail 4 colonnes, Légal & Contrat fusionnés.

**Pas de brief Core / Infra** : dictionnaire + chrome seulement.

## Comportement

- Pastille `contrat` : **Contrat /10**. Titres d’axe **gras**. Totaux : `occupées / {h}` (sans « contrat ») ; `indispos respectées`.
- Clic pastille **et** liste Alertes : même tableau Catégorie | Sous-catégorie | Statut (⚠️/✅) | Détail. Miss groupés par catégorie, **puis** hits groupés. Pas d’alternance. Zéro sous-titre sous les `h2`.
- `/planning` + `/exemple` (`PublishedPlanning` **et** `App.tsx`) : après Alertes → **Légal & Contrat** (legal_cols + Contrat + Indispos) puis **Bien-être** (wish_cols moins contrat/indispo ; omettre si vide). Cellules emoji + mesure, plus « Règles légales » / « Souhaits bien-être » ici. Wizard contexte inchangé.
- Banc compare : pastilles + clic seulement.

## Vérif

Build. `/exemple` : pastille Contrat ; clic = 4 col, warnings d’abord ; Alertes même format ; un tableau Légal & Contrat avec Diane ⚠️ 30h · 29h / 39h ; Bien-être sans col contrat/indispo ; plus de sous-titres. `/planning` idem. Barre **v0.32.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI score-tables pushed @ <sha>, v0.32.0`
