# Brief — destinataire **Bastien** (pas un chat spécialiste)

File wellbeing **prêt à lander**. Seed (bouton exemple) = **change suivant**, après ce merge : il part d’un `master` qui a déjà `Wellbeing`.

## Landing (orchestrateur, quand tu dis **land**)

Merge commits, **pas squash**, **pas rebase** :

1. `wellbeing/core` @ `4005994` → `master` — `Merge branch 'wellbeing/core' into master`
2. `wellbeing/infra` @ `3275e04` → `master` — `Merge branch 'wellbeing/infra' into master`
3. `wellbeing/ui` @ `ebe9a81` → `master` — `Merge branch 'wellbeing/ui' into master`

Tip produit : **`master has wellbeing landed`** = SHA du 3ᵉ merge.

Pas d’`/opsx-archive` / `/opsx-sync`. Railway suit `master` tout seul.

## Après land (pas ce brief)

Bouton **intégrer l’exemple** sur tous les comptes company (pré-BETA) : Core → Infra → UI. Écrase rôles / équipe / types / semaine / souhaits / indispos ; **pas** le planning publié ; **garde le nom** du compte.
