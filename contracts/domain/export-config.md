# Export / import config resto

Freeze **domaine + HTTP**. Boutons UI = brief UI ensuite.  
Pas de generate. Pas de Core nouveau (reuse persist + smash seed).

Un JSON **portable** du contexte (pas le planning). À côté du seed Saint-Cloud.  
Import = **même violence** que `POST /v1/context/seed-example`.

## Forme fichier

```
{
  export_version: 1,
  name: string,
  services: Context.services,
  ladders: Context.ladders,
  employees: Context.employees sans invite_token,
  types: Context.types,
  typical_week: Context.typical_week
}
```

**Jamais** : `company_code`, `invite_token`, `ready`, `week_labels`, `legal_context_id`, `published_cycles`, `live_sandboxes`, assignments / planning.

`export_version` entier **1**. Autre / absent → 400 `Champs invalides.`

## Export — `GET /v1/context/export`

Bearer **company**. 200 = forme ci-dessus (générée **maintenant**, pas un fichier stocké).  
Strip tokens / `company_code` même s’ils existent en base.  
Employee → 403. Sans session → 401. Sans DB → 503.

## Import — `POST /v1/context/import`

Bearer **company**. Body = forme export.  
Si `company_code` / `invite_token` / `ready` / `week_labels` / `legal_context_id` sont envoyés : **ignorer** (ne pas persister).

Smash **comme seed** :

- Écrase name, services, ladders, employees, types, typical_week (hours dérivés comme PATCH).
- Vide `published_cycles`, `live_sandboxes`, `linked_employee_ids`.
- Supprime comptes salariés / sessions **de cette** company.
- **Nouveaux** `invite_token` par fiche (ne pas réutiliser ceux du JSON).
- Garde `companies.id`, `invite_code` (`company_code`), `legal_context_id`.

200 = même `Context` que GET (tokens neufs, `company_code` **de cette** company).  
Pas de 409 fiche liée. Employee → 403. JSON / version → 400 `Champs invalides.`

## Tests

GET export : `export_version === 1` ; aucune clé `company_code` / `invite_token`.  
POST import sur company vide → GET prêt selon le JSON ; tokens ≠ ids.  
Company avec fiche liée + cycle publié → import 200, cycles nuls, linked vide, ancien salarié 401.  
`export_version: 2` → 400. Exemple public **92** inchangé. Auth verts.

## Hors freeze

Boutons UI, export planning (JSON/CSV/XLSX/JPEG), admin, coerce Railway, archive / sync.
