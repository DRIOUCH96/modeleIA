# Compte rendu pédagogique du projet `modeleIA`

Date du compte rendu : 25 octobre 2026

Dépôt : `DRIOUCH96/modeleIA`

Branche : `main`

État couvert : du cadrage initial au premier déploiement réussi dans Azure Container Apps

Les résultats chiffrés proviennent des fichiers de preuve et des sorties réellement obtenues. Les commandes Azure dont la ligne originale n'était pas enregistrée mot pour mot sont signalées comme des commandes équivalentes utilisant les mêmes paramètres. Aucun mot de passe ni jeton secret n'est reproduit.

## 1. Le projet résumé simplement

L'objectif est de construire un service accessible sur Internet qui reçoit le résumé d'un film et répond :

- `0 = comédie` ;
- `1 = horreur`.

Le projet ne se limite pas à entraîner un modèle. Il couvre tout son trajet jusqu'à la production :

```text
CSV brut
   |
   v
Audit et dédoublonnage
   |
   v
Découpage apprentissage / test / production
   |
   v
Transformation TF-IDF
   |
   v
Comparaison et optimisation des modèles
   |
   v
Réseau final + vectoriseur + métriques
   |
   v
API FastAPI
   |
   v
Image Docker
   |
   v
GitHub Actions : tests -> image -> publication
   |
   v
Azure Container Registry
   |
   v
Azure Container Apps
   |
   v
API publique HTTPS
```

Cette chaîne est appelée un pipeline de machine learning et de MLOps :

- le **machine learning** concerne les données, les variables, les modèles et les scores ;
- le **NLP** concerne la transformation du texte en nombres ;
- le **MLOps** rend l'entraînement, les contrôles, la version, l'empaquetage et le déploiement reproductibles ;
- **Azure** héberge le registre d'images et l'API publique.

## 2. Trois versions à ne pas confondre

Le projet manipule trois identifiants différents.

### Version du modèle

```text
horror-comedy-tfidf-dnn-v1
```

Elle désigne les artefacts appris : réseau, vectoriseur, seuil et classes.

### Version de l'application

Elle correspond au SHA du commit Git utilisé pour construire l'image, par exemple :

```text
a13ec169a9e61b4fb671c5560e66d9a5ad11667f
```

Cette valeur est visible dans `GET /health` sous le nom `app_version`.

### Version de l'image Docker

Dans Azure Container Registry, le SHA Git complet sert également de tag :

```text
adriouchmovieacr.azurecr.io/classifieur-films-api:a13ec169a9e61b4fb671c5560e66d9a5ad11667f
```

Ce lien entre commit, image et réponse `/health` rend le déploiement traçable et permet un retour arrière précis.

## 3. Organisation actuelle du projet

```text
modeleIA/
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- config/
|   |-- model_selection_rule.json
|   `-- quality_gate.yaml
|-- data/
|   `-- splits/
|       `-- split_indices.json
|-- evidence/
|   |-- azure/
|   |   `-- deployment_verification.txt
|   |-- docker/
|   |   `-- local_container_verification.txt
|   `-- metrics/
|       |-- baseline_validation_runs.csv
|       |-- baseline_validation_summary.csv
|       |-- keras_tuner_best.json
|       |-- keras_tuner_trials.csv
|       |-- optuna_best.json
|       |-- optuna_trials.csv
|       |-- optimizer_validation_comparison.csv
|       |-- optimized_network_validation_runs.csv
|       |-- optimized_network_validation_summary.csv
|       |-- model_selection_decision.json
|       `-- final_test_metrics.json
|-- model/
|   |-- metrics.json
|   |-- model.keras
|   |-- reference_sample.json
|   `-- vectorizer.joblib
|-- notebooks/
|   `-- 01_pipeline_nlp.ipynb
|-- scripts/
|   `-- check_quality.py
|-- src/
|   |-- __init__.py
|   |-- inference.py
|   |-- main.py
|   `-- schemas.py
|-- tests/
|   |-- fixtures/
|   |   `-- metrics_insufficient.json
|   |-- test_api.py
|   |-- test_artifacts.py
|   `-- test_quality_gate.py
|-- .dockerignore
|-- .gitattributes
|-- .gitignore
|-- Dockerfile
|-- PLAN.md
|-- README.md
|-- requirements-api.txt
|-- requirements-dev.txt
|-- requirements-train.txt
|-- textes_films_horreur_comedie.csv
|-- tp7_texte_nlp.ipynb
|-- c12-fiche-planifier-le-projet-6ad934865387c314988957.pdf
`-- suite-deploiement-pipeline-production-1-6ad92fa254ca6782626714.pdf
```

Les dossiers locaux suivants existent aussi, mais ils sont ignorés par Git :

- `.venv/` : environnement Python local ;
- `.pytest_cache/` : cache de pytest ;
- `keras_tuner/` : état local de la recherche KerasTuner ;
- `tmp/` : fichiers temporaires.

## 4. Étape 1 — Cadrage et préparation de l'environnement

### Objectif

Avant de coder, nous avons comparé :

- les exigences du nouveau brief ;
- le notebook existant `tp7_texte_nlp.ipynb` ;
- les données CSV ;
- les exigences de planification C12.

Le notebook existant contenait des éléments réutilisables, mais son protocole n'était pas conforme au nouveau brief. Il utilisait notamment un ancien découpage 75/25 et des résultats calculés avant dédoublonnage. Ces anciens scores ne pouvaient donc pas être présentés comme les résultats du nouveau projet.

### Fichiers créés ou préparés

- `PLAN.md` : exigences, tâches, dépendances, charges et preuves attendues ;
- `README.md` : point d'entrée documentaire ;
- `requirements-train.txt` : dépendances du notebook et de l'entraînement ;
- `requirements-api.txt` : dépendances minimales de l'inférence ;
- `requirements-dev.txt` : dépendances des tests et contrôles ;
- `.gitignore` : exclusion des environnements, caches, secrets et sorties locales ;
- `.gitattributes` : normalisation des fins de ligne et déclaration des fichiers binaires.

### Pourquoi trois fichiers de dépendances ?

L'entraînement utilise `pandas`, `matplotlib`, KerasTuner, Optuna et Jupyter. L'API de production n'a pas besoin de tous ces outils. Séparer les dépendances :

