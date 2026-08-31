# Doux Planning

Moteur de planning de restaurant : cycle de 14 jours (salle / cuisine), postes à niveaux, contraintes légales et souhaits de bien-être.

## Rapport exemple (salle)

Le cycle généré à partir du classeur *Exemple de restau* est en HTML :

**[Ouvrir le planning 14 jours](https://1mbc.github.io/doux-planning/)**

## Moteur (Python 3.12)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
