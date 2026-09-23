# Brief — coller dans le chat **Core Engine**

Le tech lead : **lignée `core-2.2` … `core-2.5`** d’un coup. Les 4 modules. Relis les specs (gagnent) + `engines.md`.

`git pull origin master` ; branche **depuis `master`**.

OpenSpec **`core-2-family-repair`**. Skills → **propose puis apply**. Pas d’archive / sync.

**Process** : pytest vert → **commit + push toi-même**. Titre : `feat(core): core-2.2 to 2.5 from manual gaps`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `web/`, `api/`, `contracts/`. Catalogue **50**. Keep-best **inchangé**. VERSION reste `core-5`.

## Pourquoi (une ligne)

Le manuel du banc, là où il bat core-2 : 0 interdit, 2 repos tenus, couverture par **heures empilées / coupures / réserves / ouvreurs≠fermeurs** — jamais par un 6e jour.

## 4 modules (copies de `core_2.py`, pas de `core_2_1.py`)

| ref | Spec | Idée |
|---|---|---|
| `core-2.2` | `engine-core-2-2.md` | Repair trous **légal** (+4 h, `off_days`, revert si interdit↑ **ou globale↓**) |
| `core-2.3` | `engine-core-2-3.md` | Idem mais cap **48 h légales** + tie-break **titulaire** (petits / triple / république) |
| `core-2.4` | `engine-core-2-4.md` | Passe **11 h** (déplacer un soir pour ouvrir le morning) puis repair 2.2 (pigalle / vaugirard) |
| `core-2.5` | `engine-core-2-5.md` | Fill : **skip** les contrats ≤ 8 h s’il existe un titulaire ; repair 2.2 après (abbesses / clichy) |

Pipe commun : repair **dans** `consider(off_days)`, jamais après keep-best sans `off_days` (bug 2.1).

## SearchTrace

`repairs` **à la racine**. Étendre `SearchTrace` live : `repairs: dict | None = None`.  
`registry` : insérer les 4 refs **après** `core-2.1`, copier `repairs`.  
`attempt_key` = uniquement les 6 clés.

## Tests min (en plus du registre)

- 2.2 : `pigalle` empty<4 interdit=0 ; `marche` interdit=0 ; `petits` globale ≥ core-2
- 2.3 : `petits` empty<10 interdit=0 globale≥core-2 (viser 0 trou) ; `triple` empty<4
- 2.4 : `vaugirard` interdit=0 ; `pigalle` empty<4 interdit=0
- 2.5 : `abbesses` empty=0 interdit=0 ; `clichy` empty<2 interdit=0
- pytest vert
