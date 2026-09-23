# Brief — agent UI neuf (cloud) · change **admin-historique** (file 70)

Le tech lead : table **Note**, bouton **Voir**, clic droit email = **lien copiable** (fenêtre privée). Relis `contracts/domain/admin-historique.md` UI (**gagne**). Tu ne modifies pas `contracts/`.

**Pas de Python.** File 71/72 hors scope (pas de popup import, pas de chrome banc).

Instance **neuve**. Branche **`cursor/admin-historique-ui-2843`** depuis **master**. **Ne merge pas** `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Reste `web/`. **`0.56.0`**, note : `Note, voir le planning, lien de connexion`.

**API** : tant qu’Infra n’a pas mergé, GET generates sans `restaurant_id` / `score_global` → parser **null** (pas de crash). Voir / impersonate : si 404, afficher `detail`. **Jamais** ouvrir un onglet tout seul.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): admin note, view planning, copy impersonate link v0.56.0`. Signal le SHA.

## Comportement

- Colonnes **Note** (`formatCycleNote`) et **Planning** (bouton **Voir**).
- Voir → `/admin/planning/{restaurant_id}` : grille **lecture seule** (4 crans, recaps, pas generate, pas édition live). GET admin cycles + context. Menu admin.
- Clic droit **email** : POST impersonate, copie `url`, toast « Lien copié — ouvre-le en navigation privée. »
- Route `/impersonate/{token}` : POST consume public, `sessionStorage`, `/planning`. Échec → `detail`.

## Vérif

Build. Barre **v0.56.0**. `/admin` : Note + Voir. Non-admin : pas d’appels impersonate. Banc inchangé (Défi / Lancer encore là).

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI admin-historique pushed @ <sha>, v0.56.0`