- réduit l'image Docker ;
- diminue la surface d'erreur ;
- distingue clairement entraînement, inférence et tests.

### Versions fixées

Principales versions utilisées :

- Python 3.11 ;
- NumPy 2.4.6 ;
- pandas 3.1.0 ;
- scikit-learn 1.9.1 ;
- TensorFlow CPU 2.21.0 ;
- TensorBoard 2.21.0 ;
- KerasTuner 1.4.8 ;
- Optuna 5.0.0 ;
- FastAPI 0.161.1 ;
- Uvicorn 0.54.0 ;
- pytest 9.1.1.

### Commandes PowerShell d'installation

À exécuter depuis la racine du projet :

```powershell
python --version
git --version

python -m venv .venv
python -m pip --python .venv install --upgrade pip
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements-train.txt
python -m pip install -r requirements-dev.txt

python -m ipykernel install `
  --user `
  --name modeleIA `
  --display-name "Python (modeleIA)"
```

Contrôles :

```powershell
python -m pip check
python -c "import tensorflow as tf; print(tf.__version__)"
python -c "import tensorboard; print(tensorboard.__version__)"
python -c "import sklearn, fastapi, keras_tuner, optuna; print('imports OK')"
```

Résultats observés :

- environ 74,53 Gio étaient disponibles ;
- TensorBoard répondait en version `2.21.0` ;
- `pip check` a répondu `No broken requirements found`.

Une incompatibilité importante a été constatée plus tard : le terminal utilisé se comporte comme Windows PowerShell 5.1, car `Invoke-WebRequest -SkipHttpErrorCheck` n'est pas disponible. Les commandes de test HTTP ont donc été adaptées avec `try/catch`.

### Premier jalon Git

```text
8f2b724 chore: cadrer le projet et préparer l'environnement
```

## 5. Étape 2 — Audit et nettoyage des données

### Objectif

Un modèle apprend ce qu'on lui fournit. Avant tout découpage, il fallait vérifier que les données étaient cohérentes et éviter qu'une même ligne apparaisse dans plusieurs lots.

### Données initiales observées

- 2 400 lignes ;
- 3 colonnes : `titre`, `resume`, `cible` ;
- 1 200 comédies et 1 200 horreurs ;
- aucune valeur manquante ;
- aucun titre ou résumé vide après retrait des espaces de bord ;
- 54 occurrences dupliquées à supprimer ;
- 51 groupes de doublons : 48 paires et 3 triplets ;
- aucun résumé identique associé à deux étiquettes contradictoires.

Longueur des résumés :

- médiane : 474 caractères et 82 mots ;
- minimum : 201 caractères ;
- maximum : 7 104 caractères.

### Nettoyage obtenu

Les doublons exacts ont été supprimés avec :

```python
df_clean = (
    df_raw.drop_duplicates(
        subset=["titre", "resume", "cible"],
        keep="first",
    )
    .reset_index(drop=True)
    .copy()
)
```

Résultat :

- 2 346 lignes conservées ;
- 1 195 comédies ;
- 1 151 horreurs.

### Pourquoi supprimer les doublons avant le découpage ?

Si le dédoublonnage était réalisé séparément après le découpage, une occurrence pourrait se trouver dans l'apprentissage et une autre dans la validation ou le test. Le modèle aurait alors déjà vu presque exactement la réponse attendue. Le score serait artificiellement élevé : c'est une **fuite de données**.

Le nettoyage global avant découpage garantit qu'une observation logique n'appartient qu'à un seul lot.

### Jalon Git

```text
9a88599 feat: auditer les donnees et preparer le TF-IDF
```

## 6. Étape 3 — Découpage reproductible des données

### Objectif

Les 2 346 lignes nettoyées ont été réparties comme demandé :

- 60 % pour l'apprentissage : 1 407 lignes ;
- 20 % pour le test final : 469 lignes ;
- 20 % pour le lot de production : 470 lignes.

Le découpage utilise :

```python
train_test_split(..., random_state=42, stratify=...)
```

`random_state=42` rend le découpage reproductible. `stratify` conserve approximativement la proportion de comédies et d'horreurs dans chaque lot.

### Validation interne

Les 60 % d'apprentissage ont ensuite été séparés en :

- apprentissage interne : 1 125 lignes ;
- validation interne : 282 lignes.

La validation interne a servi à comparer les modèles et choisir les hyperparamètres. Le test final n'a pas été utilisé pendant ces choix.

### Rôle de chaque lot

| Lot | Rôle | Autorisé pour choisir les hyperparamètres ? |
|---|---|---:|
| Apprentissage interne | Apprendre les paramètres du modèle | Oui, indirectement |
| Validation interne | Comparer les choix et hyperparamètres | Oui |
| Test final | Mesurer une seule fois la généralisation finale | Non |
| Production holdout | Lot scellé, conservé pour un usage futur | Non |

Les indices ont été enregistrés dans `data/splits/split_indices.json`, avec la graine et l'empreinte SHA-256 du CSV. Cela permet de reconstruire exactement les mêmes lots.

## 7. Étape 4 — Transformation TF-IDF

### Pourquoi transformer le texte ?

Un modèle numérique ne lit pas directement des phrases. TF-IDF transforme chaque résumé en un vecteur de nombres.

Chaque colonne représente un terme ou un groupe de termes. Chaque ligne représente un résumé.

### Intuition mathématique

Pour un terme `t` dans un document `d` :

```text
TF-IDF(t,d) = TF(t,d) x IDF(t)
```

- `TF` mesure la présence du terme dans le document ;
- `IDF` réduit le poids des termes présents dans beaucoup de documents ;
- un terme fréquent dans un document, mais rare dans le corpus, reçoit un poids important.

Avec le réglage `sublinear_tf=True`, scikit-learn applique une forme logarithmique du TF. Cela évite qu'un mot répété dix fois pèse dix fois plus qu'un mot présent une seule fois.

### Paramètres utilisés

```python
TFIDF_PARAMS = {
    "lowercase": True,
    "strip_accents": "unicode",
    "ngram_range": (1, 2),
    "min_df": 2,
    "max_df": 0.95,
    "max_features": 10_000,
    "sublinear_tf": True,
    "norm": "l2",
    "dtype": np.float32,
}
```

Interprétation :

- minuscules et normalisation des accents ;
- mots seuls et groupes de deux mots ;
- exclusion des termes vus dans moins de deux documents ;
- exclusion des termes présents dans plus de 95 % des documents ;
- vocabulaire limité à 10 000 variables ;
- nombres en `float32` ;
- normalisation L2 de chaque ligne.

### Règle contre la fuite de données

```python
X_train_internal = vectorizer.fit_transform(train_internal["resume"])
X_validation_internal = vectorizer.transform(validation_internal["resume"])
```

`fit_transform` est utilisé uniquement sur l'apprentissage, car `fit` apprend le vocabulaire et les poids IDF. La validation est seulement transformée avec ce qui a déjà été appris.

Si nous utilisions `fit_transform` sur la validation, elle influencerait le vocabulaire et les poids IDF. Le modèle disposerait d'informations provenant du lot censé l'évaluer.

### Matrice creuse et matrice dense

Un résumé n'utilise qu'une petite partie des 10 000 termes. Une matrice creuse stocke principalement les positions non nulles. Une matrice dense réserve de la mémoire pour chaque valeur, y compris les milliers de zéros.

Exemple pour l'apprentissage interne :

```text
1 125 lignes x 10 000 colonnes x 4 octets
= 45 000 000 octets
= environ 42,9 Mio
```

La conversion en dense a été faite uniquement pour les réseaux Keras, qui utilisaient ces tableaux. La régression logistique et Bayes naïf ont conservé les matrices creuses.

## 8. Étape 5 — Comparaison des modèles de référence

### Modèles comparés

Trois modèles ont été évalués :

1. régression logistique ;
2. Bayes naïf multinomial ;
3. petit réseau dense avec ReLU, dropout et régularisation L2.

Les graines utilisées étaient :

```text
11, 22, 33, 44, 55
```

### Résultats moyens sur la validation interne

| Modèle | F1 moyen | Écart-type du F1 |
|---|---:|---:|
| Réseau dense de référence | 0,871971 | 0,006885 |
| Bayes naïf multinomial | 0,836502 | 0,000000 |
| Régression logistique | 0,827068 | 0,000000 |

### Pourquoi certains modèles donnent exactement le même F1 sur cinq graines ?

Ce n'est pas une erreur. Dans la configuration utilisée :

- Bayes naïf ne comporte pas de tirage aléatoire ;
- le solveur `liblinear` de la régression logistique produit ici le même résultat ;
- le réseau initialise des poids aléatoires et varie donc légèrement selon la graine.

### Pourquoi comparer moyenne et écart-type ?

Retenir seulement la meilleure exécution favoriserait un coup de chance. La moyenne estime la performance typique. L'écart-type mesure la stabilité.

Un modèle légèrement meilleur une fois, mais très instable, peut être moins fiable qu'un modèle presque aussi bon et beaucoup plus stable.

### Métriques utilisées

Pour la classe positive `1 = horreur` :

```text
precision = vrais positifs / (vrais positifs + faux positifs)
recall    = vrais positifs / (vrais positifs + faux négatifs)
F1        = 2 x precision x recall / (precision + recall)
accuracy  = prédictions correctes / toutes les prédictions
```

Le F1 est la métrique principale, car il équilibre précision et rappel.

### Jalon Git

```text
79f8667 feat: comparer les modeles de reference
```

## 9. Étape 6 — Optimisation avec KerasTuner

### Architecture commune

La fonction `build_dense_network` crée :

- une entrée de taille 10 000 ;
- une à trois couches denses ;
- activation ReLU ;
- dropout après chaque couche ;
- régularisation L2 ;
- une sortie unique avec sigmoïde ;
- optimisation Adam ;
- perte d'entropie croisée binaire.

La sigmoïde produit une valeur entre 0 et 1, interprétée ici comme la probabilité de la classe `1 = horreur`. Le seuil de décision est `0,50`.

### Espace exploré

| Hyperparamètre | Valeurs |
|---|---|
| Nombre de couches | 1, 2, 3 |
| Neurones par couche | 32, 64, 128 |
| Dropout | 0,10 ; 0,30 ; 0,50 |
| L2 | 0,00001 ; 0,0001 ; 0,001 |
| Taux d'apprentissage | 0,0001 ; 0,0003 ; 0,001 ; 0,003 |

KerasTuner a exécuté 20 essais aléatoires, avec au maximum 15 époques et un early stopping.

Meilleure configuration observée :

```text
2 couches
128 neurones par couche
dropout = 0,50
L2 = 0,001
learning rate = 0,001
F1 validation recalculé = 0,880546
```

Fichiers de preuve :

- `evidence/metrics/keras_tuner_trials.csv` ;
- `evidence/metrics/keras_tuner_best.json`.

### Jalon Git

```text
a950824 feat: optimiser le reseau avec KerasTuner
```

## 10. Étape 7 — Optimisation comparable avec Optuna

Optuna a utilisé :

- le même constructeur de réseau ;
- les mêmes données ;
- le même espace d'hyperparamètres ;
- le même objectif F1 ;
- le même budget de 20 essais ;
- un échantillonneur TPE avec cinq essais initiaux.

Meilleure configuration observée lors de la recherche :

```text
3 couches
64 neurones par couche
dropout = 0,50
L2 = 0,001
learning rate = 0,003
F1 validation recalculé = 0,888889
```

Optuna a donc trouvé le meilleur **essai isolé**, mais cela ne suffisait pas pour déclarer son architecture gagnante. Il fallait ensuite tester la stabilité des deux architectures sur cinq graines.

Fichiers de preuve :

- `evidence/metrics/optuna_trials.csv` ;
- `evidence/metrics/optuna_best.json` ;
- `evidence/metrics/optimizer_validation_comparison.csv`.

### Jalons Git

```text
b365c12 feat: optimiser le reseau avec Optuna
7c18618 docs: enregistrer les sorties Optuna
```

## 11. Étape 8 — Décision figée avant le test final

### Pourquoi figer une règle ?

Si nous regardions le test final puis changions de modèle, de graine, de seuil ou d'époques, le test deviendrait lui-même un jeu de réglage. Son score ne serait plus une estimation honnête de généralisation.

La règle a donc été écrite avant l'ouverture du test dans `config/model_selection_rule.json`.

### Comparaison robuste des architectures optimisées

| Architecture | F1 moyen | Écart-type | Paramètres |
|---|---:|---:|---:|
| KerasTuner | 0,870709 | 0,005282 | 1 296 769 |
| Optuna | 0,866647 | 0,012315 | 648 449 |

L'écart des moyennes vaut environ `0,004062`, inférieur à la tolérance pratique fixée à `0,005`. Les modèles ont donc été considérés comme pratiquement ex aequo sur leur moyenne.

La règle départage alors par la stabilité : l'architecture KerasTuner a l'écart-type le plus faible. Elle a donc été retenue.

Choix figés :

```text
Architecture : keras_tuner_optimized_network
Graine       : 11
Époques      : 6
Seuil        : 0,50
```

La graine 11 n'a pas été choisie parce qu'elle était la meilleure sur le test. Elle était l'exécution de validation la plus proche de la moyenne de l'architecture retenue. Le nombre de six époques correspond à la médiane des meilleures époques observées.

Fichiers de preuve :

- `evidence/metrics/optimized_network_validation_runs.csv` ;
- `evidence/metrics/optimized_network_validation_summary.csv` ;
- `evidence/metrics/model_selection_decision.json`.

### Jalons Git avant le test

```text
f82199a chore: figer la regle de selection avant le test
032ffd9 docs: enregistrer la decision du modele avant le test
fb49780 chore: figer la campagne de test final
```

Le commit enregistré juste avant la campagne finale était :

```text
fb49780e4b9eb6f5fd91fb42ffabc865603f6f26
```

## 12. Étape 9 — Campagne finale unique

### Réentraînement final

Après la décision, le vectoriseur a été réappris sur les 1 407 lignes du lot d'apprentissage complet. Le test final a seulement été transformé.

Dimensions :

```text
Apprentissage final : (1407, 10000)
Test final           : (469, 10000)
Paramètres réseau    : 1 296 769
Époques              : 6
```

### Résultats réellement obtenus

| Métrique | Valeur |
|---|---:|
| Accuracy | 0,842217 |
| Précision horreur | 0,878641 |
| Rappel horreur | 0,786957 |
| F1 | 0,830275 |

Matrice de confusion :

| | Prédit comédie | Prédit horreur |
|---|---:|---:|
| Réel comédie | 214 | 25 |
| Réel horreur | 49 | 181 |

Interprétation :

- 214 comédies ont été correctement reconnues ;
- 181 films d'horreur ont été correctement reconnus ;
- 25 comédies ont été prises pour des films d'horreur ;
- 49 films d'horreur ont été pris pour des comédies.

La marge pédagogique demandée est :

```text
1,96 x racine(F1 x (1 - F1) / n) = environ 0,0340
```

Elle ne constitue pas automatiquement un intervalle de confiance statistiquement valide du F1. Elle a été conservée parce que le brief la demandait, tout en documentant cette limite.

Le lot de production de 470 lignes est toujours scellé et n'a pas été évalué.

### Jalon Git

```text
c524874 feat: evaluer le modele sur le test final
```

## 13. Étape 10 — Sauvegarde des artefacts

Le dossier `model/` contient le paquet autonome nécessaire à l'inférence.

### `model/model.keras`

Architecture et poids du réseau final. L'optimiseur Adam a été exclu de l'artefact d'inférence, car il n'est nécessaire que pour poursuivre l'entraînement.

Cette correction a réduit le fichier d'environ 14,869 Mio à 4,969 Mio.

### `model/vectorizer.joblib`

Contient le vocabulaire TF-IDF et les poids IDF appris sur les 1 407 lignes d'apprentissage final. Sa taille est d'environ 0,325 Mio.

### `model/metrics.json`

Contient notamment :

- la version du modèle ;
- le mapping `0 = comédie`, `1 = horreur` ;
- le seuil 0,50 ;
- les hyperparamètres ;
- les métriques finales ;
- les tailles des lots ;
- les commits de traçabilité.

### `model/reference_sample.json`

Contient six exemples techniques : trois par classe, choisis dans le lot d'apprentissage sans regarder les prédictions. Ils servent uniquement à vérifier que le modèle rechargé reproduit les mêmes sorties.

Résultat du contrôle :

```text
Échantillons vérifiés        : 6
Écart maximal de probabilité : 0.0000000000
Rechargement                 : OK
```

### Jalons Git

```text
28fdcdf chore: preparer la sauvegarde des artefacts
93a143c fix: exclure l optimiseur de l artefact keras
6e0c752 feat: sauvegarder et verifier les artefacts du modele
```

## 14. Étape 11 — API FastAPI

### Organisation du code

- `src/inference.py` charge et vérifie les quatre artefacts, transforme le texte et calcule la prédiction ;
- `src/schemas.py` définit et valide les objets HTTP ;
- `src/main.py` crée l'application et expose les routes.

### Chargement unique

Le réseau et le vectoriseur sont chargés dans le `lifespan` de FastAPI au démarrage. Ils ne sont pas relus depuis le disque à chaque appel.

### Routes

#### `GET /health`

Retourne :

- l'état du service ;
- si le modèle est chargé ;
- la version du modèle ;
- la version de l'application.

#### `POST /predict`

Attend un JSON :

```json
{
  "text": "Une famille découvre une présence dans une maison abandonnée."
}
```

Retourne la classe, le libellé, la probabilité et la version du modèle.

La clé `probability` correspond **toujours à la classe 1, horreur**, même lorsque la classe prédite vaut 0. Exemple : une probabilité de `0,41` signifie 41 % pour horreur ; comme elle est inférieure à 0,50, la prédiction est comédie.

### Validation des entrées

- taille de 1 à 10 000 caractères ;
- retrait des espaces de bord ;
- rejet des chaînes vides ou composées uniquement d'espaces ;
- rejet des champs JSON supplémentaires.

### Limite importante

Le modèle ne connaît que deux classes. Un texte hors domaine, par exemple une recette ou une actualité sportive, sera quand même forcé vers comédie ou horreur. Une probabilité élevée ne prouve pas que l'entrée est réellement un résumé de film.

### Commande de lancement local

Terminal PowerShell, à la racine :

```powershell
$env:APP_VERSION = (git rev-parse HEAD)

