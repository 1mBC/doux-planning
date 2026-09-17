## Architecture

New module `core_2_1.py` based on `core_2.py` with repair logic added.

## Approach

### generate_cycle modification

```python
def generate_cycle(draft, search):
    # 1. Original core-2 fill
    result = _fill_cycle_core2(draft, search)
    
    # 2. Count empty posts
    empty_before = count_empty_posts(result)
    
    # 3. If empty posts exist, attempt repair
    if empty_before > 0:
        assignments = list(result.assignments)
        filled_count = repair_empty_posts(draft, assignments)
        result = evaluate(draft.with_assignments(tuple(assignments)))
    
    # 4. Build trace with repairs info
    return EngineResult(
        assignments=result.assignments,
        warnings=result.warnings,
        trace=SearchTrace(..., repairs={...})
    )
```

### repair_empty_posts implementation

```python
REPAIR_HOURS_TOLERANCE = 4

def repair_empty_posts(draft, assignments):
    filled_count = 0
    
    for empty_window in get_empty_windows(draft, assignments):
        candidates = []
        for employee in draft.employees:
            if can_repair_fill(draft, assignments, employee, empty_window):
                score = repair_score(draft, assignments, employee, empty_window)
                candidates.append((score, employee))
        
        if candidates:
            candidates.sort()
            best_employee = candidates[0][1]
            apply_repair(assignments, best_employee, empty_window)
            filled_count += 1
    
    return filled_count

def can_repair_fill(draft, assignments, employee, window):
    # 1. Level check
    if employee.level < window.level:
        return False
    
    # 2. 11h rest check
    if not _rest_between_ok(assignments, trial):
        return False
    
    # 3. Coupure ≤ 5h check
    if not _pause_within_legal(assignments, trial):
        return False
    
    # 4. Max 48h check
    if week_hours + duration > MAX_WEEKLY_HOURS:
        return False
    
    # 5. Hours tolerance (contract + 4h)
    if week_hours + duration > contract + REPAIR_HOURS_TOLERANCE:
        return False
    
    # 6. Max coupures check
    if creates_coupure and _would_exceed_coupures(assignments, employee, trial):
        return False
    
    # 7. No cascade check
    if would_create_cascade(draft, assignments, employee, window):
        return False
    
    return True

def repair_score(draft, assignments, employee, window):
    # 1. Hour overage (lower is better)
    projected = week_hours + duration
    overage = max(0, projected - contract)
    
    # 2. Has coupure today (0 if no, 1 if yes)
    has_coupure = 1 if would_create_coupure else 0
    
    # 3. Overqualification
    overqual = employee.level - window.level
    
    return (overage, has_coupure, overqual, employee.id)
```

## Risks

- Repair with hour tolerance could cause hours_miss warnings
- Need to ensure hard constraints never violated
