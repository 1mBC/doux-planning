# Brief — agent UI neuf (cloud) · change **bench-export-speed** (file 74)

Le tech lead : Banc Manuels / IA n’appellent plus `/versions` global. Relis `contracts/domain/bench-export-speed.md` UI (**gagne**). Tu ne modifies pas `contracts/`.

**Pas de Python.** Infra ajoute `?origin=` en parallèle. FastAPI actuel ignore une query inconnue → **toujours** envoyer `origin` depuis les deux pages banc (pas de retry sans query).

Instance **neuve**. Branche **`cursor/bench-export-speed-ui-2843`** depuis **master**. **Ne merge pas** `master`.

`/opsx-update` **`build-planning-ui`**. Reste `web/`. **`0.60.0`**, note : `Export jeu, banc manuels plus rapide`.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): versions origin query v0.60.0`. Signal le SHA.

## Comportement

- `loadBenchVersions({ origin })`. Banc IA → `catalogue`. Banc Manuels → `imported`. Stats inchangé (pas d’origin).
- Exporter ce jeu : même GET `scope=dataset`. Plus de 404 si des runs existent (Infra). Afficher `detail` sinon.
- Filtre client `dataset.origin === origin` **peut rester** (défense) mais la liste API est déjà filtrée.

## Vérif

Build. Barre **v0.60.0**. Appel Banc Manuels = `/v1/admin/bench/versions?origin=imported`.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-export-speed pushed @ <sha>, v0.60.0`
