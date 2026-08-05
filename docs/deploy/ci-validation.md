# Validation automatique des Releases

La CI empêche la publication d’un catalogue SideStore incohérent. Elle compare
le contenu de `apps.json` avec les Releases réellement publiées dans
`ICANSII/icansii-sidestore`.

## Événements surveillés

Le workflow s’exécute lors de :

- chaque push sur `main` ;
- chaque pull request vers `main` ;
- la publication d’une Release ;
- la modification d’une Release ;
- un lancement manuel depuis l’onglet **Actions**.

Lors d’un événement Release, GitHub positionne normalement le workflow sur le
commit du tag. Le workflow ICANSII récupère explicitement la branche par défaut
afin de valider le `apps.json` actuellement destiné à GitHub Pages.

## Contrôles locaux

À chaque pull request et à chaque publication, la CI vérifie :

- la syntaxe de `apps.json` ;
- la casse `ICANSII` ;
- les champs indispensables ;
- les bundle identifiers uniques ;
- l’ordre décroissant des versions ;
- les noms `ICANSII-vX.Y.Z.ipa` ;
- les chemins des icônes et captures ;
- la cohérence des champs de compatibilité supérieurs avec `versions[0]` ;
- les tests automatisés du validateur ;
- la construction stricte du site MkDocs.

## Contrôles avec GitHub

Sur `main`, lors d’une Release et lors d’un lancement manuel, la CI interroge
l’API REST GitHub et vérifie pour chaque version :

- l’existence de la Release `vX.Y.Z` ;
- son état publié, stable et non brouillon ;
- l’existence exacte de l’asset `ICANSII-vX.Y.Z.ipa` ;
- l’état complètement téléversé de l’asset ;
- l’égalité de l’URL GitHub et du `downloadURL` ;
- l’égalité de la taille GitHub et du champ `size` ;
- l’absence d’asset stable orphelin non référencé dans `apps.json` ;
- l’absence d’ancien nom public utilisant `ICanSii`.

Les préversions et les brouillons non référencés sont ignorés lors de la
recherche d’assets orphelins.

## L’ordre des opérations peut être inversé

### `apps.json` est poussé avant la Release

```text
Push sur main
→ la Release manque
→ validation rouge
→ aucun nouveau déploiement Pages
→ l’ancien catalogue public reste disponible

Publication de la Release
→ nouvelle validation
→ cohérence trouvée
→ déploiement du nouveau catalogue
```

### La Release est publiée avant `apps.json`

```text
Publication de la Release
→ l’asset n’est pas encore référencé
→ validation rouge
→ aucun déploiement

Push du nouveau apps.json
→ nouvelle validation
→ cohérence trouvée
→ déploiement du nouveau catalogue
```

Une CI rouge temporaire entre les deux opérations est donc normale. Elle ne
signifie pas que le catalogue public a été cassé : le job de déploiement ne
s’exécute qu’après une validation complète.

## Course normale lors de `gh release create`

GitHub CLI crée la Release puis téléverse l’asset. L’événement `published` peut
être reçu pendant ce court intervalle. Le workflow effectue jusqu’à six
nouvelles tentatives espacées de dix secondes lors de la publication d’une
Release.

Si l’asset est ajouté bien plus tard, relancez le workflow manuellement :

```text
Actions
→ Documentation and SideStore source
→ Run workflow
```

Une modification de la Release déclenche également une nouvelle validation.

## Ce que la CI ne fait pas

La CI ne supprime pas une Release incorrecte et ne modifie pas automatiquement
`apps.json`. Elle bloque uniquement le nouveau déploiement et produit un
message précis. La correction reste explicite et traçable dans Git.

## Vérification distante en local

Utilisez de préférence l’environnement du projet :

```bash
make install
export GITHUB_TOKEN="$(gh auth token)"
make validate-releases
```

Le validateur utilise un contexte TLS vérifié. Il donne la priorité à
`SSL_CERT_FILE` lorsqu’un bundle CA d’entreprise est configuré, utilise ensuite
le bundle public de `certifi`, puis le magasin par défaut de Python.

Une erreur `CERTIFICATE_VERIFY_FAILED` provient du magasin de certificats du
Python local, et non du contenu de `apps.json` ni du jeton GitHub. Consultez la
page [Dépannage](../support/troubleshooting.md#le-validateur-echoue-avec-certificate_verify_failed).
