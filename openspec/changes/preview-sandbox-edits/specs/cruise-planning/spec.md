## ADDED Requirements

### Requirement: Hydrate a delivered cycle into the cycle sandbox
The system SHALL build restaurant staff, structures, hours, and a published 14-day cycle from a planning the engine already delivered, then open the cycle sandbox on that cycle. Hydration MUST copy the delivered assignments into the published cycle and the sandbox draft. Hydration MUST NOT call cycle generation. Scoring the copied draft (warnings on the sandbox) is allowed. The Saint-Cloud example file is a frozen seed for this path and MUST NOT be rewritten as the sandbox working copy.

#### Scenario: Saint-Cloud assignments survive hydration
- **WHEN** the restaurateur hydrates the delivered Saint-Cloud cycle into planning state and enters the cycle sandbox
- **THEN** the sandbox draft has the same shifts as that delivered planning (same person, day, service, start, end, post level), and no new cycle generation ran

#### Scenario: Hydration opens the cycle target
- **WHEN** hydration completes
- **THEN** the open sandbox target is the cruise cycle, not a calendar week, and the restaurateur is not asked to choose week versus cycle for this entry

### Requirement: Preview does not mutate the sandbox draft
A preview of a sandbox gesture MUST return ranked proposals, each with the engine result of that trial and a warning delta against the current sandbox draft. After preview, the sandbox assignments and last scored result MUST be unchanged. Apply of one proposal MUST write that trial’s assignments into the sandbox, rescore, and record a history entry. Preview MUST NOT record history.

#### Scenario: Preview leaves the draft untouched
- **WHEN** the restaurateur previews retune, replace, or swap on a shift in the cycle sandbox
- **THEN** the sandbox still has the same assignments as before the preview, and the history stack is unchanged

#### Scenario: Apply crantes one proposal
- **WHEN** the restaurateur applies one proposal from that preview
- **THEN** the sandbox assignments match that proposal’s trial, warnings are those of the engine on that trial, and history has one new entry

### Requirement: Undo restores the last cranted sandbox state
The cycle sandbox SHALL keep a stack of cranted states (assignments plus last scored result). Undo MUST restore the most recently cranted previous state and pop it. Undo MUST NOT restore a gesture from the middle of the stack. Undo with an empty stack MUST fail and MUST NOT change the draft.

#### Scenario: Undo the last apply
- **WHEN** the restaurateur applies a replace, then undoes
- **THEN** the sandbox assignments and warnings match the draft from before that replace, and a second undo with no remaining history fails without a further change

#### Scenario: Two applies then one undo
- **WHEN** the restaurateur applies a retune then a swap, then undoes once
- **THEN** the sandbox matches the state after the retune only
