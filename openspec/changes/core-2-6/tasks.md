## Core

- [ ] 1.1 Copier `core_2.py` vers `engines/core_2_6.py` et l’enregistrer sous `core-2.6` juste après `core-2.5`. `mix-0` reste le dernier et ne l’appelle pas.
- [ ] 1.2 Contraindre les week-ends dans le modèle de repos : `even` / `odd` verrouillés, `every_two` exactement un côté, comptes A et B les plus proches possibles. Garder l’énumération et le keep-best. Repli : lâcher l’équilibrage avant les souhaits individuels.
- [ ] 1.3 Poser chaque repos de semaine restant sur le jour au surplus le plus haut, et évaluer ce calendrier avec les autres.
- [ ] 1.4 Choisir le titulaire sans étirer la fenêtre : d’abord ceux dont le minimum tient, puis ceux sous le contrat, puis le plus bas rapport heures / contrat, puis le niveau le plus proche.
- [ ] 1.5 Transférer des shifts dans un groupe de même niveau et de même contrat tant que l’écart dépasse 0,5 h et que le transfert est légal.
- [ ] 1.6 Tests du périmètre : registre, répartition 2 et 2, préférence sous contrat, dépassement si seul, ratio, transfert, surplus, fenêtre exacte y compris plus courte que le minimum. Pytest du moteur vert.
