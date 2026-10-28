# Plan du projet - classifieur NLP de résumés de films

## 1. Objectif et règle de validation

Construire un pipeline reproductible qui classe un résumé en **comédie (`0`)** ou **horreur (`1`)**, compare des modèles dans des conditions équitables, exporte un modèle vérifiable, l'expose avec FastAPI, le teste, le conteneurise, publie ses images par GitHub Actions, puis le déploie manuellement sur Azure avec un retour arrière démontré.

Règle de travail : les choix de modèle et d'hyperparamètres sont arrêtés avec une validation interne issue des 60 % d'apprentissage. Le lot de test final n'est utilisé qu'une fois pour la campagne finale. Le lot de production reste à part et ne sert ni à l'apprentissage, ni au réglage, ni au calcul du score final.

## 2. État initial vérifié

### Données

- Fichier source : `textes_films_horreur_comedie.csv`.
- Forme : 2 400 lignes et 3 colonnes (`titre`, `resume`, `cible`).
- Étiquettes initiales : 1 200 comédies et 1 200 horreurs.
- Valeurs manquantes : aucune dans les trois colonnes.
- Textes vides après suppression des espaces de bord : aucun.
- Lignes ayant des espaces répétés, tabulations ou sauts de ligne dans `titre` ou `resume` : aucune.
- Doublons exacts au-delà de la première occurrence : 54, répartis dans 51 groupes (48 paires et 3 triplets).
- Résumés identiques associés à des étiquettes différentes : aucun.
- Après suppression des doublons exacts : 2 346 lignes, dont 1 195 comédies et 1 151 horreurs.
- Longueur des résumés : médiane de 474 caractères et 82 mots ; minimum de 201 caractères ; maximum de 7 104 caractères.

Ces nombres décrivent l'audit initial du fichier fourni. Ils devront être recalculés par le notebook, et non saisis comme constantes.

### Notebook existant

Éléments réutilisables :

- lecture du CSV et signification des classes ;
- notions de normalisation, mots vides, stemming et lemmatisation ;
- emploi de `train_test_split(..., stratify=...)` ;
- apprentissage du `TfidfVectorizer` sur l'apprentissage seulement ;
- régression logistique, calcul du F1 et principe de répétition sur cinq graines ;
- explications pédagogiques déjà rédigées sur plusieurs notions NLP.

Adaptations obligatoires au nouveau brief :

- ajouter l'audit et supprimer les 54 doublons avant tout découpage ;
- remplacer le découpage 75/25 par 60/20/20, puis créer une validation interne dans les seuls 60 % d'apprentissage ;
- réserver définitivement le test final et le lot de production ;
- calculer le F1 pour les comparaisons, sa moyenne et sa dispersion ;
- renommer en `accuracy` les valeurs actuellement appelées « précision » mais calculées par `(prediction == cible).mean()` ;
- ne pas réutiliser les scores enregistrés dans l'ancien notebook comme résultats du nouveau projet, car ils proviennent des 2 400 lignes non dédupliquées et d'un protocole 75/25 ;
- ajouter Bayes naïf, réseau dense, dropout, early stopping, KerasTuner, Optuna, fonction commune de construction, campagne finale et export/rechargement ;
- partager le prétraitement entre entraînement et API sans imposer spaCy/NLTK si l'expérience ne justifie pas leur coût ;
- ajouter API, tests, barrière qualité, Docker, CI, registre, déploiement Azure, retour arrière et fin de vie.

Le notebook contient des sorties d'une ancienne exécution, mais son noyau `Python (collecte-rn)` pointe vers un environnement virtuel d'un autre projet. Il n'est donc pas reproductible tel quel dans ce dossier.

## 3. Traçabilité des exigences

