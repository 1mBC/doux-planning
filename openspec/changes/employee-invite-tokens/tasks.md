## 1. Tokens on the fiche

- [x] 1.1 Add `Employee.invite_token` (generated, ≠ id) and `rotate_employee_invite_token`, and verify a new fiche has a non-empty token different from its id
- [x] 1.2 Track `linked_employee_ids` on `RestaurantIdentity` and verify hydrate Saint-Cloud employees each have a non-empty token

## 2. Redeem

- [x] 2.1 Change `redeem_invite` to company code + token (QR) or company code + fiche id (manual), and verify two fiches: manual A OK, second A fails, QR token B links B, wrong company code is `InvalidInviteCode`
- [x] 2.2 After rotate of A, verify the old token fails and the new token redeems; update existing `redeem_invite` callers

## 3. Guardrails

- [x] 3.1 Run `pytest` green without edits to `web/`, `api/`, `contracts/`, `planning.py` preview/fill, or `engine.py` formulas
