# Brief — coller dans le chat **Core Engine**

Le tech lead : on attaque l’auth. Premier maillon **Python** : rattacher un compte employé à une **fiche** via code entreprise et/ou jeton QR. Relis `contracts/http/v1-auth.md` (tu le suis, tu ne le modifies pas).

Nouveau change OpenSpec **`employee-invite-tokens`**. Skills → **propose puis `/opsx-apply`**. Pas un mega-change auth/HTTP. Pas de `/opsx-update` sandbox.

**Ne pas toucher** `web/`, `src/doux_planning/api/`, `contracts/`, `planning.py` preview/fill, `engine.py` formules, FIFO / keep-best / `generate_cycle`. Pas d’HTTP. Pas de commit. Pas d’archive / sync.

## Comportement

- `RestaurantIdentity.invite_code` reste le **code entreprise**.
- Chaque `Employee` a un `invite_token` (secret, généré à la création de la fiche, ≠ `id`).
- `rotate_employee_invite_token(employee) -> Employee` : nouveau jeton, l’ancien ne redeem plus.
- `redeem_invite(...)` :
  - code entreprise faux → `InvalidInviteCode` ;
  - **QR** : code entreprise + `employee_token` → lie **cette** fiche (`employee_id` ignoré s’il est passé et ne matche pas → erreur) ;
  - **manuel** : code entreprise + `employee_id` (fiche existante) ;
  - jeton déjà utilisé / fiche déjà liée (si tu tracks `linked`) / jeton inconnu → erreur.
- Une fiche, un compte. Pas de mot de passe ici (Infra). Pas de second restaurateur dans ce change.

Si tu as besoin d’un set `linked_employee_ids` sur le resto pour « déjà liée », OK domaine ; sinon documente comment Infra saura qu’une fiche est prise (ex. table comptes plus tard — alors le redeem Core vérifie seulement code/jeton/id existant, et « déjà liée » sera Infra). **Préfère** un ensemble d’ids liés côté `RestaurantIdentity` ou store si c’est naturel, pour que le GET invites (plus tard) liste les non liées.

## Tests

Créer deux fiches ; redeem manuel sur A OK ; même jeton A → erreur ; rotate A puis ancien jeton → erreur, nouveau → OK ; QR token B lie B ; mauvais `company_code` → `InvalidInviteCode`. Hydrate Saint-Cloud : chaque employé a un token non vide (si tu touches `hydrate.py` pour ça seulement, OK).

Tâches cochées + pytest vert → stop.
