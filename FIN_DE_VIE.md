# Plan de fin de vie

> Avertissement : ce document contient des commandes destructives.
> Elles ne doivent pas être exécutées pendant la rédaction du projet.
> Chaque suppression exige une validation explicite et un contrôle de
> la ressource ciblée.

## 1. Objectif

La fin de vie retire proprement le service tout en conservant les
éléments nécessaires à l’audit, à l’oral et à une éventuelle
restauration.

Deux scénarios sont distingués :

- fin de vie partielle : arrêter l’exposition publique tout en
  conservant les images et les preuves ;
- fin de vie totale : retirer toutes les ressources propres au projet
  après la période de conservation.

Le groupe de ressources `adriouchRG` est partagé avec d’autres projets.
Il ne doit jamais être supprimé.

## 2. Inventaire des éléments du projet

| Élément | Nom ou emplacement | Propre au projet ? | Décision |
|---|---|---:|---|
| Container App | `adriouch-modeleia-api` | Oui | Supprimer |
| Environnement Container Apps | `adriouch-modeleia-env` | Oui | Supprimer après l’application |
| Azure Container Registry | `adriouchmovieacr` | Oui | Supprimer en fin de vie totale |
| Dépôt d’images | `classifieur-films-api` | Oui | Supprimé avec ACR |
| Jeton de publication | `github-modeleia-push` | Oui | Désactiver ou supprimer |
| Jeton de lecture | `adriouch-modeleia-pull` | Oui | Désactiver ou supprimer |
| Identité OIDC inutilisée | `github-modeleia-acr-push` | Oui | Supprimer |
| Secret GitHub | `ACR_PASSWORD` | Oui | Supprimer |
| Variables GitHub | `ACR_IMAGE_NAME`, `ACR_LOGIN_SERVER`, `ACR_USERNAME` | Oui | Supprimer en fin de vie totale |
| Dépôt GitHub | `DRIOUCH96/modeleIA` | Oui | Archiver, ne pas supprimer par défaut |
| Modèle et vectoriseur | `model/` | Oui | Conserver avec les preuves |
| Données sources | `textes_films_horreur_comedie.csv` | Oui | Conserver selon la politique validée |
| Métriques et preuves | `evidence/` | Oui | Conserver |
| Groupe de ressources | `adriouchRG` | Non, partagé | Ne jamais supprimer |

## 3. Dépendances et ordre de retrait

L’application dépend de l’environnement Container Apps et de l’image
présente dans ACR.

L’ordre de retrait est donc :

1. collecter les preuves et les coûts ;
2. supprimer l’application publique ;
3. supprimer l’environnement devenu vide ;
4. supprimer ou désactiver les secrets et jetons ;
5. supprimer l’identité OIDC inutilisée ;
6. supprimer ACR et ses images en fin de vie totale ;
7. archiver le dépôt GitHub ;
8. vérifier l’absence des ressources.

Supprimer ACR avant l’application empêcherait un redémarrage ou un
retour arrière. Cet ordre est donc interdit.

## 4. Préconditions obligatoires

Avant toute suppression :

- obtenir l’accord du formateur ;
- vérifier que l’oral et les démonstrations sont terminés ;
- pousser tous les commits et vérifier que Git est propre ;
- conserver les résultats des workflows verts et rouges ;
- conserver les réponses `/health`, `/predict` et `/hello` ;
- enregistrer les commits, images, digests et révisions Azure ;
- relever les coûts estimés et réels disponibles ;
- préciser la période couverte par les coûts ;
- vérifier qu’une copie du modèle et des preuves existe ;
- vérifier chaque nom de ressource avant suppression.

Contrôles Git :

```powershell
git status --short
git log --oneline --decorate -10
git push
```

## 5. Collecte des coûts

Les coûts doivent être relevés dans Azure Cost Management en filtrant :

- l’abonnement utilisé par le projet ;
- le groupe `adriouchRG` ;
- le tag `project=modeleia` ;
- la période comprise entre la création et le retrait des ressources.

Il faut distinguer :

- l’estimation avant création ;
- le coût réellement visible ;
- la période couverte ;
- le délai éventuel de remontée des données ;
- les consommations non taguées ou impossibles à isoler.

Aucun montant ne doit être inventé lorsque le portail ne l’affiche pas.

### Relevé du 28 octobre 2026

Le relevé a été généré le 28 octobre 2026 à 14:01 UTC.

- coût réel exact : **0,487956505104 EUR** ;
- coût arrondi : **0,49 EUR** ;
- jours contenant des coûts : du 24 au 28 octobre 2026 ;
- budget mensuel affiché : **8 EUR** ;
- filtre : `ResourceGroupName=adriouchrg` et `project=modeleia`.

Ce montant doit être actualisé une dernière fois avant la suppression des
ressources. Le relevé final pourra évoluer à cause du délai de remontée des
données Azure.

Preuves conservées :

- `evidence/azure/costs_2026-10-28.txt` ;
- `evidence/azure/costs_project_modeleia_2026-10-28.xlsx`.

## 6. Fin de vie partielle

La fin de vie partielle retire l’API publique, mais conserve :

- ACR ;
- les images identifiées par SHA ;
- le modèle et le vectoriseur ;
- le dépôt GitHub archivé ou actif ;
- les métriques et les preuves.

### Suppression de la Container App

À exécuter uniquement après validation :

