# Brief — coller dans le chat **UI** (suite, pas une première intro)

Le tech lead a validé `build-planning-ui` tel que tu l’as proposé, y compris tes 4 décisions :

1. Stats = le JSON (`souhait: 15`), pas le ratio démo `21/29`.
2. Chrome FR (Interdit / Couverture / Souhait) ; `message` moteur affiché tel quel.
3. Totaux semaine = somme des `duration_hours` déjà posés (présentation).
4. Hors scope : édition, generate, sandbox, auth, Docker ; CORS seulement si le proxy casse.

**Contrat HTTP figé (lire, ne pas modifier) :** `contracts/http/v1-examples.md`  
Tes artifacts OpenSpec restent le *quoi*. Ce fichier fige les clés / invariants du 200. Conflit de forme → le contrat gagne.

Tu peux **`/opsx-apply`** sur `build-planning-ui` (toutes les tâches). Même interdits qu’au premier message : pas d’archive, pas de `/opsx-sync`, pas de moteur hors `api/`, pas d’autre route que `GET /v1/examples/saint-cloud`, pas de commit.

API locale inchangée : `uvicorn doux_planning.api.app:app --reload` (snapshot fichier tant que `DATABASE_URL` est absent).

Si une clé du contrat manque : stop, ne invente pas.
