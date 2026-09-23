## Context

See proposal.md. `Wellbeing` already has `consecutive_rest` and the `weekend` radio. Closed days already force `work[day] == 0` in the rest model. Saint-Cloud has no `weekend_rest_day` key and must keep its snapshot stats.

## Goals / Non-Goals

**Goals:**
- Bool on the fiche, warning + solver per week, board row, hydrate default.

**Non-Goals:**
- HTTP persist, snapshot rewrite, aliases for the old list key.

## Decisions

### 1. Additive field, default false

`Wellbeing.weekend_rest_day = False`. Missing JSON key hydrates to false so Saint-Cloud employees stay unchanged.

### 2. Held = Saturday or Sunday rest, closed counts

Helper mirrors consecutive-rest closed-day logic. Sunday closed → already held. Solver constraint: `work[sat] + work[sun] <= 1` per week (closed Sunday is already 0, so Saturday may still be worked).

### 3. Independent of the radio

Both wishes can be posed. Two warning codes. Board emits two rows.

### 4. Do not touch the snapshot

Absent key = false → no new Saint-Cloud warnings. Leave `planning` and stats 92 / 17 / 10/12.

## Risks / Trade-offs

- [Solver may fail coverage if every weekend day is required] → Same slack path as other rest wishes; warning still scores after fill.

## Migration Plan

None for the file snapshot. HTTP persist is Infra.

## Open Questions

None.
