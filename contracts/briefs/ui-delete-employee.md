# Brief — agent UI neuf (cloud) · change **delete-employee**

Le tech lead : poubelle **Équipe** + écran re-lien salarié. Relis `contracts/domain/delete-employee.md` UI + `wizard-ui.md` section Équipe. **Gagne.** Tu ne modifies pas `contracts/`.

Instance **neuve**. Branche **`cursor/delete-employee-ui-2843`** depuis la freeze. **Ne merge pas** Python / `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Ne pas toucher** `src/doux_planning/`, `api/`, `contracts/`. Reste `web/`. **`0.53.0`**, note : `Supprimer un salarié ; compte conservé`.

**API** : le DELETE / link peuvent **ne pas être en ligne** tant qu’Infra n’a pas fini. Code **contre le contrat** (types `restaurant_id: string | null`, `DELETE /v1/staff/{id}`, `POST /v1/auth/link`). IronBee E2E complet seulement si l’API répond ; sinon build + parcours UI (confirm, écran code+liste) et **signale** le skip API.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): delete employee keep account v0.53.0`. Signal le SHA.

## Comportement

- Équipe : poubelle, confirm FR du freeze (compte conservé, planning **de cette équipe** jeté, **pas** l’autre). Persistée → DELETE puis GET. Ligne locale → pas d’HTTP.
- `me.kind === "employee"` && `employee_id == null` : **pas** `/planning`. Écran code entreprise → `GET /v1/invites/{code}` → choisir fiche → `POST /v1/auth/link`. Succès → planning.
- Barre : pas « Planning » tant que non affilié. Parser `restaurant_id` null. `/exemple` + company wizard hors poubelle inchangés.

## Vérif

Build. `/context` Équipe : poubelle + texte confirm. Salarié `employee_id` null : écran rattachement, pas de grille. Barre **v0.53.0**. Si DELETE 200 dispo : fiche disparaît, cuisine publié intact.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI delete-employee pushed @ <sha>, v0.53.0`
