# Brief — coller dans le chat **UI**

Le tech lead : chrome planning (3 rangées, versions) + stepper cadre + types sans N. **Attends le land Infra** (`master has generate-versions landed`). Relis `generate-versions.md`, `wizard-ui.md` (stepper / colonnes), `v1-generate.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/generate-versions/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`planning-chrome/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master` + worker Compose. Proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `planning-chrome/ui` toi-même**. Message : `feat(web): planning versions chrome steppers types v0.23.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.23.0`**, note FR : trois versions de calcul, steppers cadrés, types sans N.

## Planning company — 3 rangées

1. Salle | Cuisine — bleu = équipe.
2. Minimal | Optimisé | Maximal — bleu = **sélection** (pas de POST). Défaut = `latest`. Slot vide → « Pas encore calculé » (pas l’autre version).
3. **(Re)Calculer le planning** | **Entrer en mode édition** | **Quitter le mode édition** | **Publier** | **Exporter** — **blancs** (actions). Recalculer → POST de l’effort **sélectionné**. Édition : enter avec cet effort. Export = version affichée.

Sous la rangée 3 : **date + heure** `generated_at` (Europe/Paris) du cycle affiché ; absent → tiret.

Loader ≥ 1 s. Maximal = 202 + poll (inchangé). Salarié : `me/planning` `latest` seulement, pas de sélecteur.

## Stepper + types

Snippet **encadré**, libellé **gras**, chiffre **centré**.  
Types : **plus de colonne N**. Titre unique **Niveaux minimal requis (par arrivée | après sortie)**. K départ = sac avant − somme(à garder). Persist inchangée (somme des niveaux).

## Vérif

Build. 2 generates (minimal puis optimized) : clic Minimal / Optimisé change la grille ; timestamp différent ; salarié voit le plus récent. Recalculer ne part que du bouton rangée 3. Types sans N. Steppers cadrés. Barre **v0.23.0**. Exemple 92.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI planning-chrome pushed @ <sha>, v0.23.0`
