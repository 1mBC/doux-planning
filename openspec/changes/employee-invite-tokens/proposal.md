## Why

Auth starts with attaching an employee account to a staff fiche. Today `redeem_invite` only checks the restaurant company code and accepts any `employee_id`. QR tokens and “already linked” are missing, so Infra cannot wrap a safe redeem.

## What Changes

- Each `Employee` carries a secret `invite_token` generated when the fiche is created (`≠ id`).
- `rotate_employee_invite_token` issues a new token; the previous one no longer redeems.
- **BREAKING**: `redeem_invite` takes the staff list and either a QR token or a manual `employee_id` (plus company code). Wrong company code → `InvalidInviteCode`. Unknown / already-used token or already-linked fiche → error. QR `employee_id` that does not match the token’s fiche → error.
- `RestaurantIdentity.linked_employee_ids` records which fiches are taken so a later GET invites can list the unlinked ones.
- No passwords, no HTTP, no second restaurateur.

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `staff-configuration`: per-employee invite token, rotate, QR vs manual redeem, and linked-fiche tracking on the restaurant identity.

## Impact

- `src/doux_planning/invites.py`, `src/doux_planning/staff.py`. `hydrate.py` only if Saint-Cloud employees need a non-empty token on load.
- Tests in `tests/test_domain.py` (and existing `redeem_invite` callers). Do not edit `web/`, `api/`, `contracts/`, `planning.py` preview/fill, `engine.py` formulas, or `data/examples/saint-cloud.json`.