| Exigence obligatoire          | Réalisation prévue                                                                                                                                   | Livrable                                                            | Preuve de validation                                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Audit et nettoyage            | Contrôler schéma, valeurs manquantes, classes, longueurs, espaces, doublons complets et conflits de labels ; supprimer les doublons avant découpage | Notebook, section 1                                                 | Sorties d'audit avant/après et assertions                                 |
| Découpage 60/20/20           | Deux découpages stratifiés ; indices conservés ; lot production scellé                                                                             | Notebook, section 2                                                 | Effectifs, proportions et absence de chevauchement                         |
| Validation interne            | Découper uniquement les 60 % d'apprentissage pour comparer/régler                                                                                    | Notebook, sections 4 à 6                                           | Tailles et indices distincts du test final                                 |
| TF-IDF sans fuite             | Ajuster le vocabulaire sur le sous-ensemble d'apprentissage autorisé puis seulement transformer validation/test/production                            | Notebook, section 3 ; vectoriseur exporté                          | Dimensions, vocabulaire et contrôles de non-réajustement                 |
| Comparaison des références  | Régression logistique, MultinomialNB et réseau de départ, cinq graines, F1 moyen et écart-type                                                     | Notebook, section 4                                                 | Tableau des cinq scores, moyenne et dispersion                             |
| Marge de bruit                | Calcul pédagogique `1,96 * sqrt(p * (1-p) / n)` et avertissement sur le F1                                                                          | Notebook, sections 4 et 7                                           | Valeur calculée et interprétation avec dispersion entre graines          |
| KerasTuner                    | Fonction commune et recherche aléatoire de 20 essais                                                                                                  | Notebook, section 5                                                 | Résultats des 20 essais et meilleur réglage de validation                |
| Optuna                        | Même fonction, domaines, métrique, données et budget de 20 essais                                                                                   | Notebook, section 6                                                 | Étude de 20 essais et comparaison équitable                              |
| Verdict final                 | Figer les choix, réentraîner sur cinq graines, définir la règle d'export avant le test, lancer une seule campagne test                             | Notebook, section 7                                                 | Tableau final, règle de sélection datée et test non réutilisé         |
| Sauvegarde et rechargement    | Export `.keras`, vectoriseur joblib, `metrics.json` UTF-8 et échantillon de référence documenté                                                | `model/`                                                          | Prédictions identiques avant/après rechargement                          |
| API FastAPI                   | Chargement unique au démarrage ; `/health` et `/predict` ; validation explicite ; version modèle et commit séparés                             | `src/` et `README.md`                                           | `/docs`, cas valide, vide et très court                                 |
| Tests et barrière qualité   | Tests API, artefacts et qualité ; seuils configurables ; faux fichier de métriques séparé                                                          | `tests/`, `config.yaml`, `scripts/`                           | Vrai modèle accepté, faux modèle refusé sans écrasement               |
| Docker                        | Image d'inférence minimale, dépendances fixées, artefacts inclus                                                                                    | `Dockerfile`, `.dockerignore`, dépendances API                 | Construction, taille, démarrage, trois tests et logs                      |
| GitHub Actions                | Jobs `test`, `image`, puis `publier` avec `needs`; image étiquetée par SHA                                                                   | `.github/workflows/`                                              | Chaîne verte, expérience rouge, jobs suivants ignorés, retour au vert   |
| Azure                         | ACR Basic avec deux jetons ACR limités; Container App 1 vCPU/2 Gio, ingress externe et bon port ; déploiement manuel                                 | Ressources Azure et procédure                                      | Image par commit, URL publique, tests et validation formateur              |
| Évolution et retour arrière | Ajouter `/hello`, publier/déployer le nouveau SHA, puis redéployer l'ancien SHA                                                                    | Code, images et journal des versions                                | `/hello` apparaît puis disparaît ; `/health` montre les SHA attendus |
| Documentation C12             | Mettre à jour plan/réel, procédure d'une page, journal, fin de vie partielle/totale                                                                 | `PLAN.md`, `PROCEDURE_MISE_EN_PRODUCTION.md`, `FIN_DE_VIE.md` | Cohérence dates, charges, commits, décisions et ressources               |
| Fin de vie                    | Identifier les ressources propres au projet, coûts estimés/réels, ordre de retrait ; ne jamais supprimer un groupe partagé                         | `FIN_DE_VIE.md` et preuves                                        | Absence vérifiée de l'app, de son environnement et du registre           |
| Synthèse et oral             | Fiche d'une page et préparation aux questions                                                                                                         | Fiche finale, `README.md`, preuves                                | Relecture des livrables et exécution complète du notebook                |

## 4. Planning C12 prévisionnel

Les dates sont provisoires, faute de date de rendu communiquée. La charge est du temps de travail actif ; le temps de calcul et d'attente des services sera relevé séparément. Les charges réelles restent volontairement vides et seront remplies au fil du projet.

