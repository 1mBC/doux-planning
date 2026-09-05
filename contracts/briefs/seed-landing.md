# Brief — destinataire **Bastien** (pas un chat spécialiste)

File seed **prêt à lander**. File produit 3→2→1 (wellbeing + seed) close après ce merge.

## Landing (orchestrateur, quand tu dis **land**)

Merge commits, **pas squash**, **pas rebase** :

1. `seed/core` @ `bb9ac1d` → `master` — `Merge branch 'seed/core' into master`
2. `seed/infra` @ `71c9776` → `master` — `Merge branch 'seed/infra' into master`
3. `seed/ui` @ `6dc665b` → `master` — `Merge branch 'seed/ui' into master`

Tip produit : **`master has seed landed`** = SHA du 3ᵉ merge.

Pas d’`/opsx-archive` / `/opsx-sync`. Railway suit `master` (v0.13.0 + `POST /v1/context/seed-example`).

Recette après deploy : `/context` company → **Intégrer l’exemple Saint-Cloud** → confirm → Équipe Diane/Théo, salle prête, nom gardé. `/exemple` toujours 92.
