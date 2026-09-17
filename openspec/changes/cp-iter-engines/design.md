## Architecture

Deux nouveaux modules engines/ indépendants, chacun avec son generate_cycle.

## Approach

### cp-0 (CP-SAT global)

Structure du modèle :
```python
def generate_cycle(draft, search):
    model = cp_model.CpModel()
    
    # Variables
    work = {}  # work[e_id, day, service] -> BoolVar
    start = {} # start[e_id, day, service] -> IntVar (minutes)
    end = {}   # end[e_id, day, service] -> IntVar (minutes)
    post = {}  # post[e_id, day, service] -> IntVar (level)
    
    # Contraintes dures
    add_rest_constraints(model, ...)      # 2 jours repos / semaine
    add_eleven_hour_constraints(model)    # 11h entre shifts
    add_weekly_cap_constraints(model)     # max 48h / semaine
    add_coupure_constraints(model)        # coupure ≤ 5h
    add_level_constraints(model)          # niveau ≥ poste
    add_max_services_constraints(model)   # max_services dur
    
    # Objectif
    objective = (
        W_EMPTY * sum(empty_posts)
        + W_HOURS * sum(hour_gaps)
        + W_WISH * sum(broken_wishes)
        + W_BELOW * sum(below_role)
        + W_OVERQ * sum(overqual)
    )
    model.Minimize(objective)
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SEARCH_SECONDS[search]
    status = solver.Solve(model)
    
    # Extract assignments
    return EngineResult(assignments, warnings, trace)
```

### iter-0 (post-traitement itératif)

Structure des passes :
```python
def repair_loop(draft, result, max_passes=3):
    assignments = list(result.assignments)
    stats = {"surqual_swaps": 0, "hour_transfers": 0, ...}
    
    for _ in range(max_passes):
        changed = False
        changed |= pass_swap_surqual(draft, assignments, stats)
        changed |= pass_balance_hours(draft, assignments, stats)
        changed |= pass_fill_holes(draft, assignments, stats)
        changed |= pass_reduce_coupures(draft, assignments, stats)
        if not changed:
            break
    
    return assignments, stats

def pass_swap_surqual(draft, assignments, stats):
    # Pour chaque surqual >= 2, chercher swap légal
    for shift in assignments:
        if shift.employee.level > shift.post_level + 1:
            for other in same_day_employees(shift):
                if is_legal_swap(shift, other):
                    apply_swap(assignments, shift, other)
                    stats["surqual_swaps"] += 1
                    return True
    return False
```

## Risks

- cp-0 peut être lent sur gros jeux (timeout)
- iter-0 : les passes peuvent interférer (amélioration d'une casse autre)
- Validation de légalité critique pour iter-0
