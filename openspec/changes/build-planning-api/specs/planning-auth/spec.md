## Purpose

Authenticates one restaurateur and linked employees with email and password, scopes every restaurant route to the session’s restaurant, and keeps employee access to published own-shifts only.

## ADDED Requirements

### Requirement: Restaurateur registers and signs in with email and password
The system SHALL let the restaurateur create the single restaurateur account with email and password when none exists yet, then sign in with those credentials. The system MUST issue a session that carries that restaurant’s `restaurant_id`. A second restaurateur registration MUST be rejected. The system MUST NOT offer OAuth or a magic-link / email-token sign-in.

#### Scenario: First restaurateur account
- **WHEN** no restaurateur account exists and a caller registers with email and password
- **THEN** a restaurateur account is created for the deployment restaurant and a session is issued

#### Scenario: Duplicate restaurateur rejected
- **WHEN** a restaurateur account already exists and another caller attempts restaurateur registration
- **THEN** the request is rejected and no second restaurateur is created

#### Scenario: Password login
- **WHEN** the restaurateur submits the registered email and password
- **THEN** a session is issued for that restaurant

#### Scenario: Wrong password
- **WHEN** the restaurateur submits a wrong password
- **THEN** the request is rejected with a French error and no session is issued

### Requirement: Employee creates an account with the restaurant invite code
The system SHALL let an employee create an account by presenting the restaurant invite code already defined in staff-configuration, choosing an unlinked employee profile, and setting email and password. A valid code MUST link the account to that restaurant and that employee. An invalid code MUST be rejected. After the account exists, the employee SHALL sign in with email and password. The system MUST NOT let an employee write unavailabilities, wellbeing preferences, or other staff constraints.

#### Scenario: Preview with valid code
- **WHEN** a caller presents a valid invite code before registering
- **THEN** the system returns the restaurant name and the unlinked employee profiles (id, name, role) and does not require a session

#### Scenario: Employee joins with code
- **WHEN** an employee registers with a valid invite code, an unlinked employee id, email, and password
- **THEN** the account is linked to that restaurant and employee and a session is issued

#### Scenario: Invalid code
- **WHEN** an employee presents an invite code that does not match the restaurant
- **THEN** registration is rejected and no account is created

#### Scenario: Already linked profile
- **WHEN** an employee tries to register against an employee id that already has an account
- **THEN** registration is rejected

### Requirement: Session scopes restaurant routes
Authenticated restaurant routes SHALL use the `restaurant_id` from the session. The client MUST NOT pass a different restaurant id to select another restaurant. A missing or invalid session on a protected route MUST be rejected with a French error.

#### Scenario: Implicit restaurant
- **WHEN** a restaurateur calls a restaurant route with a valid session
- **THEN** reads and writes apply only to the session’s restaurant

#### Scenario: Unauthenticated protected route
- **WHEN** a client calls a protected restaurant route without a session
- **THEN** the request is rejected and no restaurant data is returned

### Requirement: Restaurateur may configure, generate, sandbox, and publish
A restaurateur session SHALL be authorized to read and write restaurant configuration, enter the sandbox, request generation, evaluate, swap, rank, and publish. An employee session MUST be rejected on those mutating or sandbox routes.

#### Scenario: Restaurateur generate allowed
- **WHEN** a restaurateur with a valid session requests generation
- **THEN** the request is authorized for that restaurant

#### Scenario: Employee cannot sandbox
- **WHEN** an employee session calls sandbox enter, edit, discard, publish, or generate
- **THEN** the request is rejected with a French error and the sandbox is unchanged

### Requirement: Employee reads only own published shifts
An employee session SHALL receive only that employee’s shifts from the last published cycle or week instances. The system MUST NOT include other employees’ assignments, MUST NOT include sandbox drafts, and MUST NOT expose the full team grid.

#### Scenario: Own published shifts
- **WHEN** an employee with a linked account requests their planning
- **THEN** the response contains only that employee’s published shifts

#### Scenario: Sandbox is hidden
- **WHEN** the restaurateur has unpublished sandbox edits
- **THEN** the employee planning response still matches the last published assignments for that employee
