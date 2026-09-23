# Spec Delta

## ADDED Requirements

### Requirement: Company can delete a staff fiche over HTTP
`DELETE /v1/staff/{id}` (Bearer company) SHALL wrap Core `remove_employee` and persist the staff list. The 200 body MUST be the same `Context` shape as `GET /v1/context`. An unknown fiche or a fiche of another restaurant MUST be HTTP 404 `Fiche introuvable.` An employee Bearer MUST be HTTP 403 `Action réservée au restaurateur.` Persist MUST nullify an affiliated `employee_accounts` row (`restaurant_id` and `employee_id` both NULL, never one without the other), MUST keep that row and `account_emails`, MUST invalidate that account’s employee sessions, MUST delete the `staff_fiches` row only after the FKs are null, MUST NOT call `_persist_state(..., smash_live=True)`, and MUST set only that employee’s team key to `None` on stored `published_cycles` and `live_sandboxes`. The other team’s stored maps MUST stay. `PATCH /v1/context` that omits a still-linked fiche MUST stay HTTP 409 `Cette fiche a déjà un compte.`

#### Scenario: Linked salle fiche is deleted and cuisine published stays
- **WHEN** a company deletes a linked salle fiche while cuisine has a stored published cycle and live sandbox
- **THEN** the response is 200 Context without that fiche, the employee account and email remain with both affiliation ids null, that employee’s sessions are gone, salle published and live are null, and cuisine published and live are unchanged

#### Scenario: Employee cannot delete a fiche
- **WHEN** an employee Bearer deletes `/v1/staff/{id}`
- **THEN** the response is 403 `Action réservée au restaurateur.`

#### Scenario: Unknown fiche is 404
- **WHEN** the restaurateur deletes a fiche id that is not on their restaurant
- **THEN** the response is 404 `Fiche introuvable.`

### Requirement: Unaffiliated employee can log in and re-link
`me.restaurant_id` and `me.employee_id` SHALL be `string | null`. An unaffiliated employee (`kind: employee`) MUST login 200 with both ids null. `POST /v1/auth/link` `{ company_code, employee_id }` (Bearer employee without affiliation) SHALL wrap `redeem_invite` with the existing `account_id` and write affiliation on the same account row. Unknown fiche MUST be 404 `Fiche introuvable.` Company Bearer MUST be 403 `Action réservée au salarié.` Already affiliated MUST be 409 `Vous êtes déjà rattaché à un restaurant.` Bad company code MUST be 400 `Code entreprise ou jeton invalide.` Fiche already linked MUST be 409 `Cette fiche a déjà un compte.` Missing fields MUST be 400 `Champs invalides.` Register’s unknown-fiche mapping MUST stay 400.

#### Scenario: Login after delete then link another fiche
- **WHEN** a linked fiche is deleted and that employee logs in then posts link to a different unlinked fiche
- **THEN** login is 200 with both ids null, and link is 200 me affiliated to the new fiche

### Requirement: Unaffiliated planning is 409
`GET /v1/me/planning` SHALL return HTTP 409 `Vous n'êtes rattaché à aucun restaurant.` when the employee session has a null `employee_id` or `restaurant_id`, and MUST NOT call `employee_board`.

#### Scenario: Planning after delete
- **WHEN** an unaffiliated employee gets `/v1/me/planning`
- **THEN** the response is 409 `Vous n'êtes rattaché à aucun restaurant.`
