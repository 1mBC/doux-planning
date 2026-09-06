# Brief — coller dans le chat **UI**

Le tech lead : admin hover recap + durée planning + rôles tableau + copies wizard + invite code. **Attends le land Infra** (`master has admin-recap landed`). Relis `contracts/domain/admin.md` (hover), `wizard-ui.md`. **Pas** de delete salarié.

`git fetch origin` ; si `origin/admin-recap/infra` ≠ SHA du signal → **stop**.  
`git pull origin master` ; branche **`wizard-polish/ui` depuis `master`**. **Ne merge pas** Python. API uvicorn `master`.

`/opsx-update` **`build-planning-ui`**. Pas d’archive / sync.

**Process** : tâches + `npm run build` vert → **commit + push `wizard-polish/ui` toi-même**. Message : `feat(web): admin recap roles table wizard copy v0.24.0`. Pas de PR master. Signal le SHA.

**Ne pas toucher** `src/doux_planning/`, `contracts/`. Reste `web/`. **`0.24.0`**, note FR : admin warnings lisibles, rôles tableau, copies wizard.

## Admin

Colonnes **Effort** + **Durée** (tiret si null). Hover : **une carte par warning** comme le recap planning (gravité, jour, semaine A/B, personne, message). Pas seulement `message`.

## Planning

Après le timestamp : **durée** du slot affiché (`duration_seconds`), tiret si absent.

## Wizard

- **Rôles** : `<table>` Nom / Niveau (stepper) / poubelle. Supprimer → confirm FR : lister les **fiches** qui ont ce rôle, dire qu’il faudra les revoir / recalculer, **conseiller de renommer** plutôt. Si confirmé : retire la ligne (fiches inchangées jusqu’au save).
- **Équipe** : plus de phrase sous le titre ; plus de ligne texte d’indispos (chips seuls).
- **Souhaits** : plus de phrase sous le titre.
- **Services types** : plus « Sous-onglets = services offerts ».
- **Semaine type** : plus « Libellés de cycle… » ni « L’autre équipe est renvoyée… ».
- **Inviter** : afficher + **copier le code entreprise** (`company_code`) dans la popup (en plus de l’URL / QR).

## Vérif

Build. Admin : hover riche + effort/durée. Planning : durée sous le timestamp. Rôles table + confirm delete. Copies disparues. Invite montre le code. Barre **v0.24.0**. Exemple 92.

Tâches cochées + build vert → **commit + push** → stop.  
Signal : `UI wizard-polish pushed @ <sha>, v0.24.0`
