# Supprimer un salarié (Équipe)

Freeze **domaine + HTTP**. Moteur OR-Tools inchangé.  
Gagne sur `wizard-ui.md` (ex-« annulé ») pour la poubelle Équipe.

Le patron retire une **fiche** de son restaurant. Le **compte plateforme** (email + mot de passe) **reste**. Seule l’affiliation (resto + fiche) saute. L’autre équipe (cycle publié, sandbox, labels) **n’est pas** touchée.

## Core

```
UnknownEmployee
remove_employee(state, employee_id) -> RestaurantState
```

- Fiche absente → `UnknownEmployee`.
- Retire la fiche de `state.employees`.
- Retire `employee_id` de `identity.linked_employee_ids` (no-op s’il n’y était pas).
- `published_cycles[team]` de **son** équipe → `None`.
- `live_sandboxes[team]` de **son** équipe → `None` (équivalent `discard_live_sandbox`).
- L’**autre** équipe : `published_cycles` / `live_sandboxes` **intacts**.
- Types, semaine type, rôles, hours, `week_label_scheme` : pas d’écriture dédiée (le schéma de labels peut changer à la lecture, c’est accepté ; on ne dépublie pas l’autre équipe pour ça).
- Pas de comptes / sessions / email (Infra).
- `redeem_invite` **inchangé** (le re-lien Infra le réutilise avec l’`account_id` existant).

Tests : deux équipes, cycle publié des deux, sandbox live sur l’équipe du salarié → `remove_employee` salle : salle publié + sandbox vides ; cuisine publié intact ; fiche absente ; `linked_employee_ids` sans l’id. Inconnu → `UnknownEmployee`. Pytest Saint-Cloud verts.

## Infra HTTP

```
DELETE /v1/staff/{id}              Bearer company → 200 Context
POST   /v1/auth/link               Bearer employee → 200 me
```

`PATCH /v1/context` `employees` qui **omet** une fiche **liée** → **toujours** 409 `Cette fiche a déjà un compte.` (garde-fou). La suppression volontaire = `DELETE`. Fiche **non liée** : DELETE **ou** PATCH omit, même effet fiche.

### `DELETE /v1/staff/{id}`

1. Fiche inconnue / autre resto → 404 `Fiche introuvable.`
2. Employee Bearer → 403 `Action réservée au restaurateur.`
3. Compte affilié à cette fiche : **ne pas** supprimer la ligne `employee_accounts` ni `account_emails`. Mettre `restaurant_id` + `employee_id` à `NULL` (les deux, jamais un seul). Invalider **ses** sessions (`kind: employee` de cet `account_id`).
4. `remove_employee` Core puis persist fiches (delete row). Ordre : nullifier le FK **avant** delete `staff_fiches`.
5. 200 = même `Context` que GET.

Alembic : `employee_accounts.restaurant_id` et `employee_id` nullables. Invariant : les deux null **ou** les deux non-null. Sessions : `restaurant_id` nullable.

### `me` (login / register / GET /v1/me)

```
restaurant_id: string | null
employee_id: string | null
```

- `kind: company` : `restaurant_id` string, `employee_id` null (comme aujourd’hui).
- `kind: employee` affilié : les deux strings.
- `kind: employee` **sans affiliation** : les deux `null`. Login 200 quand même (il reste sur la plateforme).

### `POST /v1/auth/link`

```
{ "company_code": "...", "employee_id": "..." }
```

Bearer **employee sans affiliation**. Wrappe `redeem_invite` (manuel, `employee_id`) avec l’`account_id` **existant**, puis écrit `restaurant_id` / `employee_id` sur **la même** ligne compte. 200 `me` affilié.

| Cas | HTTP | `detail` |
|---|---|---|
| Company Bearer / pas employee | 403 | `Action réservée au salarié.` |
| Déjà affilié (`employee_id` non null) | 409 | `Vous êtes déjà rattaché à un restaurant.` |
| Code faux | 400 | `Code entreprise ou jeton invalide.` |
| Fiche inconnue | 404 | `Fiche introuvable.` |
| Fiche déjà liée | 409 | `Cette fiche a déjà un compte.` |
| Champs manquants | 400 | `Champs invalides.` |

Pas de `employee_token` dans ce change (la liste `GET /v1/invites/{code}` suffit). Email déjà pris au **register** : 409 inchangé (il doit **login** puis link).

### `GET /v1/me/planning`

Sans affiliation (`employee_id` null) → 409 `Vous n'êtes rattaché à aucun restaurant.` Ne pas appeler `employee_board`.

### Jobs generate

**Pas** de nouvelle annulation (pas de `cancelled` sur `generate_jobs`, pas de kill worker). Si un maximal `queued`/`running` de **cette** équipe se termine après le DELETE : **ne pas** écrire `published_cycles` si un `employee_id` d’assignment n’est plus une fiche du resto (job `failed`, détail FR). Si ce garde-fou est lourd → **skip**, documente. Banc inchangé.

## UI

Équipe : poubelle par fiche (chrome rôles). Confirm FR :

- fiche + indispos / souhaits ;
- s’il a un compte : *« Son accès à ce restaurant sera retiré. Il pourra se reconnecter avec le code entreprise. »* ;
- *« Le planning publié de la {salle\|cuisine} sera retiré. L’autre équipe est inchangée. »*

Ligne jamais PATCH : retrait local. Persistée : `DELETE` puis GET context.

`kind: employee` et `employee_id === null` : **pas** `/planning`. Écran : code entreprise → `GET /v1/invites/{code}` → liste fiches non liées → `POST /v1/auth/link`. Succès → `/planning`.

Barre session : pas « Planning » tant que non affilié. `/exemple` inchangé. Company wizard ailleurs inchangé.

`web/src/release.ts` + `package.json` : **0.53.0**, note FR : `Supprimer un salarié ; compte conservé`.

## Hors freeze

Panneau compte salarié. Unlink sans delete fiche. Multi-resto simultané. `employee_token` sur link. Kill job maximal. Archive / sync. `continuous` / chambres.
