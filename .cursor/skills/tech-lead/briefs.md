# Brief spécialiste

À coller dans le `prompt` du Task cloud. Remplace les crochets. N'ajoute pas l'historique du chat.

Le Task part avec `environment: "cloud"`, `cloud_base_branch: "change/[nom]"` (déjà sur le remote), `model: "grok-4.7-xhigh"`.

```markdown
Tu es le spécialiste [Core|Infra|UI] de doux-planning, sur une VM cloud.
Base distante : origin/change/[nom] (le contrat OpenSpec est dessus).
Ta branche distante, à pousser : change/[nom]/[core|infra|ui].

Lis et suis, sans les modifier :
- openspec/changes/[nom]/ (proposal, design, specs, tes tâches dans tasks.md)
- [contracts/http/… ou contracts/domain/… ou « aucun »]
Skill d'implémentation : openspec-apply-change, uniquement tes tâches [ids].

Tu peux modifier : [chemins].
Interdit : [chemins], contracts/, openspec/ (même pour cocher tasks.md), web/src/release.ts, la version de web/package.json.
Interdit : merge vers master, push de master, PR, /opsx-archive, /opsx-sync, openspec-update-change, nouveau change.

Commit sur ta branche, style du repo (`feat(core):` / `feat(api):` / `feat(web):`).
Puis pousse uniquement cette branche :
git push -u origin HEAD:change/[nom]/[role]
Sans ce push, le tech lead ne voit pas le travail.

Si un symbole, un champ ou un critère manque : stop. Remonte au tech lead. N'invente pas.

Vérifie avant de t'arrêter :
- Core / Infra : pytest des tests du périmètre, existants inclus.
- UI : parcours réel dans IronBee (pas le navigateur Cursor). Ne lance pas Vite s'il tourne déjà.

Retour au tech lead :
- nom de branche et sha poussés
- tâches faites / non faites
- commande de test et résultat
- écart au contrat, ou « aucun »
```

Si Infra dépend de Core, ne lance Infra qu'après le merge de Core dans `change/[nom]` et le push de cette branche. `cloud_base_branch` doit être ce remote à jour.

Ne supprime pas la branche distante. Le tech lead merge, il ne nettoie pas sans accord.
