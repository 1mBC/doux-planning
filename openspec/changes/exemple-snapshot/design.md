## Context

See proposal.md. `load_delivered_cycle` already builds a draft from the file. `evaluate` and `cycle_recap` already emit French warnings and live wish keys. The file still stores the old English recap.

## Goals / Non-Goals

**Goals:**
- Refresh only the recap blocks of `saint-cloud.json` from evaluate + salle `cycle_recap`.
- Keep a helper so the rewrite is not hand-edited JSON.

**Non-Goals:**
- `generate_cycle`, HTTP persist, dual-read Postgres, UI pins, adding `legal_cols`.

## Decisions

### 1. Refresh helper in `hydrate.py`

Load the JSON, build the same draft as `load_delivered_cycle`, `evaluate`, publish that result on `published_cycles[salle]`, `cycle_recap(state, salle)`, replace `warnings` / `stats` / `legal_rows` / `wish_cols` / `wish_rows`. Leave `restaurant` and `assignments` objects as loaded. Do not import `api/`.

### 2. File write is the delivery

Run the helper once during apply. Tests assert the committed file (92 / Théo / Diane / no dead keys / FR substrings) plus hydrate and seed.

## Risks / Trade-offs

- [Wellbeing held/total and warning count change] → Signal them; do not pin old 10/12 or 17 in contracts.
- [json.dump reformats the file] → Acceptable if values for restaurant and assignments stay the same.

## Migration Plan

File replace only. Infra dual-read / UI pins follow.

## Open Questions

None.
