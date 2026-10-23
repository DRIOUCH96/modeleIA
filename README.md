# Classifieur de résumés de films

Ce projet construit puis met en production un classifieur binaire de résumés de films :

- `0` : comédie ;
- `1` : horreur.

Le protocole complet et le planning sont décrits dans `PLAN.md`.

## État actuel

L'audit initial des briefs, du notebook, des données et de l'environnement Windows est terminé. L'environnement Python isolé est créé, les dépendances sont installées et le noyau `Python (modeleIA)` est enregistré.

Le nouveau notebook reproductible contient maintenant :

- l'audit et la suppression des doublons avant découpage ;
- les lots stratifiés d'apprentissage, de test final et de production ;
- la validation interne issue des seuls 60 % d'apprentissage ;
- le TF-IDF ajusté uniquement sur l'apprentissage interne, avec contrôles des dimensions et de la mémoire.
- la comparaison sur cinq graines de la régression logistique, de Bayes naïf et d'un réseau dense de référence.
- une recherche KerasTuner de 20 essais, optimisée sur le F1 de validation interne.

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

`httpx2` est utilisé pour les tests FastAPI, conformément à la dépendance désormais recommandée par Starlette pour `TestClient`.
