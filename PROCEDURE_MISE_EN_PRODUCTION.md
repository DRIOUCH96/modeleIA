
# Procédure synthétique de mise en production

## Périmètre et responsabilités

Application : `adriouch-modeleia-api`Environnement : `adriouch-modeleia-env`Registre : `adriouchmovieacr.azurecr.io/classifieur-films-api`Groupe partagé : `adriouchRG`, à ne jamais supprimer.

- L’apprenant choisit le SHA, contrôle la CI et déploie manuellement.
- GitHub Actions teste puis publie l’image dans ACR.
- Le formateur valide l’API avant une évolution sensible.
- Aucun secret ne doit apparaître dans Git ou dans les preuves.

## 1. Conditions de déploiement

Le déploiement est autorisé si :

- le commit est poussé sur `main` ;
- les huit tests et la barrière qualité réussissent ;
- le test Docker réussit ;
- l’image portant le SHA complet existe dans ACR ;
- le SHA actif avant modification est enregistré ;
- l’accord du formateur est obtenu lorsqu’il est requis.

```powershell
git status --short
$targetCommit = "<SHA_COMPLET_VALIDE>"

gh run list --workflow "CI" --commit $targetCommit --limit 1

az acr repository show `
  --name adriouchmovieacr `
  --image "classifieur-films-api:$targetCommit" `
  --output table

az containerapp show `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG `
  --output table
```

## 2. Déploiement manuel

```powershell
$image = "adriouchmovieacr.azurecr.io/classifieur-films-api:$targetCommit"
$shortCommit = $targetCommit.Substring(0, 7)
$timestamp = Get-Date -Format "MMddHHmm"
$suffix = "deploy-$shortCommit-$timestamp"

az containerapp update `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG `
  --image $image `
  --revision-suffix $suffix `
  --output none
```

Le déploiement reste manuel : les identifiants ACR de GitHub publient
les images, mais ne donnent pas le droit de modifier la Container App.

## 3. Validation après déploiement

URL :

```text
https://adriouch-modeleia-api.niceforest-29b9ca50.francecentral.azurecontainerapps.io
```

Contrôles obligatoires :

- `/health` retourne HTTP `200`, `model_loaded=true` et le SHA attendu ;
- `/predict` retourne HTTP `200` pour un résumé valide ;
- `/predict` retourne HTTP `422` pour un texte vide ;
- les nouvelles routes répondent comme prévu ;
- l’image, la révision, la date et les réponses sont conservées dans
  `evidence/azure/`.

## 4. Retour arrière

Déclencher le retour arrière si la santé, la version ou le contrat HTTP
est incorrect, ou si une régression est constatée.

```powershell
$rollbackCommit = "<SHA_COMPLET_PRECEDENT_VALIDE>"
$rollbackImage = "adriouchmovieacr.azurecr.io/classifieur-films-api:$rollbackCommit"
$rollbackShort = $rollbackCommit.Substring(0, 7)
$timestamp = Get-Date -Format "MMddHHmm"
$rollbackSuffix = "rollback-$rollbackShort-$timestamp"

az acr repository show `
  --name adriouchmovieacr `
  --image "classifieur-films-api:$rollbackCommit" `
  --output table

az containerapp update `
  --name adriouch-modeleia-api `
  --resource-group adriouchRG `
  --image $rollbackImage `
  --revision-suffix $rollbackSuffix `
  --output none
```

Répéter tous les contrôles de la section 3 et vérifier que les
fonctionnalités propres à la version retirée ont disparu.

## 5. Journal réel

| Date       | Commit          | Révision Azure                             | Opération              | Résultat |
| ---------- | --------------- | ------------------------------------------- | ----------------------- | --------- |
| 2026-10-25 | `a13ec169...` | `adriouch-modeleia-api--2dwkro0`          | Déploiement V1         | Validé   |
| 2026-10-28 | `c8a90ccf...` | `adriouch-modeleia-api--hello-c8a90cc`    | Déploiement `/hello` | Validé   |
| 2026-10-28 | `a13ec169...` | `adriouch-modeleia-api--rollback-a13ec16` | Retour arrière         | Validé   |

État actuel : `a13ec169...` est actif, `/hello` retourne `404`, tandis
que `/health` et `/predict` restent opérationnelles.

Preuves :

- `evidence/azure/deployment_verification.txt` ;
- `evidence/azure/trainer_validation.txt` ;
- `evidence/azure/hello_and_rollback_verification.txt`.
