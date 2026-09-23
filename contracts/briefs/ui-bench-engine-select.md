# Brief UI — file 61 sélecteur moteur bench

**Freeze** : `contracts/domain/bench.md` @ master tip.  
**Dépendance** : Infra bench-engine-select landed.

## Objectif

Ajouter un menu déroulant pour choisir le moteur utilisé lors des lancements bench.

## Modification

Page `/admin/bench` (`BenchPage.tsx`) :

### Dropdown moteur

- **Position** : sur la **même ligne** que les boutons "Toutes les catégories" / efforts, **à gauche** des boutons.
- **Contenu** : liste des `engine_refs` retournés par `GET /v1/admin/bench/versions`.
- **Défaut** : `versions.engine_ref` (VERSION courant, core-5).
- **État** : stocker le moteur sélectionné dans un `useState`.

### Utilisation

- **Toutes les catégories** (scope=all) : passer `engine_ref` du dropdown dans le body POST.
- **Par compute** (scope=category) : idem.
- **Par dataset** (scope=dataset) : idem.
- **Compléter les trous** (scope=gaps) : **ne pas** passer `engine_ref` (comportement existant, remplit tous les refs).

### Style

- `<select>` natif avec classe `.bench-engine-select`.
- Hauteur alignée sur les boutons existants.
- Marge droite ~12px avant les boutons.

### Exemple HTML

```html
<div className="bench-launch-row">
  <select className="bench-engine-select" value={selectedEngine} onChange={...}>
    {engineRefs.map(ref => <option key={ref} value={ref}>{ref}</option>)}
  </select>
  <button>Toutes les catégories</button>
  ...
</div>
```

### Version

`web/src/release.ts` → `v0.50.0`, note : "Sélecteur moteur sur le banc".  
`web/package.json` → `0.50.0`.

## Tests

- Le dropdown affiche tous les `engine_refs`.
- Sélectionner `core-2` puis cliquer "Minimal" → le job créé a `engine_ref="core-2"`.
- "Compléter les trous" ignore le dropdown (comportement existant).

## Hors scope

Rien.
