## ADDED Requirements

### Requirement: Employee fiche has a secret invite token
The system SHALL give each employee fiche a secret invite token at creation. The token MUST NOT equal the fiche id. The restaurateur MAY rotate that token; after rotation the previous token MUST NOT attach any account.

#### Scenario: New fiche has a token
- **WHEN** the restaurateur creates an employee fiche
- **THEN** that fiche has a non-empty invite token different from its id

#### Scenario: Rotated token replaces the old one
- **WHEN** the restaurateur rotates the invite token of an already created fiche
- **THEN** a later redeem with the previous token fails and a redeem with the new token can attach that fiche

### Requirement: Redeem links one fiche to one account
The system SHALL attach an employee account to exactly one unlinked fiche of a restaurant. Redeem MUST accept either the company invite code plus that fiche’s current invite token (QR), or the company invite code plus an existing unlinked fiche id (manual). A wrong company code MUST be rejected as an invalid invite code. An unknown token, a token that no longer matches, a fiche already linked, or a QR redeem whose fiche id does not match the token MUST fail. Passwords are out of scope.

#### Scenario: Manual redeem then reuse fails
- **WHEN** two unlinked fiches exist and a caller redeems the company code with fiche A’s id
- **THEN** the account is linked to A and A is marked linked; a second redeem of A (same token or same id) fails

#### Scenario: QR redeem attaches the token’s fiche
- **WHEN** a caller redeems a valid company code with fiche B’s current invite token
- **THEN** the account is linked to B

#### Scenario: Wrong company code is rejected
- **WHEN** a caller presents a company code that is not the restaurant’s invite code
- **THEN** redeem fails as an invalid invite code and no fiche is linked

## MODIFIED Requirements

### Requirement: Restaurant invite code
The system SHALL let the restaurateur generate a company invite code from the interface. When an employee creates an account, they MUST present that company code together with either an unlinked fiche id or that fiche’s invite token. The system MUST then link the account to that restaurant and that fiche.

#### Scenario: Employee joins with code
- **WHEN** an employee creates an account using a valid company invite code and an unlinked fiche
- **THEN** the account is linked to that restaurant and can see that restaurant’s published planning
