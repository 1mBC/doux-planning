# Brief — coller dans le chat **Core Engine**

Le tech lead : **`mix-0`**. Relis **`contracts/domain/engine-mix-0.md`** (gagne) + `engines.md`.

`git pull origin master` ; branche **depuis `master`**.

OpenSpec **`mix-0-experts`**. Skills → propose puis apply. Pas d’archive / sync.

**Process** : pytest vert → commit + push. Titre : `feat(core): mix-0 sequential experts`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. VERSION reste `core-5`. Keep-best **interne** des experts inchangé. Catalogue 50.

## Comportement

Module `engines/mix_0.py` :

```
MIX0_EXPERTS = ("core-2", "core-2.1", "cp-0", "iter-0")
```

`generate_cycle(draft, search)` :

1. Appeler `generate_for(expert, draft, search)` **dans l’ordre**, séquentiel.
2. **minimal / optimized** : chaque expert garde son budget natif (3 s / 30 s).
3. **maximal** : pipe maximal de l’expert, **deadline 150 s** (600/4). Pas 4×600.
4. Choisir le result à **`cycle_score.global` max**. Égalité → `_attempt_key` → ordre liste.
5. Ne jamais s’appeler soi-même.

`SearchTrace.mix` à la racine (winner, runs[4]). Étendre `SearchTrace` : `mix: dict | None = None`. Registry copie `mix`. Insérer `mix-0` après `iter-0`.

## Tests min

- registre se termine par `mix-0`
- `tight/halles` minimal mix-0 : 4 runs, winner renseigné
- le gagnant a la globale la plus haute
- pytest vert
