# Brief — coller dans le chat **UI**

Le tech lead : **podiums Stats banc**. Relis `contracts/domain/bench.md` section **Stats — podiums**. Gagne.

`git pull origin master` ; branche **depuis `master`**.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Pas de route HTTP. Même `GET /v1/admin/bench/versions`.

**Process** : commit + push **ta** branche. Titre : `feat(web): bench stats podium counts v0.51.0`. Pas de PR master. Signal le SHA.

## Comportement

Page `/admin/bench/stats` **en plus** des 3 graphes moyenne/min/max (inchangés).

Pour chaque compute : **4 graphes barres**, X = `engine_refs`.

Ligne = dataset avec au moins un `global` pour cet effort.  
Meilleur = max des globaux présents.

- **1er** : `global == meilleur` (ex-æquo OK)
- **À 0,1 / 0,2 / 0,3** : `global >= meilleur − 0,1` (etc.)

Notes déjà à 1 décimale. Y = nombre de jeux, ymin 0, ymax = nb lignes. Chiffre sur la barre.

Modèle sans run → barre 0 (pas sauté).

Couleur : une teinte par graphe, plus claire quand le seuil s’élargit.

`web/src/release.ts` + `package.json` → **v0.51.0**, note : `Podiums banc 1er / 0,1 / 0,2 / 0,3`.

Vérifier Stats (3 computes × 4 barres) + hover des anciens graphes pas cassé. IronBee si dispo.

Tâches + build → **commit + push** → stop.  
Signal : `UI bench-podiums pushed @ <sha>`
