# Classifieur de résumés de films

Ce projet construit puis met en production un classifieur binaire de résumés de films :

- `0` : comédie ;
- `1` : horreur.

Le protocole complet et le planning sont décrits dans `PLAN.md`.

## État actuel

L'audit initial des briefs, du notebook, des données et de l'environnement Windows est terminé. L'environnement Python isolé peut être créé, mais l'installation des bibliothèques lourdes attend qu'au moins 10 Gio soient libres sur le disque `C:`.

## Environnement prévu

- Windows 11 64 bits ;
- PowerShell 7 ;
- CPython 3.11 ;
- VS Code avec les extensions Python et Jupyter ;
- environnement virtuel local `.venv` ;
- noyau Jupyter `Python (modeleIA)`.

## Dépendances

- `requirements-train.txt` : notebook, entraînement et optimisation ;
- `requirements-api.txt` : inférence et FastAPI ;
- `requirements-dev.txt` : tests et barrière qualité.

Les commandes d'installation seront exécutées dans le terminal **PowerShell de VS Code** :

```powershell
python -m venv .venv
python -m pip --python .venv install --upgrade pip
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-train.txt
python -m pip install -r requirements-dev.txt
python -m ipykernel install --user --name modeleIA --display-name "Python (modeleIA)"
```

Sur ce poste, la mise à niveau de `pip` depuis l'interpréteur global est nécessaire juste après la création de la `.venv` : le `pip 22.3` fourni avec Python 3.11 ne validait pas correctement le certificat de PyPI. La commande ci-dessus installe `pip 26.2.2` dans la `.venv` sans désactiver la vérification TLS.

Contrôles prévus après installation :

```powershell
python -m pip check
python -c "import tensorflow as tf; print(tf.__version__)"
python -c "import sklearn, fastapi, keras_tuner, optuna; print('imports OK')"
```

Ne pas exécuter ces installations tant que l'espace libre recommandé n'est pas disponible.
