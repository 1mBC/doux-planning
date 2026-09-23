## Tasks

- [ ] 1. Snapshot engine.py → engines/core_4.py
- [ ] 2. Update VERSION to core-5
- [ ] 3. Modify engine.py _soft_penalty: int(not started_day), remove coupure_matters
- [ ] 4. Simplify engine.py _pick_for_post (remove has_choice logic)
- [ ] 5. Create engines/core_6.py with _is_rare and rare-aware fill
- [ ] 6. Update registry.py: ENGINE_REFS core-0..core-6, _FROZEN, generate_for traces
- [ ] 7. Update context.py generate_team with engine_ref parameter
- [ ] 8. Update test_bench.py assertions for core-5/core-6
- [ ] 9. Add test for core-5 prefer already-there
- [ ] 10. Add tests for core-6 rare recase logic
- [ ] 11. Run pytest, verify 50 listings, commit + push