.\.venv\Scripts\python.exe -m uvicorn src.main:app `
  --host 127.0.0.1 `
  --port 8000
```

Adresses :

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

La route `/` n'a pas été créée. Un `GET /` qui retourne 404 est donc normal. Un `GET /predict` retourne 405, car cette route exige `POST`.

### Tests manuels PowerShell

Santé :

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/health"
```

Prédiction valide :

```powershell
$body = @{
  text = "Une famille découvre une présence terrifiante dans une maison."
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/predict" `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

Entrée vide sous Windows PowerShell 5.1 :

```powershell
try {
  Invoke-WebRequest `
    -Method Post `
    -Uri "http://127.0.0.1:8000/predict" `
    -ContentType "application/json" `
    -Body '{"text":"   "}' `
    -UseBasicParsing
} catch {
  Write-Output "HTTP $([int]$_.Exception.Response.StatusCode)"
}
```

Résultat attendu : `HTTP 422`.

### Jalon Git

```text
6c4753e feat: ajouter l api d inference
```

## 15. Étape 12 — Tests automatisés et barrière qualité

### Sept tests pytest

`tests/test_api.py` contrôle :

1. les deux versions retournées par `/health` ;
2. une prédiction valide ;
3. le rejet d'un texte vide ;
4. l'acceptation du cas limite très court `"x"`.

`tests/test_artifacts.py` recharge les artefacts et reproduit les six prédictions de référence.

`tests/test_quality_gate.py` contrôle :

1. que les vraies métriques passent ;
2. qu'un faux fichier insuffisant échoue sans modifier les vraies métriques.

Commande :

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Résultat final observé :

```text
7 passed
```

### Barrière qualité

`config/quality_gate.yaml` contient :

```yaml
quality_gate:
  minimum_f1: 0.80
  minimum_test_rows: 400
