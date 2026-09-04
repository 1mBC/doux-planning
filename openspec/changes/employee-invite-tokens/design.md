## Context

See proposal.md. `RestaurantIdentity.invite_code` and `redeem_invite(restaurant, code, account_id, employee_id)` already exist in `invites.py`. `Employee` has no token. HTTP stays in Infra (`contracts/http/v1-auth.md`).

## Goals / Non-Goals

**Goals:**
- Domain redeem that Infra can wrap: company code + token or company code + fiche id.
- Track linked fiches on the restaurant so unlinked lists are possible later.

**Non-Goals:**
- HTTP, passwords, sessions, a second restaurateur, sandbox preview, engine formulas.

## Decisions

### 1. Token lives on `Employee`

`invite_token` default-generated (`secrets.token_urlsafe(16)`), never equal to `id`. `rotate_employee_invite_token(employee) -> Employee` via `replace`. No used-token ledger: after rotate the old string is simply absent; after redeem the fiche id is in `linked_employee_ids`.

### 2. Linked set on `RestaurantIdentity`

`linked_employee_ids: frozenset[str]`. Redeem returns `(EmployeeAccount, RestaurantIdentity)` with the id added. Alternative: leave “already linked” to Infra account tables — rejected so GET invites can filter without HTTP in this change.

### 3. Redeem signature

`redeem_invite(restaurant, employees, company_code, account_id, employee_id=None, employee_token=None)`. Token present → QR path (resolve fiche by token; if `employee_id` is also passed and differs → `InviteTargetMismatch`). Token absent → manual path requires `employee_id` on the staff list. Errors: `InvalidInviteCode`, `UnknownInviteToken`, `UnknownEmployee`, `InviteAlreadyRedeemed`, `InviteTargetMismatch`.

Existing callers (`tests/test_domain.py`, `tests/test_planning.py`) update to the new signature.

### 4. Hydrate

Default factory on `Employee.invite_token` is enough for Saint-Cloud load. Touch `hydrate.py` only if a test proves tokens stay empty.

## Risks / Trade-offs

- [Breaking `redeem_invite` positional args] → Update the two existing tests; no HTTP wrapper yet.
- [Random tokens on each hydrate] → Acceptable for the snapshot; not persisted in `saint-cloud.json`.

## Migration Plan

None for data. Infra maps the new errors after this Python freeze.

## Open Questions

None.
