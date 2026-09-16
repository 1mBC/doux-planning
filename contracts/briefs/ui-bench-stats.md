# Brief — coller dans le chat **UI**

Le tech lead : **Stats banc** + deltas tableau **×10** et **flèche vs modèle précédent**. Relis **`contracts/domain/bench.md`** section UI (gagne). `git pull origin master` — master doit contenir ce brief. Branche **depuis `master`**.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Pas de route HTTP neuve. Même `GET /v1/admin/bench/versions`.

**Process** : commit + push **ta** branche. Titre : `feat(web): bench stats curves and x10 deltas v0.43.0`. Pas de PR master. Signal le SHA.

## Comportement

- Menu admin : **Historique des computes | Banc | Stats banc**. `/admin/bench/stats`.
- **Plus** de bande Recap (% / min / max) sur `/admin/bench`.
- Stats : **3 graphes SVG** (un par compute). X = modèles, Y = note /10. Courbes **moyenne / min / max** des `global` (couleurs + `ymin` : `bench.md`). Pas de lib graphe.
- Cellule modèle : delta vs Manuel en **entier ×10** ; à droite, indicateur vs `engine_refs` précédent (flèche bleu haut / liseret vert / flèche rouge bas + petit chiffre ×10). Fond cellule = delta Manuel /10 comme aujourd’hui. Premier modèle : pas d’indicateur.
- `web/src/release.ts` + `web/package.json` → **v0.43.0**, note FR : stats banc en courbes, deltas ×10 et flèche vs le modèle d’avant.
- Vérifier Banc **et** Stats (desktop + une largeur tableau). IronBee si dispo.

Tâches + build + vérif → **commit + push** → stop.  
Signal : `UI bench-stats pushed @ <sha>`