```

La commande suivante lit les métriques sauvegardées ; elle ne réévalue pas le test final :

```powershell
.\.venv\Scripts\python.exe .\scripts\check_quality.py `
  --metrics .\model\metrics.json `
  --config .\config\quality_gate.yaml
```

Résultat réel :

```text
F1 : 0.830275 (minimum 0.800000) -> OK
Taille du test : 469 (minimum 400) -> OK
Barrière qualité : OK
Code de sortie : 0
```

Le faux fichier de test contient un F1 de 0,60 et seulement 20 lignes. Il produit le code de sortie 1.

Codes du script :

- `0` : qualité acceptée ;
- `1` : métriques valides, mais seuils non atteints ;
- `2` : fichier ou structure invalide.

### Jalons Git

```text
92e449f test: couvrir les routes de l api
b0109ae test: ajouter la barriere qualite
08f8ca6 test: verifier le rechargement des artefacts
56da0a8 docs: documenter l api et les controles qualite
```

## 16. Étape 13 — Conteneurisation Docker

### Concepts

- une **image** est un paquet immuable contenant le code, Python, les dépendances et les artefacts ;
- un **conteneur** est une exécution d'une image ;
- le port interne 8000 est publié vers le port 8000 de la machine ;
- `APP_VERSION` est injecté pendant la construction.

### Incident initial

La CLI Docker était installée, mais le moteur Docker Desktop n'était pas démarré. Les commandes renvoyaient une erreur sur :

```text
npipe:////./pipe/dockerDesktopLinuxEngine
```

Après le démarrage de Docker Desktop, le client et le serveur ont répondu correctement.

### Dockerfile

Le `Dockerfile` :

- part de `python:3.11-slim-bookworm` ;
- installe seulement `requirements-api.txt` ;
- copie seulement `src/` et `model/` ;
- exécute le service avec un utilisateur non privilégié `appuser` ;
- expose le port 8000 ;
- définit un healthcheck sur `/health` ;
- lance Uvicorn sur `0.0.0.0:8000`.

Le `.dockerignore` commence par exclure tout le contexte, puis réautorise seulement les fichiers nécessaires. Les données, notebooks, tests et outils d'entraînement ne sont pas envoyés dans l'image.

### Construction

```powershell
$fullCommit = git rev-parse HEAD
$shortCommit = git rev-parse --short HEAD
$imageTag = "classifieur-films-api:$shortCommit"