| ID | Tâche                                                             | Dépend de                   | Charge estimée | Charge réelle | Ressources humaines                              | Ressources matérielles                | Ressources techniques                   | Ressources financières                     | Date prévue |
| -- | ------------------------------------------------------------------ | ---------------------------- | --------------: | -------------- | ------------------------------------------------ | -------------------------------------- | --------------------------------------- | ------------------------------------------- | ------------ |
| P0 | Cadrage, audit des références et environnement                   | -                            |             4 h |                | Apprenant                                        | PC Windows, 10 Gio libres recommandés | VS Code, PowerShell, Python, Git        | 0 EUR supplémentaire                       | 2026-10-23   |
| P1 | Créer l'environnement isolé, le noyau et le dépôt Git          | P0 et espace disque libéré |             2 h |                | Apprenant                                        | PC Windows                             | `venv`, pip, ipykernel, Git           | 0 EUR supplémentaire                       | 2026-10-26   |
| N1 | Audit, nettoyage et documentation des données                     | P1                           |             3 h |                | Apprenant                                        | PC Windows                             | pandas, Jupyter                         | 0 EUR supplémentaire                       | 2026-10-27   |
| N2 | Découpages, validation interne et TF-IDF                          | N1                           |             3 h |                | Apprenant                                        | PC Windows                             | scikit-learn, matrices creuses          | 0 EUR supplémentaire                       | 2026-10-28   |
| N3 | Références sur cinq graines et notions ML                        | N2                           |             4 h |                | Apprenant                                        | CPU et RAM locales                     | scikit-learn, TensorFlow                | Électricité locale non isolée            | 2026-10-29   |
| N4 | KerasTuner, 20 essais                                              | N3                           |             4 h |                | Apprenant                                        | CPU et RAM locales                     | KerasTuner                              | Électricité locale non isolée            | 2026-10-30   |
| N5 | Optuna, 20 essais comparables                                      | N4                           |             4 h |                | Apprenant                                        | CPU et RAM locales                     | Optuna                                  | Électricité locale non isolée            | 2026-11-02   |
| N6 | Verdict final, export et test de rechargement                      | N5                           |             4 h |                | Apprenant                                        | PC Windows                             | TensorFlow, joblib, JSON                | 0 EUR supplémentaire                       | 2026-11-03   |
| A1 | API, validation des entrées, tests et barrière qualité          | N6                           |             5 h |                | Apprenant                                        | PC Windows                             | FastAPI, Pydantic, pytest               | 0 EUR supplémentaire                       | 2026-11-04   |
| D1 | Docker, image d'inférence et tests conteneur                      | A1                           |             4 h |                | Apprenant                                        | PC Windows, Docker Desktop             | Dockerfile, Docker CLI                  | 0 EUR supplémentaire                       | 2026-11-05   |
| C1 | Dépôt GitHub et jobs `test`/`image`, expérience rouge/verte | D1                           |             4 h |                | Apprenant                                        | Internet                               | Git, GitHub Actions                     | Selon quota du compte GitHub                | 2026-11-06   |
| C2 | ACR et job `publier` par SHA                                     | C1                           |             3 h |                | Apprenant                                        | Internet                               | GitHub Secrets, ACR Basic               | Estimation Azure à relever avant création | 2026-11-09   |
| Z1 | Container App et tests publics                                     | C2                           |             3 h |                | Apprenant, formateur pour le point de validation | Internet                               | Azure Container Apps, Azure CLI/portail | Estimation Azure à relever avant création | 2026-11-10   |
| Z2 | Ajouter `/hello`, déployer et effectuer le retour arrière      | Z1 et accord formateur       |             3 h |                | Apprenant                                        | Internet                               | Git, GitHub Actions, Azure              | Consommation Azure pendant l'essai          | 2026-11-12   |
| F1 | Documentation finale, preuves, oral et fin de vie                  | Z2                           |             6 h |                | Apprenant, formateur à l'oral                   | PC et Internet                         | Markdown, portail Azure, GitHub         | Coût réel Azure à relever                | 2026-11-13   |

Charge totale estimée : **52 heures de travail actif**. L'estimation devra être révisée si les recherches d'hyperparamètres dépassent le budget matériel local ou si l'accès Azure impose un délai externe.

## 5. Ressources et responsabilités

