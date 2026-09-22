# Brief — agent UI neuf (cloud) · change **bench-chrome** (file 72)

Le tech lead : ranger le tableau banc. Relis `contracts/domain/bench-chrome.md` UI (**gagne**). Tu ne modifies pas `contracts/`.

**Attends** file 71 UI (popup import) sur master. Instance **neuve**. Branche **`cursor/bench-chrome-ui-2843`**. **Ne merge pas** `master` / Python.

`/opsx-update` **`build-planning-ui`**. Reste `web/`. **`0.58.0`**, note : `Menu jeu, filtre IA / manuels`.

**Process** : `npm run build` → **commit + push**. Message : `feat(web): bench row menu, origin filter, move exports v0.58.0`. Signal le SHA.

## Comportement

- Plus de colonnes Défi et Lancer.
- `…` sous le nom : 3 lancers, exporter, supprimer (confirm).
- Hover jeu = défi + commentaire.
- Exports globaux dans le bloc **Lancer**.
- Sous Derniers runs : **Tous | IA | Manuels** (`origin`).
- DELETE puis refresh.

## Vérif

Build. Barre **v0.58.0**. Tableau sans Défi/Lancer. Filtre Manuels. Historique + popup import intacts.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI bench-chrome pushed @ <sha>, v0.58.0`