docker build `
  --build-arg "APP_VERSION=$fullCommit" `
  --tag $imageTag `
  .
```

### Lancement

```powershell
$containerName = "classifieur-films-api-test"

docker run --detach `
  --name $containerName `
  --publish 8000:8000 `
  $imageTag
```

### Vérifications

```powershell
docker inspect $containerName `
  --format 'Etat={{.State.Status}} Sante={{.State.Health.Status}}'

Invoke-RestMethod `
  -Method Get `
  -Uri "http://127.0.0.1:8000/health"

docker logs $containerName
```

Résultats de l'image `bff4277` :

- image Linux `amd64` ;
- contenu d'environ 474 Mo ;
- utilisation disque affichée par Docker Desktop d'environ 2,45 Go ;
- conteneur `running` et `healthy` ;
- santé : HTTP 200 ;
- prédiction valide : HTTP 200 ;
- texte vide : HTTP 422 ;
- texte très court : HTTP 200.

### Nettoyage du conteneur de test

```powershell
docker stop $containerName
docker rm $containerName

docker ps --all --filter "name=$containerName"
docker image ls classifieur-films-api
```

Le conteneur a été supprimé ; l'image locale a été conservée.

### Preuve et jalons Git

```text
evidence/docker/local_container_verification.txt

bff4277 build: ajouter l image Docker de l api
2d071ff docs: enregistrer la validation Docker locale
```

## 17. Étape 14 — Dépôt GitHub et intégration continue

### Création du dépôt privé

GitHub CLI a été installé puis authentifié avec le compte `DRIOUCH96`.

Contrôles :

```powershell
gh --version
gh auth status
```

Création et premier push :

```powershell
gh repo create DRIOUCH96/modeleIA `
  --private `
  --source . `
  --remote origin `
  --push
```

Vérification :