- **Décideur et exécutant du déploiement** : l'apprenant, dans la limite du rôle Azure Contributeur.
- **Validation avant évolution** : le formateur vérifie l'adresse publique et les trois cas avant l'ajout de `/hello`.
- **Matériel local** : Windows 11 64 bits, Intel Core i7-1165G7 (4 coeurs/8 threads), 15,7 Gio de RAM. Cette configuration est suffisante pour le petit jeu de données et des réseaux denses modestes sur CPU.
- **Services** : GitHub, GitHub Actions, Azure Container Registry Basic et Azure Container Apps.
- **Secrets** : uniquement dans GitHub Secrets et Azure ; jamais dans Git, les notebooks, les journaux ou les captures.
- **Coûts** : chiffrer ACR et Container Apps avec les paramètres réellement retenus juste avant création ; relever ensuite le coût réel visible en précisant la période et le délai de remontée.

## 6. Arborescence cible proposée

```text
modeleIA/
|-- .github/workflows/ci.yml
|-- data/raw/textes_films_horreur_comedie.csv
|-- docs/briefs/
|-- evidence/
|-- model/
|   |-- metrics.json
|   |-- model.keras
|   |-- reference.csv
|   `-- vectorizer.joblib
|-- notebooks/
|   |-- tp7_texte_nlp.ipynb
|   `-- 01_pipeline_nlp.ipynb
|-- scripts/quality_gate.py
|-- src/
|   |-- api.py
|   |-- model_factory.py
|   `-- preprocessing.py
|-- tests/
|-- .dockerignore
|-- .gitignore
|-- config.yaml
|-- Dockerfile
|-- FIN_DE_VIE.md
|-- PLAN.md
|-- PROCEDURE_MISE_EN_PRODUCTION.md
|-- README.md
|-- requirements-api.txt
|-- requirements-dev.txt
`-- requirements-train.txt
```

Les quatre fichiers sources resteront inchangés. Leur rangement éventuel sera fait par déplacement Git traçable seulement après initialisation du dépôt.

## 7. Dépendances : séparation prévue

- `requirements-train.txt` : pandas, NumPy, scikit-learn, TensorFlow CPU, KerasTuner, Optuna, joblib, ipykernel et JupyterLab.
- `requirements-api.txt` : TensorFlow CPU, scikit-learn, joblib, FastAPI, Uvicorn, Pydantic et les dépendances minimales de chargement.
- `requirements-dev.txt` : dépendances API plus pytest, client HTTP de test et lecteur YAML de la barrière qualité.

Les versions seront fixées et installées dans `.venv` après libération de l'espace disque, puis validées par imports, `pip check`, exécution d'un mini-calcul TensorFlow et enregistrement d'un noyau propre au projet.

## 8. Vérification de l'environnement au 2026-10-23

| Élément                                     | Résultat réel                                                                     | Décision                                                                                   |
| --------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Windows                                       | Windows 11 Famille 64 bits, build 26300                                             | Compatible                                                                                  |
| PowerShell                                    | 7.6.5 ; politique locale `RemoteSigned`                                           | Utiliser uniquement la syntaxe PowerShell dans les consignes locales                        |
| VS Code                                       | 1.142.0 ; extensions Python, Pylance, Jupyter, Conteneurs et PowerShell présentes  | Compatible                                                                                  |
| Python                                        | CPython 3.11.0 64 bits dans `C:\Python311`                                        | Conserver Python 3.11 pour le projet                                                        |
| Environnement Python global                   | Plusieurs incohérences signalées par `pip check` et distributions pip invalides | Ne pas l'utiliser pour le projet                                                            |
| Ancien noyau                                  | `Python (collecte-rn)` pointe vers la `.venv` d'un autre dossier                | Ne pas l'utiliser ; créer `Python (modeleIA)`                                            |
| Jupyter                                       | Non présent comme commande directe, mais disponible via `python -m jupyter`      | Le nouveau noyau sera enregistré depuis `.venv`                                          |
| Bibliothèques manquantes dans l'ancien noyau | KerasTuner, Optuna, FastAPI, Uvicorn et pytest                                      | Installer dans l'environnement du projet, pas dans l'ancien                                 |
| Git                                           | 2.46.2 ; dossier actuel non initialisé                                             | Initialiser après validation de l'arborescence                                             |
| Docker                                        | CLI 29.7.2 et Compose 5.5.1 ; moteur Docker arrêté                                | Démarrer Docker Desktop au début de l'étape conteneur                                    |
| WSL                                           | WSL 2 configuré, distribution Ubuntu par défaut                                   | Compatible avec Docker Desktop                                                              |
| Azure CLI                                     | Absente                                                                             | Installer avant les opérations Azure ; le portail reste prévu pour les contrôles visuels |
| GitHub CLI                                    | Absente                                                                             | Facultative ; Git et l'interface web suffisent                                              |
| Disque `C:`                                 | 74,53 Gio libres lors de la dernière vérification                                 | Compatible avec l'environnement Python et les prochaines constructions Docker               |
| Mémoire                                      | 15,7 Gio                                                                            | Adaptée au projet local ; surveiller les conversions TF-IDF denses                         |

