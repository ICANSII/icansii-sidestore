# Contribuer à la documentation ICANSII

## Prévisualisation locale

```bash
make install
make serve
```

Le site est généralement disponible sur `http://127.0.0.1:8000/`.

## Vérification locale complète

```bash
make validate
```

Cette commande :

1. exécute les tests du validateur ;
2. valide la structure locale de `apps.json` ;
3. vérifie les noms `ICANSII-vX.Y.Z.ipa` ;
4. vérifie que les captures et icônes locales existent ;
5. construit la documentation en mode strict.

## Vérification des Releases GitHub

Après la publication des assets, utilisez l’environnement du projet afin de
bénéficier du bundle de certificats installé avec `certifi` :

```bash
make install
make validate-releases
```

Pour bénéficier d’une limite API supérieure, exportez un jeton ou utilisez le
jeton déjà fourni par GitHub CLI :

```bash
export GITHUB_TOKEN="$(gh auth token)"
make validate-releases
```

La commande vérifie les Releases, les noms d’assets, les URL, les tailles et
les éventuels IPA publics non référencés dans `apps.json`. En cas d’erreur TLS
`CERTIFICATE_VERIFY_FAILED`, consultez la page **Dépannage** du site.

## Règles de publication

- Toujours écrire la marque **ICANSII** en majuscules.
- Conserver les bundle identifiers en minuscules, par exemple `fr.icansii.app.v5`.
- Nommer un IPA `ICANSII-vX.Y.Z.ipa`.
- Classer les versions de la plus récente à la plus ancienne.
- Conserver les anciennes versions dans `versions` tant que leurs Releases
  publiques existent.
- Ne jamais publier d’identifiant Apple, de fichier d’appairage, d’UDID ou de
  secret interne.

## CI rouge entre deux étapes

La création d’une version est une opération composée : la Release et
`apps.json` ne peuvent pas devenir visibles exactement au même instant.
Une validation rouge temporaire est normale. GitHub Pages ne remplace le
catalogue public qu’après cohérence complète.