```powershell
gh repo view DRIOUCH96/modeleIA `
  --json nameWithOwner,visibility,defaultBranchRef,url
```

Le dépôt est privé et sa branche par défaut est `main`.

### Workflow `.github/workflows/ci.yml`

Le workflow se déclenche :

- sur les push vers `main` ;
- sur les pull requests vers `main` ;
- manuellement avec `workflow_dispatch`.

#### Job 1 — Tests et barrière qualité

Il :

1. récupère le dépôt ;
2. installe Python 3.11 ;
3. installe `requirements-dev.txt` ;
4. exécute `pip check` ;
5. exécute pytest ;
6. applique explicitement la barrière qualité.

#### Job 2 — Construction et test Docker

Il dépend du job 1 avec `needs: tests`. Il ne démarre donc pas si les tests échouent.

Il :

1. construit l'image avec `GITHUB_SHA` comme `APP_VERSION` ;
2. démarre un conteneur ;
3. attend que `/health` soit disponible ;
4. vérifie que `/health` expose le bon SHA ;
5. teste une prédiction valide ;
6. vérifie le rejet du texte vide ;
7. affiche les logs en cas d'échec ;
8. supprime toujours le conteneur.

#### Job 3 — Publication dans Azure Container Registry

Il dépend du job Docker et s'exécute seulement pour un push sur `main`, jamais sur une pull request.

Il :

1. se connecte à ACR ;
2. reconstruit l'image avec le SHA complet ;
3. pousse l'image ;
4. vérifie son manifeste.

### Expérience rouge puis verte

Le seuil F1 a temporairement été porté de `0,80` à `0,99`.

Résultat :

- le job de tests est devenu rouge ;
- le F1 réel `0,830275` n'atteignait pas `0,99` ;
- le job Docker n'a pas été exécuté ;
- le pipeline a renvoyé un échec.

Le commit expérimental était :

```text
e6bdcef test: provoquer l echec de la barriere qualite
```

Il a ensuite été annulé :

```text
b611886 Revert "test: provoquer l echec de la barriere qualite"
```

Le seuil est revenu à `0,80` et la CI est redevenue verte. Cette expérience prouve que la barrière bloque réellement les étapes suivantes.

### Commandes de suivi

```powershell
$commit = git rev-parse HEAD

gh run list `
  --workflow "CI" `
  --commit $commit `
  --limit 1

$runId = gh run list `
  --workflow "CI" `
  --commit $commit `
  --limit 1 `
  --json databaseId `
  --jq '.[0].databaseId'

gh run watch $runId --exit-status
```

### Jalons Git

```text
fd58d3c ci: ajouter les tests et la barriere qualite
b827921 ci: construire et tester l image Docker
e6bdcef test: provoquer l echec de la barriere qualite
b611886 Revert "test: provoquer l echec de la barriere qualite"
```

## 18. Étape 15 — Azure Container Registry

### Vérification du compte Azure

Azure CLI répondait en version 2.91.0.

```powershell
az version
az account show --output json
```

Abonnement utilisé :

```text
ARA_Bourg-en-B_DataEng_207803_INT_SWS
```

Groupe de ressources existant et réutilisé :

```text
adriouchRG
```

Le groupe n'a pas été créé uniquement pour ce projet. Il ne devra donc jamais être supprimé en bloc lors de la fin de vie.

### Registre créé

```text
Nom     : adriouchmovieacr
Serveur : adriouchmovieacr.azurecr.io
SKU     : Basic
Admin   : désactivé
```

Commande de création utilisée dans son principe :

```powershell
az acr create `
  --name adriouchmovieacr `
  --resource-group adriouchRG `
  --location francecentral `
  --sku Basic `
  --admin-enabled false
```

### Première tentative : identité fédérée OIDC

Une identité `github-modeleia-acr-push` et une fédération GitHub `github-main` ont été créées. L'affectation du rôle ACR a échoué : le compte utilisateur n'avait pas le droit `Microsoft.Authorization/roleAssignments/write`.

Cette identité n'a donc aucun rôle utile et n'est pas utilisée par le pipeline. Elle devra être supprimée plus tard après confirmation explicite.

### Solution retenue : jetons ACR limités au dépôt

Au lieu d'activer l'administrateur général du registre, deux jetons à privilèges minimaux ont été créés :

#### Publication depuis GitHub Actions

```text
Jeton : github-modeleia-push
Droits : content/read et content/write
Dépôt : classifieur-films-api uniquement
```

#### Lecture depuis Azure Container Apps

```text
Jeton : adriouch-modeleia-pull
Droits : content/read
Dépôt : classifieur-films-api uniquement
```

Exemple de création du scope de publication :

```powershell
az acr scope-map create `
  --name github-modeleia-push-scope-map `
  --registry adriouchmovieacr `
  --resource-group adriouchRG `
  --repository classifieur-films-api content/read content/write

az acr token create `
  --name github-modeleia-push `
  --registry adriouchmovieacr `
  --resource-group adriouchRG `
  --scope-map github-modeleia-push-scope-map
```

Le mot de passe a été généré pour 90 jours avec l'emplacement `password1`. Sa valeur n'a jamais été ajoutée au dépôt ni affichée dans le compte rendu.

### Variables et secret GitHub

Variables non secrètes :

```powershell
gh variable set ACR_IMAGE_NAME `
  --body "classifieur-films-api" `
  --repo DRIOUCH96/modeleIA

gh variable set ACR_LOGIN_SERVER `
  --body "adriouchmovieacr.azurecr.io" `
  --repo DRIOUCH96/modeleIA

gh variable set ACR_USERNAME `
  --body "github-modeleia-push" `
  --repo DRIOUCH96/modeleIA
```

Secret :

```powershell
$acrSecretValue | gh secret set ACR_PASSWORD `
  --repo DRIOUCH96/modeleIA
