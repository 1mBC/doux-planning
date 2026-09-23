## Why

core-2 is the best engine on the bench, but leaves empty posts on some datasets:
- hours/petits: 10 empty posts (small contracts, not enough hours)
- crafted/pigalle: 4 empty posts (late evening → morning, 11h constraint)
- crafted/clichy/republique: 2 empty posts (multiple types)

iter-0 shows we can fill these posts by accepting more hour overage. core-2.1 applies this idea in a **targeted** way after the initial fill.

## What Changes

### engines/core_2_1.py (new module)

Based on core_2.py, with a **second pass** after fill:

1. Fill fewest-first (identical to core-2)
2. If empty > 0: repair_empty_posts()
3. Keep-best on calendars (identical to core-2)

### repair_empty_posts()

For each empty post (in fewest order):
- Selection criteria: level ≥ post, 11h between shifts, coupure ≤ 5h, max 48h
- Hours tolerance: accept up to +4h beyond contract
- Coupure tolerance: accept midi+soir coupure (if max_coupures allows)
- No cascade: candidate doesn't create new empty post elsewhere

Tie-break: least hour overage → no coupure today → least overqual → employee_id

### Registry

- list_engine_refs = core-0, core-1, core-2, **core-2.1**, core-3, ...
- generate_for("core-2.1") dispatches to core_2_1.generate_cycle

### SearchTrace

Like core-2 + repairs field: { attempted, filled, remaining }

## Capabilities

### Modified Capabilities
- `core-engine`: core-2.1 repairs empty posts with hour tolerance

## Impact

- `src/doux_planning/engines/core_2_1.py` : new module
- `src/doux_planning/engines/registry.py` : add core-2.1 after core-2
- Tests for repair behavior. Pas de web/, api/, contracts/.