## 9. Risques et mesures

| Risque                                   | Impact                                          | Mesure prévue                                                                             |
| ---------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Espace disque insuffisant                | Installation et construction Docker impossibles | Libérer de l'espace avant P1 et revérifier avec `Get-Volume C`                         |
| Fuite entre doublons ou partitions       | Scores artificiellement élevés                | Dédupliquer avant split et tester l'absence de chevauchement                              |
| Utilisation répétée du test           | Réglage indirect sur le test                   | Sceller les indices et journaliser l'unique campagne finale                                |
| TF-IDF dense trop volumineux             | Mémoire saturée                               | Garder les modèles simples en creux ; convertir seulement des lots contrôlés pour Keras |
| Comparaison inéquitable des optimiseurs | Conclusion non défendable                      | Même fonction, domaines, données, métrique et 20 essais chacun                          |
| Variabilité des réseaux                | Choix opportuniste d'une graine                 | Cinq graines, règle d'export définie avant le test et dispersion publiée                |
| Image Docker trop lourde                 | Construction lente et coût de stockage         | Dépendances API séparées, contexte exclu et taille mesurée                             |
| Droits Azure limités                    | Déploiement automatisé impossible             | Publication CI, déploiement manuel, authentification par jetons ACR limités au dépôt   |
| Suppression trop large                   | Perte de ressources partagées                  | Inventaire par nom/ID et suppression ressource par ressource ; jamais le groupe partagé   |

## 10. Améliorations facultatives, hors obligations du brief

- validation croisée plus poussée ;
- calibration des probabilités et choix explicite du seuil de décision ;
- suivi d'expériences avec MLflow ;
- analyse d'explicabilité des mots influents ;
- scan de vulnérabilités de l'image ;
- déploiement Azure automatisé après obtention des droits adaptés.

Ces améliorations ne seront réalisées qu'après les obligations et si le temps le permet.

## 11. Condition de sortie de l'étape 1

L'étape est validée lorsque :

1. les quatre références sont lues et leur traçabilité est consignée ;
2. le diagnostic de l'ancien notebook et du CSV est reproductible ;
3. le planning C12 est accepté ;
4. au moins 10 Gio sont libres sur `C:` ;
5. `.venv` est créée, les trois ensembles de dépendances sont fixés, `pip check` passe, le noyau `Python (modeleIA)` est enregistré et un dépôt Git propre est initialisé.

Au 2026-10-23, les cinq points sont réalisés : la `.venv` Python 3.11 est créée, `pip` y est mis à niveau, les dépendances sont installées sans conflit, Git est initialisé sur `main`, le noyau `Python (modeleIA)` est enregistré et les tests de fumée TF-IDF, scikit-learn, Keras et FastAPI réussissent.

## 12. Avancement réel au 28 octobre 2026

Les dates réelles ci-dessous proviennent de l’historique Git. Elles
prouvent les jours de réalisation, mais ne mesurent pas le temps actif.
Les charges réelles ci-dessous sont des estimations rétrospectives.
Elles sont reconstruites à partir des sessions, des commits et des
incidents, car aucun chronométrage précis n’a été effectué.