```powershell
az containerapp show `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG `
  --output table

az containerapp delete `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG
```

Ne pas utiliser `--yes` : la confirmation interactive constitue une
protection contre une suppression accidentelle.

### Désactivation des jetons ACR

```powershell
az acr token update `
  --name github-modeleia-push `
  --registry adriouchmovieacr `
  --status disabled

az acr token update `
  --name adriouch-modeleia-pull `
  --registry adriouchmovieacr `
  --status disabled
```

### Suppression du secret GitHub

```powershell
gh secret delete ACR_PASSWORD `
  --repo DRIOUCH96/modeleIA
```

Les variables non secrètes peuvent être conservées pour faciliter une
restauration.

## 7. Restauration après une fin de vie partielle

Pour restaurer le service :

1. réactiver les jetons ACR ;
2. régénérer leurs mots de passe ;
3. recréer le secret GitHub ;
4. recréer la Container App avec une image identifiée par son SHA ;
5. vérifier `/health` et `/predict` ;
6. enregistrer la nouvelle révision.

La restauration doit utiliser une image déjà validée, jamais un tag
flottant comme `latest`.

## 8. Fin de vie totale

La fin de vie totale intervient uniquement lorsque la période de
conservation est terminée et qu’aucune restauration n’est prévue.

### 8.1 Supprimer la Container App

```powershell
az containerapp show `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG `
  --output table

az containerapp delete `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG
```

Si elle a déjà été supprimée pendant la fin de vie partielle, cette
étape est simplement vérifiée.

### 8.2 Vérifier puis supprimer l’environnement

```powershell
az containerapp list `
  --environment adriouch-modeleia-env `
  --resource-group adriouchRG `
  --output table

az containerapp env delete `
  --name adriouch-modeleia-env `
  --resource-group adriouchRG
```

L’environnement ne doit être supprimé que lorsque la liste des
applications qu’il contient est vide.

### 8.3 Supprimer les secrets et variables GitHub

```powershell
gh secret delete ACR_PASSWORD `
  --repo DRIOUCH96/modeleIA

gh variable delete ACR_IMAGE_NAME `
  --repo DRIOUCH96/modeleIA

gh variable delete ACR_LOGIN_SERVER `
  --repo DRIOUCH96/modeleIA

gh variable delete ACR_USERNAME `
  --repo DRIOUCH96/modeleIA
```

### 8.4 Supprimer l’identité OIDC inutilisée

Cette identité n’a jamais obtenu le rôle nécessaire et n’est pas
utilisée par le pipeline.

```powershell
az identity show `
  --name github-modeleia-acr-push `
  --resource-group adriouchRG `
  --output table

az identity delete `
  --name github-modeleia-acr-push `
  --resource-group adriouchRG
```

### 8.5 Supprimer Azure Container Registry

La suppression du registre retire également ses images, jetons et
scope maps.

```powershell
az acr show `
  --name adriouchmovieacr `
  --resource-group adriouchRG `
  --output table

az acr delete `
  --name adriouchmovieacr `
  --resource-group adriouchRG
```

La confirmation interactive doit afficher exactement
`adriouchmovieacr`.

### 8.6 Archiver le dépôt GitHub

L’archivage est recommandé à la place de la suppression, car il
conserve le code, les commits et les preuves en lecture seule.

```powershell
gh repo archive DRIOUCH96/modeleIA
```

La suppression définitive du dépôt nécessite une décision séparée et
n’est pas incluse dans la procédure normale.

## 9. Conservation des éléments

Proposition à faire valider par le formateur :

- conserver le dépôt GitHub privé et archivé pendant 12 mois ;
- conserver `model/`, `evidence/`, le notebook et les métriques pendant
  la même période ;
- conserver l’empreinte du CSV et les indices de découpage ;
- ne conserver aucun mot de passe ou jeton ;
- supprimer immédiatement `.venv/`, les caches et les fichiers
  temporaires lorsqu’ils ne sont plus nécessaires ;
- supprimer les images Azure lors de la fin de vie totale après
  conservation de leurs digests dans les preuves.

La durée réelle dépend de la politique de l’organisme de formation.

## 10. Vérifications après retrait

Les commandes suivantes doivent échouer avec une ressource introuvable
après une fin de vie totale :

```powershell
az containerapp show `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG

az containerapp env show `
  --name adriouch-modeleia-env `
  --resource-group adriouchRG

az acr show `
  --name adriouchmovieacr `
  --resource-group adriouchRG

az identity show `
  --name github-modeleia-acr-push `
  --resource-group adriouchRG
```

Contrôler également GitHub :

```powershell
gh secret list --repo DRIOUCH96/modeleIA
gh variable list --repo DRIOUCH96/modeleIA
```

Le groupe partagé doit toujours exister :

```powershell
az group show `
  --name adriouchRG `
  --output table
```

## 11. Preuves de fin de vie

Le dossier `evidence/azure/` devra contenir :

- date et heure du retrait ;
- décision de fin de vie partielle ou totale ;
- accord du formateur ;
- coût relevé et période couverte ;
- liste des ressources avant suppression ;
- résultats des commandes de suppression ;
- vérifications d’absence ;
- confirmation que `adriouchRG` existe toujours ;
- liste des éléments conservés ;
- date prévue de suppression des archives restantes.

## 12. État actuel

À la date de rédaction :

- aucune ressource n’est supprimée ;
- la version `a13ec169...` est active après retour arrière ;
- `/health` et `/predict` sont opérationnelles ;
- `/hello` retourne HTTP `404` ;
- les ressources restent nécessaires pour la démonstration et l’oral.
