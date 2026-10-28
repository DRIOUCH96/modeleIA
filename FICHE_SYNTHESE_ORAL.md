# Fiche de synthèse — Classifieur de résumés de films

## Objectif

Le projet classe un résumé de film en `0 = comédie` ou `1 = horreur`.

Chaîne complète :

CSV -> nettoyage -> découpage -> TF-IDF -> modèle -> artefacts
-> FastAPI -> Docker -> GitHub Actions -> ACR -> Container Apps

## Données et protocole

- Données initiales : 2 400 résumés équilibrés.
- Après suppression des doublons : 2 346 résumés.
- Apprentissage : 1 407 lignes.
- Test final : 469 lignes.
- Lot de production scellé : 470 lignes.
- Validation interne : 282 lignes issues de l’apprentissage.
- Le test final n’a été utilisé qu’une seule fois.
- Le lot de production n’a servi ni au réglage ni au score final.

## Sélection du modèle

Le texte est transformé avec TF-IDF :

- vocabulaire maximal : 10 000 caractéristiques ;
- unigrammes et bigrammes ;
- matrice creuse pour limiter la mémoire.

Les modèles comparés sont Bayes naïf, régression logistique, réseau dense,
KerasTuner et Optuna.

Le réseau KerasTuner a été choisi après une comparaison sur cinq graines.
Son F1 moyen était proche de celui d’Optuna, mais sa variabilité était plus
faible.

## Résultat final

Le réseau final a été entraîné avec la graine 11 pendant 6 époques.

- accuracy : 0,842217 ;
- précision : 0,878641 ;
- rappel : 0,786957 ;
- F1 : **0,830275** ;
- matrice de confusion : `[[214, 25], [49, 181]]`.

La barrière qualité exige un F1 minimal de 0,80 et au moins 400 exemples de
test. Le modèle respecte ces deux seuils.

## Industrialisation

Les artefacts sauvegardés sont :

- `model.keras` ;
- `vectorizer.joblib` ;
- `metrics.json` ;
- `reference_sample.json`.

Les prédictions ont été reproduites après rechargement avec un écart maximal
de probabilité égal à zéro.

L’API FastAPI expose `/health`, `/predict` et, dans la version 2, `/hello`.
Les tests pytest, la construction Docker et les contrôles de l’image sont
exécutés par GitHub Actions.

L’image est publiée dans :

`adriouchmovieacr.azurecr.io/classifieur-films-api:<SHA Git>`

L’API est hébergée dans Azure Container Apps :

`https://adriouch-modeleia-api.niceforest-29b9ca50.francecentral.azurecontainerapps.io`

## Version et retour arrière

- version 1 : commit `a13ec16`, sans `/hello` ;
- version 2 : commit `c8a90cc`, avec `/hello` ;
- retour arrière : redéploiement de la version 1 ;
- après le rollback, `/health` indique l’ancien SHA ;
- `/predict` fonctionne encore ;
- `/hello` retourne HTTP 404.

Le tag Docker, le SHA Git, la révision Azure et la réponse `/health`
permettent d’identifier précisément la version déployée.

## Coûts Azure

Le relevé Azure Cost Management est filtré sur `project=modeleia`.

- coût réel exact au 28 octobre 2026 : 0,487956505104 EUR ;
- montant à présenter : **0,49 EUR** ;
- budget mensuel affiché : 8 EUR ;
- jours contenant des coûts : du 24 au 28 octobre 2026.

Le montant peut évoluer à cause du délai de remontée des données Azure.

## Limites et améliorations

- Le modèle ne connaît que deux classes.
- Un texte hors domaine reçoit malgré tout une réponse comédie ou horreur.
- Une classe « autre » ou un seuil de rejet améliorerait ce comportement.
- Le lot de production reste disponible pour une future surveillance.
- Une identité managée pourrait remplacer les jetons ACR si les droits Azure
  nécessaires étaient disponibles.

## Message principal pour l’oral

J’ai séparé l’apprentissage, la validation, le test final et la production.
J’ai ensuite rendu le modèle reproductible, testable, versionné,
conteneurisé, déployable et réversible.
