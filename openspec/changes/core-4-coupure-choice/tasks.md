## Tasks

- [ ] 1. Snapshot `engine.py` → `engines/core_3.py`
- [ ] 2. Mettre `data/bench/VERSION` à `core-4`
- [ ] 3. Mettre à jour `registry.py` : `ENGINE_REFS = ("core-0", "core-1", "core-2", "core-3", "core-4")`, `_FROZEN` inclut `core_3`
- [ ] 4. Ajouter paramètre `coupure_matters: bool = True` à `_soft_penalty` dans `engine.py`
- [ ] 5. Modifier `_pick_for_post` dans `engine.py` : détecter `has_choice`, re-scorer avec `coupure_matters=has_choice`
- [ ] 6. Tests unitaires : `engine_ref() == "core-4"`, deux légaux dont un sans coupure, un seul légal avec coupure posé
- [ ] 7. `run_bench(tight, halles, minimal)` vert, 50 listings, keep-best bit-à-bit
- [ ] 8. Pytest moteur verts
