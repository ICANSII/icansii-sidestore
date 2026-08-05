# Déploiement

La chaîne publique de distribution est centralisée dans :

```text
https://github.com/ICANSII/icansii-sidestore
```

Elle contient :

- le catalogue `apps.json` ;
- les icônes et captures ;
- les Releases IPA actuellement distribuées ;
- la documentation publique ;
- la CI GitHub Pages.

## Cycle d’une version

```text
Projet Xcode
→ archive .xcarchive
→ création de l’IPA
→ contrôle des métadonnées et de la taille
→ GitHub Release
→ mise à jour de apps.json
→ validation CI
→ publication GitHub Pages
```

## Public et interne

Le site public peut contenir le processus reproductible d’export et de
publication. En revanche, les éléments suivants doivent rester dans Microsoft
Loop, Teams ou un dépôt privé :

- comptes Apple utilisés pour les démonstrations ;
- fichiers d’appairage ;
- UDID des appareils ;
- liens GitLab internes ;
- informations opérationnelles ou identifiants d’entreprise.

Le runbook public est donc volontairement limité aux opérations techniques
sans secret.