```

La variable PowerShell contenait temporairement la valeur, mais celle-ci n'a pas été écrite dans Git ni dans la conversation.

### Incident et correction

Le premier job de publication a échoué avec `Password required`, car Azure n'avait pas retourné de mot de passe avec la première variante de commande. La génération a été corrigée avec l'option `--password1`, puis le secret GitHub a été remplacé.

Le run GitHub Actions `40143248993` a ensuite réussi.

Image validée et publiée :

```text
Tag    : a13ec169a9e61b4fb671c5560e66d9a5ad11667f
Digest : sha256:903f36cc6f3ddc436cc75505ed6641c80fa372675e3d446aab4151f6aeff4674
```

### Jalon Git

```text
a13ec16 ci: publier l image dans Azure Container Registry
```

## 19. Étape 16 — Déploiement manuel dans Azure Container Apps

### Préparation Azure

L'extension Container Apps et le fournisseur Azure ont été contrôlés :

```powershell
az extension add --name containerapp --upgrade

az provider register `
  --namespace Microsoft.App `
  --wait
```

Version observée de l'extension : `1.3.0b5`.

### Environnement Container Apps

Un environnement regroupe les Container Apps et leur réseau d'exécution.

```text
Nom     : adriouch-modeleia-env
Région  : France Central
Domaine : niceforest-29b9ca50.francecentral.azurecontainerapps.io
```

Commande :

```powershell
az containerapp env create `
  --name adriouch-modeleia-env `
  --resource-group adriouchRG `
  --location francecentral `
  --logs-destination none
```

`--logs-destination none` signifie qu'aucun espace Log Analytics dédié n'a été créé. Les logs directs du conteneur restent consultables, mais il n'y a pas de conservation centralisée longue durée dans cette configuration.

### Application déployée

```text
Nom          : adriouch-modeleia-api
Image        : adriouchmovieacr.azurecr.io/classifieur-films-api:a13ec169...
CPU          : 1 vCPU
Mémoire      : 2 Gio
Ingress      : externe
Port cible   : 8000
Minimum      : 0 réplique
Maximum      : 1 réplique
Mode révision: single
```

Une commande équivalente à celle utilisée est :

```powershell
$deployedCommit = "a13ec169a9e61b4fb671c5560e66d9a5ad11667f"
$imageUri = "adriouchmovieacr.azurecr.io/classifieur-films-api:$deployedCommit"

az containerapp create `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG `
  --environment adriouch-modeleia-env `
  --image $imageUri `
  --registry-server "adriouchmovieacr.azurecr.io" `
  --registry-username "adriouch-modeleia-pull" `
  --registry-password $pullPassword `
  --ingress external `
  --target-port 8000 `
  --transport auto `
  --cpu 1.0 `
  --memory 2Gi `
  --min-replicas 0 `
  --max-replicas 1
```

Le mot de passe de lecture est fourni à la commande depuis une variable temporaire. Il ne doit pas être placé en clair dans un fichier ou dans Git.

### Résultat

```text
FQDN : adriouch-modeleia-api.niceforest-29b9ca50.francecentral.azurecontainerapps.io
Révision : adriouch-modeleia-api--2dwkro0
État : Running
```

URL de santé :

```text
https://adriouch-modeleia-api.niceforest-29b9ca50.francecentral.azurecontainerapps.io/health
```

### Tests publics

```powershell
$baseUrl = "https://adriouch-modeleia-api.niceforest-29b9ca50.francecentral.azurecontainerapps.io"

Invoke-RestMethod `
  -Method Get `
  -Uri "$baseUrl/health"
```

Résultat :

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_version": "horror-comedy-tfidf-dnn-v1",
  "app_version": "a13ec169a9e61b4fb671c5560e66d9a5ad11667f"
}
```

Prédiction valide observée :

```text
HTTP                 : 200
Classe               : 0
Libellé              : comédie
Probabilité horreur  : 0,4133169055
```

Entrée vide observée :

```text
HTTP 422
```

L'affichage `comÃ©die` dans une console était un problème d'encodage d'affichage de PowerShell, pas une erreur du JSON de l'API.

### Scale-to-zero

`minimum = 0` permet à Azure d'arrêter toutes les répliques lorsqu'il n'y a pas de trafic. Cela limite la consommation, mais la première requête après une période d'inactivité peut être plus lente, car le conteneur et TensorFlow doivent redémarrer.

### Preuve

```text
evidence/azure/deployment_verification.txt
```

Ce fichier relie :

- le run GitHub Actions ;
- le F1 et la barrière qualité ;
- l'image et son digest ;
- l'environnement et la révision Azure ;
- les trois contrôles publics.

## 20. Étape 17 — Documentation du déploiement

Les sections CI/CD et Azure ont été ajoutées au `README.md`. La preuve Azure a été ajoutée au dépôt.

Jalon :

```text
8f495eb docs: documenter le deploiement Azure
```

Le run CI `40204510835` associé à ce commit a réussi sur les trois jobs.

Ce commit documentaire a aussi produit une image ACR portant le tag `8f495eb...`, car le workflow publie actuellement une image à chaque push sur `main`. Cette image n'a pas été déployée. L'application Azure reste volontairement sur `a13ec169...`, qui constitue la première version de production validée.

## 21. Historique chronologique des commits

| Commit | Rôle |
|---|---|
| `8f2b724` | Cadrage, environnement, plan et dépendances |
| `9a88599` | Audit, nettoyage, découpage et TF-IDF |
| `79f8667` | Comparaison des modèles de référence |
| `a950824` | Recherche KerasTuner |
| `b365c12` | Recherche Optuna |
| `7c18618` | Enregistrement des sorties Optuna |
| `f82199a` | Règle de sélection figée avant le test |
| `032ffd9` | Preuve de décision du modèle |
| `fb49780` | Campagne finale figée avant ouverture du test |
| `c524874` | Évaluation unique sur le test final |
| `28fdcdf` | Préparation de la sauvegarde |
| `93a143c` | Retrait de l'optimiseur de l'artefact Keras |
| `6e0c752` | Sauvegarde et contrôle des artefacts |
| `6c4753e` | API FastAPI |
| `92e449f` | Tests des routes API |
| `b0109ae` | Barrière qualité |
| `08f8ca6` | Test de rechargement des artefacts |
| `56da0a8` | Documentation API et qualité |
| `bff4277` | Dockerfile et `.dockerignore` |
| `2d071ff` | Preuve Docker locale |
| `fd58d3c` | Premier job CI tests/qualité |
| `b827921` | Job CI Docker |
| `e6bdcef` | Échec volontaire de la barrière |
| `b611886` | Retour au seuil normal |
| `a13ec16` | Publication ACR depuis la CI |
| `8f495eb` | Documentation du déploiement Azure |

Commandes Git répétées à chaque jalon :

```powershell
git status --short
git diff --check
git diff --stat