| Phase                                   | Date prévue     | Date réelle  | Statut   | Preuve principale          | Charge réelle |
| --------------------------------------- | ---------------- | ------------- | -------- | -------------------------- | -------------- |
| P0-P1 — Cadrage et environnement       | 23 et 26 octobre | 23 octobre    | Terminé | `8f2b724`                | 4,0 h          |
| N1-N2 — Audit, découpage et TF-IDF    | 27 et 28 octobre | 23 octobre    | Terminé | `9a88599`                | 2,0 h          |
| N3 — Modèles de référence           | 29 octobre       | 23 octobre    | Terminé | `79f8667`                | 1,5 h          |
| N4 — KerasTuner                        | 30 octobre       | 23 octobre    | Terminé | `a950824`                | 1,0 h          |
| N5 — Optuna                            | 2 novembre       | 23-24 octobre | Terminé | `b365c12`, `7c18618`   | 1,0 h          |
| N6 — Verdict, test et artefacts        | 3 novembre       | 24 octobre    | Terminé | `c524874`, `6e0c752`   | 2,5 h          |
| A1 — API et qualité                   | 4 novembre       | 24 octobre    | Terminé | `6c4753e` à `08f8ca6` | 3,5 h          |
| D1 — Docker                            | 5 novembre       | 24 octobre    | Terminé | `bff4277`, `2d071ff`   | 2,5 h          |
| C1 — CI et expérience rouge/verte     | 6 novembre       | 24 octobre    | Terminé | `fd58d3c` à `b611886` | 2,0 h          |
| C2 — Publication ACR                   | 9 novembre       | 25 octobre    | Terminé | `a13ec16`                | 2,5 h          |
| Z1 — Déploiement initial Azure        | 10 novembre      | 25 octobre    | Terminé | `8f495eb`                | 2,0 h          |
| Z2 — `/hello` et retour arrière     | 12 novembre      | 27-28 octobre | Terminé | `c8a90cc`, `def187b`   | 2,0 h          |
| F1 — Documentation, oral et fin de vie | 13 novembre      | 27-28 octobre | En cours | Documents C12              | 4,0 h          |

Pour éviter une fausse précision, les temps sont regroupés par famille
de travail :

### Charges réelles reconstruites

| Famille                             | Charge réelle à renseigner |
| ----------------------------------- | ---------------------------: |
| Cadrage et environnement            |                          4 h |
| Notebook, modèles et optimisation  |                          8 h |
| API, tests et Docker                |                          6 h |
| GitHub Actions et ACR               |                        4,5 h |
| Azure et retour arrière            |                          4 h |
| Documentation et préparation orale |                          4 h |
| Total                               |                       30,5 h |

### Écarts par rapport au plan

Les travaux techniques ont été réalisés plus tôt que les dates
prévisionnelles. Cela ne signifie pas que les estimations horaires
étaient exactes : le planning initial décrivait une progression
pédagogique, alors que plusieurs étapes ont été regroupées sur les
mêmes journées.

Écarts et incidents rencontrés :

- ancien `pip` incapable de valider correctement le certificat PyPI ;
- environnement de l’ancien notebook non reproductible ;
- démarrage initial de Docker Desktop nécessaire ;
- Windows PowerShell 5.1 sans `-SkipHttpErrorCheck` ;
- absence initiale de GitHub CLI ;
- absence de droit Azure pour créer une affectation de rôle ;
- abandon de l’authentification OIDC au profit de jetons ACR limités ;
- premier secret ACR vide, puis régénéré avec `password1` ;
- nécessité de distinguer image publiée et image réellement déployée ;
- conservation d’une version immuable pour démontrer le retour arrière.

### Ressources réellement utilisées

- un apprenant comme exécutant et décideur technique ;
- un formateur pour la validation avant l’évolution ;
- PC Windows avec CPU local pour TensorFlow ;
- VS Code, PowerShell, Python 3.11, Git et Docker Desktop ;
- GitHub privé et GitHub Actions ;
- Azure Container Registry Basic ;
- Azure Container Apps avec 1 vCPU, 2 Gio et zéro à une réplique.

### Coûts

Les coûts réels Azure ne sont pas encore renseignés. Ils devront être
relevés dans Azure Cost Management en indiquant :

- la période couverte ;
- les ressources filtrées ;
- les éventuels délais de remontée ;
- les coûts impossibles à isoler dans l’abonnement partagé.

Aucun montant ne sera inventé si Azure ne fournit pas encore la donnée.

### Travaux restant à terminer

- faire valider ou compléter les charges réelles ;
- relever les coûts Azure ;
- finaliser les livrables C12 ;
- préparer la fiche de synthèse et les questions d’oral ;
- exécuter la vérification finale ;
- appliquer la fin de vie uniquement après l’oral et l’accord du
  formateur.

### Comparaison de charge

- charge prévisionnelle initiale : 52 h ;
- charge réelle reconstruite : 30,5 h ;
- écart : -21,5 h, soit environ -41 %.

Cette valeur est une estimation rétrospective du temps de travail
actif. Elle exclut les temps d’attente non surveillés : entraînements,
construction Docker, exécution GitHub Actions, démarrages Azure et
attente de validation.

L’écart s’explique principalement par le regroupement de plusieurs
étapes sur les mêmes sessions, la réutilisation d’une fonction commune
pour les réseaux et l’accompagnement guidé. Cette estimation ne doit
pas être présentée comme un chronométrage exact.
