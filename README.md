# Classifieur de résumés de films

Ce projet construit puis met en production un classifieur binaire de résumés de films :

- `0` : comédie ;
- `1` : horreur.

Le protocole complet et le planning sont décrits dans `PLAN.md`.

## État actuel

Les huit parties du notebook sont terminées :

- audit, dédoublonnage et découpage stratifié ;
- TF-IDF sans fuite de données ;
- comparaison des modèles sur cinq graines ;
- optimisations KerasTuner et Optuna ;
- sélection du modèle avant ouverture du test ;
- campagne finale unique sur 469 exemples ;
- sauvegarde et rechargement des artefacts.

Le modèle final obtient sur le test :

- accuracy : `0,84222` ;
- précision pour la classe horreur : `0,87864` ;
- rappel pour la classe horreur : `0,78696` ;
- F1 : `0,83028`.

Le dossier `model/` contient le réseau Keras, le vectoriseur TF-IDF,
les métriques et six exemples de référence.

L’API FastAPI expose `/health` et `/predict`. Les contrôles locaux
comprennent actuellement sept tests pytest et une barrière qualité
configurable.

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

## Artefacts d’inférence

Le dossier `model/` contient :

- `model.keras` : architecture et poids du réseau ;
- `vectorizer.joblib` : vocabulaire et poids IDF ;
- `metrics.json` : version, seuil, classes et métriques ;
- `reference_sample.json` : six exemples techniques issus de
  l’apprentissage.

Les exemples de référence vérifient la reproductibilité après
rechargement. Ils ne constituent pas une mesure de généralisation.

## Lancer l’API localement

Dans un terminal PowerShell placé à la racine du projet :

```powershell
$env:APP_VERSION = (git rev-parse HEAD)
.\.venv\Scripts\python.exe -m uvicorn src.main:app `
  --host 127.0.0.1 `
  --port 8000
```

Documentation interactive :

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

État du service :

- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

`model_version` identifie les artefacts appris. `app_version` identifie
le commit Git de l’application exécutée.

## Contrat de prédiction

`POST /predict` attend :

```json
{
  "text": "Une famille découvre une présence dans une maison abandonnée."
}
```

La réponse contient la classe, son libellé, la version du modèle et une
probabilité. Cette probabilité correspond toujours à la classe
`1 = horreur`.

Le texte doit contenir entre 1 et 10 000 caractères après validation.
Les chaînes vides ou composées uniquement d’espaces sont refusées avec
le code HTTP `422`.

Le modèle ne connaît que les classes comédie et horreur. Une entrée hors
domaine sera tout de même forcée dans l’une de ces classes ; une forte
probabilité ne garantit donc pas que le texte appartient au domaine
d’entraînement.

## Tests locaux

Exécuter toute la suite :

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

La suite contrôle :

- les routes `/health` et `/predict` ;
- les entrées valide, vide et très courte ;
- le rechargement du réseau et du vectoriseur ;
- la reproduction des six prédictions de référence ;
- le passage des vraies métriques ;
- le refus d’un faux fichier de métriques insuffisant.

## Barrière qualité

Les seuils sont définis dans `config/quality_gate.yaml` :

- F1 minimal : `0.80` ;
- taille minimale du test : `400`.

Contrôle des vraies métriques :

```powershell
.\.venv\Scripts\python.exe .\scripts\check_quality.py `
  --metrics .\model\metrics.json `
  --config .\config\quality_gate.yaml
```

La barrière lit les métriques existantes sans réévaluer le test final.
Les seuils ne doivent pas être diminués pour masquer un échec.

## Docker

L’image contient uniquement le code d’inférence, les dépendances de
`requirements-api.txt` et les quatre artefacts du dossier `model/`.
L’entraînement, les notebooks, les données et pytest ne sont pas
embarqués.

Construction avec une version applicative correspondant au commit Git :

```powershell
$fullCommit = git rev-parse HEAD
$shortCommit = git rev-parse --short HEAD
$imageTag = "classifieur-films-api:$shortCommit"

docker build `
  --build-arg "APP_VERSION=$fullCommit" `
  --tag $imageTag `
  .
```

Lancement local :

```powershell
$containerName = "classifieur-films-api-test"

docker run --detach `
  --name $containerName `
  --publish 8000:8000 `
  $imageTag
```

Contrôles :

```powershell
docker inspect $containerName `
  --format 'Etat={{.State.Status}} Sante={{.State.Health.Status}}'

Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/health"
```

Arrêt et suppression du conteneur de test :

```powershell
docker stop $containerName
docker rm $containerName
```

Résultats locaux observés pour l’image `bff4277` :

- architecture : `linux/amd64` ;
- taille du contenu : environ `474 MB` ;
- utilisation disque affichée par Docker Desktop : environ `2,45 GB` ;
- état du conteneur : `running` et `healthy` ;
- résumé valide : HTTP `200` ;
- texte vide : HTTP `422` ;
- texte très court : HTTP `200`.

La preuve locale est conservée dans
`evidence/docker/local_container_verification.txt`.


## CI/CD avec GitHub Actions

Le workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) est exécuté lors des push et pull requests vers `main`, ainsi que manuellement.

La chaîne comporte trois jobs dépendants :

1. `tests` installe Python 3.11, vérifie les dépendances, exécute les tests et applique la barrière qualité.
2. `docker` construit l’image, démarre un conteneur et contrôle `/health`, une prédiction valide et le rejet d’un texte vide.
3. `publish` publie l’image dans Azure Container Registry uniquement depuis la branche `main`.

Si les tests ou la barrière qualité échouent, les jobs suivants ne sont pas exécutés. Ce comportement a été vérifié avec un seuil F1 temporairement impossible, puis le seuil normal a été restauré.

Chaque image publiée utilise le SHA Git complet comme tag. Cela permet d’associer précisément le code source, l’image et la version retournée par `/health`.

Registre utilisé :

```text
adriouchmovieacr.azurecr.io
```
