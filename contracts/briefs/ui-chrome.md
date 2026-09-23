# Brief — coller dans le chat **UI**

Le tech lead : chrome UI — banc sans libellés d’effort, wizard, colonne H. File 46 close (`master @ f064e2a`). Relis **`contracts/domain/bench.md`** UI (tableau) et **`contracts/domain/wizard-ui.md`** (ordre services, rôles, grille H).

`git pull origin master` ; branche **`ui-chrome/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

Pas d’archive / sync. **Pas de Core / Infra.** Pas de `continuous` / chambres.

**Process** : tâches + `npm run build` vert → **commit + push `ui-chrome/ui` toi-même**. Message : `feat(web): bench labels, wizard roles, pale H v0.42.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.42.0`**, note FR : banc sans libellés d’effort, wizard rôles, colonne H plus pâle.

## Comportement

- Banc : pile de 3 deltas **sans** Mini / Opti / Max dans la cellule (l’ordre = Lancer). Lancer / recap / loader / `locked` **inchangés**.
- Services types + semaine type + souhaits + planning : sous-onglets / colonnes / lignes toujours **petit-déj → déj → dîner** (pas l’ordre persisté).
- Rôles : colonnes **Rôle** / **Niveau de compétence** ; sous-titre **« Un niveau plus élevé est capable de tenir un poste de niveau inférieur. »**
- Planning company / exemple / salarié : cellules **H** plus pâles que Début/Fin (même teinte personne). Total semaine inchangé.

## Vérif

Build. Banc : 3 deltas nus par modèle. `/context` rôles + onglets types dans l’ordre. Planning : H plus clair. Barre **v0.42.0**.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI ui-chrome pushed @ <sha>, v0.42.0`
