# Organisation des dépôts

## Dépôt public actuel

| Rôle | Dépôt |
|---|---|
| Catalogue, Releases, documentation et Pages | [ICANSII/icansii-sidestore](https://github.com/ICANSII/icansii-sidestore) |

## Dépôts publics prévus

| Rôle | Dépôt |
|---|---|
| Code source ICANSII 5 | `https://github.com/ICANSII/icansii-v5` |
| Code source ICANSII 6 | `https://github.com/ICANSII/icansii-v6` |

Ces deux liens ne doivent être annoncés comme disponibles qu’après publication
effective des dépôts.

## Références internes

Le projet GitLab historique et ses branches internes doivent être référencés
dans Microsoft Loop ou Teams, pas dans cette documentation publique.

Organisation recommandée dans Loop :

```text
ICANSII
├── Documentation publique
├── Catalogue SideStore
├── GitLab historique
│   ├── branche swift/v5
│   └── branche swift/v6
├── Runbook de démonstration interne
└── Dépôts GitHub finaux
    ├── icansii-v5
    └── icansii-v6
```

Microsoft Loop sert d’index interne. GitHub Pages reste la référence publique
pour l’installation et le déploiement reproductible.