git add -- <fichiers-concernés>
git diff --cached --check
git diff --cached --stat

git commit -m "message du jalon"
git push
```

## 22. Ce qui est terminé

- cadrage et plan initial ;
- environnement Python isolé ;
- audit et dédoublonnage ;
- découpage reproductible ;
- TF-IDF sans fuite ;
- comparaison des trois références ;
- KerasTuner et Optuna, 20 essais chacun ;
- comparaison sur cinq graines ;
- décision figée avant le test ;
- campagne finale unique ;
- sauvegarde et rechargement des artefacts ;
- API et validation des entrées ;
- sept tests automatisés ;
- barrière qualité et expérience rouge/verte ;
- Docker et validation locale ;
- dépôt GitHub privé ;
- CI à trois jobs ;
- publication ACR par SHA ;
- premier déploiement manuel Azure ;
- tests publics et preuve du déploiement.

## 23. Ce qui reste à faire

Le projet n'est pas encore terminé. Les prochaines obligations sont :

1. obtenir la validation du formateur sur la version publique actuelle ;
2. ajouter la route `/hello` ;
3. ajouter son test ;
4. publier une nouvelle image identifiée par son SHA ;
5. déployer manuellement cette nouvelle version ;
6. vérifier `/hello` et le nouveau `app_version` ;
7. redéployer l'image `a13ec169...` ;
8. prouver que `/hello` a disparu et que l'ancienne version est revenue ;
9. tenir un journal des versions ;
10. créer `PROCEDURE_MISE_EN_PRODUCTION.md` ;
11. créer `FIN_DE_VIE.md` ;
12. renseigner les charges réelles et les écarts dans `PLAN.md` ;
13. relever les coûts Azure réellement disponibles et leur période ;
14. décider du nettoyage de l'identité OIDC inutilisée ;
15. documenter la rotation des mots de passe ACR après 90 jours ;
16. préparer la fiche d'une page et l'oral ;
17. exécuter une vérification finale de tous les livrables ;
18. supprimer uniquement les ressources propres au projet à la fin, sans supprimer le groupe partagé `adriouchRG`.

## 24. Points à savoir expliquer à l'oral

### Pourquoi le test final n'a-t-il servi qu'une fois ?

Parce qu'un test consulté plusieurs fois influence indirectement les décisions. Il devient alors une validation cachée et son score est optimiste.

### Pourquoi un lot de validation interne ?

Il permet de choisir les modèles et les hyperparamètres sans toucher au test final.

### Pourquoi `fit_transform` puis `transform` ?

Le premier apprend le vocabulaire et l'IDF sur l'apprentissage. Le second réutilise ces paramètres sans apprendre sur la validation ou le test.

### Pourquoi cinq graines ?

Pour mesurer la performance moyenne et la sensibilité à l'initialisation aléatoire du réseau.

### Pourquoi Optuna n'a-t-il pas automatiquement gagné ?

Optuna avait le meilleur essai isolé, mais l'architecture KerasTuner avait une meilleure moyenne sur cinq graines et surtout une dispersion plus faible selon la règle figée.

### Pourquoi la probabilité peut-elle sembler étrange ?

Elle correspond toujours à la classe horreur. Une réponse `predicted_class = 0` avec `probability = 0,41` signifie simplement que la probabilité d'horreur est inférieure au seuil 0,50.

### Pourquoi sauvegarder le vectoriseur avec le réseau ?

Le réseau attend exactement les mêmes 10 000 colonnes dans le même ordre. Recréer un autre vocabulaire rendrait les entrées incompatibles.

### Pourquoi Docker ?

Docker transporte le même code, les mêmes dépendances et les mêmes artefacts entre le poste local, GitHub Actions et Azure.

### Pourquoi taguer l'image avec le commit ?

Un SHA est immuable et précis. Il permet de savoir quel code tourne et de redéployer exactement une ancienne version.

### Pourquoi les jobs CI sont-ils dépendants ?

Une image ne doit pas être testée si la qualité a échoué, et ne doit pas être publiée si son test Docker a échoué.

### CI et CD sont-ils identiques ?

Non. Ici, la CI teste et publie l'image. Le déploiement Azure reste manuel, conformément au brief et aux droits disponibles.

### Pourquoi l'application peut-elle prendre du temps au premier appel ?

Avec zéro réplique minimale, Azure peut arrêter l'application. Le premier appel doit alors redémarrer le conteneur et charger TensorFlow.

## 25. Résumé final en une minute

Nous avons commencé avec 2 400 résumés étiquetés comédie ou horreur. Après audit, 54 doublons ont été retirés, laissant 2 346 lignes. Les données ont été séparées en 60 % apprentissage, 20 % test et 20 % production, avec une validation interne issue uniquement de l'apprentissage. Un TF-IDF de 10 000 variables a transformé les textes sans fuite de données. Trois modèles de référence ont été comparés, puis un réseau a été optimisé avec KerasTuner et Optuna. Une règle écrite avant le test a retenu l'architecture KerasTuner pour sa stabilité. Le test final, exécuté une seule fois sur 469 lignes, a donné un F1 de 0,830275.

Le réseau, le vectoriseur, les métriques et six exemples de référence ont été sauvegardés et rechargés sans écart. FastAPI expose `/health` et `/predict`. Sept tests et une barrière qualité contrôlent le service. Docker fournit un environnement reproductible. GitHub Actions exécute les tests, vérifie l'image puis la publie dans Azure Container Registry avec le SHA Git comme tag. L'image `a13ec169...` a été déployée manuellement dans `adriouch-modeleia-api` avec 1 vCPU, 2 Gio de mémoire, un accès HTTPS externe et une mise à l'échelle de zéro à une réplique. Les tests publics `/health`, prédiction valide et entrée vide ont réussi.

La prochaine étape, après validation du formateur, est de déployer une version ajoutant `/hello`, puis de revenir à `a13ec169...` pour démontrer un retour arrière réel.
