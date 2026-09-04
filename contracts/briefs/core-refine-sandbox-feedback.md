# Brief — coller dans le chat **Core Engine** (suite)

Le tech lead : `preview-sandbox-edits` est en prod UI/HTTP. Le feedback restaurateur est illisible / mal classé. On corrige le **Python**, pas l’overlay.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, l’archive V0, FIFO / keep-best / `generate_cycle`. Un seul `evaluate` complet (on ne fait pas un second scoreur « local »). Pas d’HTTP. Pas de commit. Pas d’archive / sync.

Nouveau change OpenSpec `refine-sandbox-feedback`. Skills openspec → **propose puis `/opsx-apply`**. `preview-sandbox-edits` reste clos (tu n’y réécris pas les artifacts) ; tu **étends** `planning.py` / tests.

## 1. Retune = un pas, plus une liste

Remplacer l’énumération ±2 h. API du genre : à partir du shift courant, un essai avec `start_minutes` et `end_minutes` (quantum 15, durée ≥ `min_shift_hours`, clip 0–1440). L’UI enverra ±15 sur début et/ou fin. Preview → **une** proposition (ou un impact), draft inchangé. Identity pair (mêmes heures) → erreur / liste vide, pas un no-op silencieux maquillé en succès.

Garder `apply_proposal` / undo pile.

## 2. Ranking replace et swap = delta, pas les totaux du cycle

Aujourd’hui `preview_replace` réutilise `rank_candidates` trié sur le **nombre total** d’interdits/souhaits du trial 14 j. Résultat : 1 interdit + 1 souhait cassé peut passer **devant** 1 interdit seul.

Trier les previews occupés sur le **changement vs draft courant** : interdits **ajoutés**, puis souhaits **ajoutés**, puis écart heures-contrat (`_hours_miss` trial vs current), puis `_attempt_key` du trial. `rank_candidates` **vide** (génération / trou) : ne pas changer.

## 3. Impact résumé (c’est ça que l’overlay doit montrer)

Ne plus s’appuyer sur `delta.unchanged` ni sur toute la liste added du cycle.

Pour un trial, construire un résumé :

- **interdits nouveaux** (rouge côté UI) ;
- **souhaits cassés** = souhaits **ajoutés** (orange) ;
- **contrat** seulement pour les personnes du geste : titulaire retiré et/ou assigné (retune = la personne du shift ; replace = ancien + nouveau ; swap = les deux). Minutes vs contrat : rapprochement / éloignement / excès. Pas les autres employés.
- Couverture : seulement `empty_post` (ou interdit couverture) **ajouté ou retiré**, pas le bruit.

Rien d’autre. Les warnings `message` moteur restent attachés à ces items (pas de nouveau diagnostic rédigé).

## 4. Score global de planning

Exposer la clé keep-best déjà là (`_attempt_key` : empty, interdit, hours_miss, souhait, below_role, overqualification) sur le draft courant **et** le trial, pour que l’UI affiche avant → après. Ne pas inventer une autre formule.

## Tests

Hydrater Saint-Cloud ou petit fixture. Cas ranking : un remplaçant qui n’ajoute qu’un interdit doit passer **avant** un remplaçant qui ajoute interdit + souhait. Retune ±15 : une proposition, draft intact. Impact : un contrat qui s’améliore pour A ne liste pas B inchangé.

Si doute : demander. Quand les tâches sont cochées et pytest vert, tu t’arrêtes (pas d’archive).
