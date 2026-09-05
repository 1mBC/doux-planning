# Brief — coller dans le chat **UI**

Le tech lead : wizard **Équipe / Souhaits / indispos** + labels A/B vs Paire/Impaire. Infra a poussé **`origin/wellbeing/infra` @ `3275e04`**. Relis `contracts/http/v1-context.md`, `contracts/http/v1-me-planning.md`, `contracts/domain/wellbeing.md` (tu les suis, tu ne les modifies pas).

`git fetch origin` ; si `origin/wellbeing/infra` ≠ `3275e0492c008d02845b496cebb9410088b101fc` → **stop**, remonte.  
`git pull origin master` ; branche **`wellbeing/ui` depuis `master`**. **Ne merge pas** `wellbeing/infra` / `wellbeing/core` (Python). API à part : uvicorn sur le checkout Infra @ `3275e04`, proxy `/v1` inchangé.

`/opsx-update` **`build-planning-ui`**. Pas de mega-change, pas d’archive / sync. Pas de commit.

**Ne pas toucher** `src/doux_planning/`, `contracts/`, Compose, Alembic. Reste `web/`. Incrémente `release.ts` + `package.json` : **`0.12.0`**, note FR sur équipe / souhaits.

## `/context` (company)

Onglets, dans l’ordre : **Rôles → Équipe → Souhaits bien-être → Services → Types → Semaine type**.  
« Fiches » **disparaît**. Souhaits **après** l’équipe. Salle / cuisine toujours indépendantes. PATCH `employees` = liste **complète** (garder l’autre équipe).

### Équipe

Une **ligne par salarié** : nom, rôle, heures contrat, `min_shift_hours`, synthèse FR des indispos.  
Bouton **Ajouter une indispo** sur chaque ligne → popup :

- cases **jours** (lun–dim), multi ; boutons **Tout sélectionner** / **Tout déselectionner** ;
- cases **services** (Petit-déjeuner / Déjeuner / Dîner — ceux du resto si déjà choisis, sinon les 3) ;
- Valider → produit **jour × service** → `{ weekday, service_id }[]` **ajoutés** aux indispos de la fiche (les autres fiches intactes).

Synthèse FR dans la ligne (ex. « Lundi déjeuner, Mardi dîner »). Pouvoir **retirer** un créneau (ou le groupe) depuis la ligne. Plus de `every_morning` / `every_evening` / anciennes clés.

### Souhaits bien-être

Une ligne par salarié, **colonnes** = souhaits (pas une liste de vieilles cases) :

| Colonne | Contrôle | JSON |
|---|---|---|
| Deux repos consécutifs par semaine | case | `consecutive_rest` |
| Week-end | **radio 0 ou 1** : Un we sur deux / We paire / We impaire (décocher = `null`) | `weekend`: `every_two` \| `even` \| `odd` \| `null` |
| Max petit-déj / déj / dîner | 3 champs **chiffre** | `max_services.morning` / `midday` / `evening` — vide = clé absente ; **0** = zéro |
| Nbre de coupures max | chiffre | `max_coupures_per_week` — vide = `null` ; **0** OK |

Onglet **pas** un prérequis de `ready` : on peut le laisser vide et passer à Services.

QR / `invite_token` restent sur la ligne Équipe (comme aujourd’hui sur la fiche).

### Labels

`week_labels` du GET context (`"ab"` \| `"parity"`) : **tout le resto**.  
`"ab"` → **A / B**. `"parity"` → **Paire / Impaire**. Semaine type + grilles `/planning` company **et** salarié. Pas d’invention.

## Autres écrans

- `/planning` employee : `wishes` `{ kind, held, … }` — libellés FR ci-dessus, tenu / non tenu. Indispos `{ weekday, service_id }`. `week_labels`. **Pas** d’edit. Plus de `key` / `WELLBEING_KEYS` morts.
- `/exemple` : types = contrat ; stats **92 / 17 / 10/12 / 47** (plus 21/21 ni below_role 43). Ancre Théo midi lundi inchangée si encore là.
- Company Calculer / live / auth **inchangés** hors labels et types context.

Types TS = contrat ; clé manquante → throw. `detail` API. Pas de nouvelle dépendance. **Pas** de bouton seed.

## Vérif (IronBee ; sinon headless + curl)

`npm run build`. Company : Équipe + popup indispo (2 jours × 1 service → 2 créneaux) + Souhaits (radio we paire → `week_labels` **parity** sur semaine type et `/planning`). Reload = persisté. Employee `/planning` lit les nouveaux wishes. Exemple 92 sans session. Barre **v0.12.0**.

Tâches cochées → stop.  
Signal : `UI wellbeing done, v0.12.0, no commit.`
