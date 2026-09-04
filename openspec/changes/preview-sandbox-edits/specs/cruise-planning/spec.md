## ADDED Requirements

### Requirement: Hydrate a delivered cycle into the cycle sandbox
The system SHALL build restaurant staff, structures, hours, and a published 14-day cycle from a planning the engine already delivered, then open the cycle sandbox on that cycle. Hydration MUST copy the delivered assignments into the published cycle and the sandbox draft. Hydration MUST NOT call cycle generation. The Saint-Cloud example file is a frozen seed and MUST NOT be rewritten as the sandbox working copy.

#### Scenario: Saint-Cloud assignments survive hydration
- **WHEN** the restaurateur hydrates the delivered Saint-Cloud cycle into planning state and enters the cycle sandbox
- **THEN** the sandbox draft has the same shifts as that delivered planning, and no new cycle generation ran

#### Scenario: Hydration opens the cycle target
- **WHEN** hydration completes
- **THEN** the open sandbox target is the cruise cycle, not a calendar week

### Requirement: Preview does not mutate the sandbox draft
A preview of a sandbox gesture MUST return ranked proposals, each with impact and keep-best scores, without changing assignments, last scored result, or history. Apply of one proposal MUST write that trial’s assignments into the sandbox, rescore, and record a history entry.

#### Scenario: Preview leaves the draft untouched
- **WHEN** the restaurateur previews retune, replace, swap, or fill
- **THEN** the sandbox still has the same assignments as before the preview, and the history stack is unchanged

#### Scenario: Apply crantes one proposal
- **WHEN** the restaurateur applies one proposal from that preview
- **THEN** the sandbox assignments match that proposal’s trial and history has one new entry

### Requirement: Undo restores the last cranted sandbox state
The cycle sandbox SHALL keep a stack of cranted states. Undo MUST restore the most recently cranted previous state and pop it. Undo with an empty stack MUST fail and MUST NOT change the draft.

#### Scenario: Undo the last apply
- **WHEN** the restaurateur applies a replace, then undoes
- **THEN** the sandbox assignments match the draft from before that replace

#### Scenario: Two applies then one undo
- **WHEN** the restaurateur applies a retune then a swap, then undoes once
- **THEN** the sandbox matches the state after the retune only
