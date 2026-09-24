# Min. créneau par service (fiche)

Freeze **domaine + HTTP + UI**.  
Gagne sur `restaurant-context.md` / `wizard-ui.md` / `http/v1-context.md` pour `min_shift_hours`.

Une fiche a **un minimum par service offert**, pas une seule durée pour tous. Défaut **4 h** partout (Saint-Cloud, banc, fiches existantes à 4). Formules d’étirement **inchangées** : on change seulement la valeur lue selon le `service_id` du créneau.

## Core

```
DEFAULT_MIN_SHIFT_HOURS = 4.0
Employee.min_shift_hours: Mapping[str, float]   # sparse, clés morning|midday|evening
min_shift_for(employee, service_id) -> float
```

- Clé absente / service inconnu → **4**.
- Valeur ≤ 0 → `ValueError` (comme aujourd’hui).
- `stretch_to_min_shift` **intouché**. Tous les `_assigned_window` ( `engine.py` + `engines/*.py` qui l’appellent ) passent `min_shift_for(employee, structure.service_id)` au lieu du scalaire. Exception : `core-2.6` pose la fenêtre telle quelle, sans étirement (`engine-core-2-6.md` gagne pour ce moteur).
- Sandbox Core (`preview_retune`, `preview_fill`, `_fill_hours`) : min = `min_shift_for` du `service_id` du créneau.
- Hydrate / banc : un **nombre** N encore lu = toutes les clés à N (compat). `4` ou omis → map vide (donc 4 partout). Ne pas réécrire `data/examples/saint-cloud.json`.
- `continuous` / chambres : hors freeze (pas de clé).

Tests : fiche `{"evening": 3}` → soir étiré à 3 h, midi reste 4 h. Nombre `3` en entrée hydrate → 3 h sur chaque service du draft. Saint-Cloud / pytest verts. `test_lower_personal_min_shift_*` adapté au map.

## Infra HTTP

`employees[].min_shift_hours` :

```
{ "morning"?: number, "midday"?: number, "evening"?: number }
```

- GET : objet, **une clé par service offert du resto**, valeur du map ou **4**. Jamais un nombre.
- PATCH / import : objet (sparse OK) **ou** nombre (compat Railway : `4` → `{}` ; autre N → les trois clés à N). Clé hors `morning|midday|evening` / valeur ≤ 0 → 400 `Champs invalides.`
- Alembic : `staff_fiches.min_shift_hours` float → JSONB. `4` → `{}` ; autre N → `{"morning":N,"midday":N,"evening":N}`.
- Export = même champ que GET (sans `invite_token`).
- Décocher un service (déjà PATCH smash) : retirer cette clé des maps de **toutes** les fiches.

## UI

Équipe : plus l’`<input type="number">` unique. **Un `Stepper` par service offert** (`CONTEXT_SERVICES.filter`, PDJ → déj → dîner), défaut 4, **`step={0.5}`**, **`min={0.5}`**. Réutiliser `web/src/Stepper.tsx` (déjà `step` / `min`). Ne pas changer le chrome des autres steppers (rôles, types, overlay). Si une prop nouvelle est indispensable, les call sites existants restent visuellement identiques.

Parser GET : objet **ou** nombre (coerce comme Infra) tant que l’API n’est pas mergée.

`web/src/release.ts` + `package.json` : **0.54.0**, note FR : `Min. créneau par service`.

## Hors freeze

Min resto-wide. Quart d’heure. `continuous`. Archive / sync. Tuer un job.
