# Brief — coller dans le chat **UI** (suite)

Le tech lead : **Infra a fini.** `POST /v1/sandbox/discard` + `history[]` recap. Contrat : `contracts/http/v1-sandbox-edit.md`.

**Pas un nouveau change.** `/opsx-update` puis apply sur **`sandbox-edit-ui`**. Uniquement `web/`. Pas d’archive / commit.

## Historique = API

Aujourd’hui `parseHistoryCran` ne lit que `index` + `gesture`, et « Lecture » fait `setJournal([])`. Parser le recap : `shift`, `slot`, `employee_id`, `start_minutes`, `end_minutes`, `partner`, `impact` (pas de `current_score` sur un cran — normal). En faire le `HistoryEntry` (proposal synthétique pour l’affichage impact, scores dummy/absents OK si on n’affiche pas le score).

`startEdit` / GET : **cette** liste, plus un journal React comme source. Lecture peut oublier le state local.

## Tout annuler

Bouton **Tout annuler** si `history.length > 0` → `POST /v1/sandbox/discard`. 200 = grille reset + history `[]`. 404 → `detail` français. Lecture ne discard pas.

IronBee : craner, Lecture, Mode édition → qui / heures / impact encore là ; Tout annuler → brouillon initial ; example 92.
