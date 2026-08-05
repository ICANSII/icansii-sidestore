# Runbook complet V5/V6

Ce runbook rassemble le chemin minimal entre une archive Xcode et une version
SideStore publiée.

## 1. Préparer les deux applications

```text
ICANSII 5
Bundle ID : fr.icansii.app.v5
IPA       : ICANSII-v5.0.0.ipa

ICANSII 6
Bundle ID : fr.icansii.app.v6
IPA       : ICANSII-v6.0.0.ipa
```

Chaque application possède son propre numéro de version et son propre numéro
de build.

## 2. Créer les IPA

Suivez la procédure détaillée :

[Exporter les IPA](export-ipa.md){ .md-button .md-button--primary }

Le dossier `.app` est renommé sans underscore avant la création de l’IPA. La
signature finale est recréée par SideStore pour le compte Apple de
l’utilisateur.

## 3. Vérifier l’archive

```bash
unzip -l ICANSII-v5.0.0.ipa | head -30
unzip -l ICANSII-v6.0.0.ipa | head -30
```

Vérifiez ensuite :

- `CFBundleIdentifier` ;
- `CFBundleShortVersionString` ;
- `CFBundleVersion`.

## 4. Relever les tailles

macOS :

```bash
stat -f%z ICANSII-v5.0.0.ipa
stat -f%z ICANSII-v6.0.0.ipa
```

Linux :

```bash
stat -c%s ICANSII-v5.0.0.ipa
stat -c%s ICANSII-v6.0.0.ipa
```

## 5. Publier les assets

Créez d’abord les GitHub Releases, puis téléversez les IPA.

[Publier une version](publish-release.md){ .md-button }

## 6. Mettre à jour la source

Dans `apps.json` :

1. ajoutez la version la plus récente en tête de `versions` ;
2. reportez l’URL directe de l’asset ;
3. reportez la taille exacte en octets ;
4. conservez l’historique ;
5. exécutez le validateur.

```bash
python3 scripts/validate_source.py apps.json
```

## 7. Publier GitHub Pages

```bash
git add apps.json
git commit -m "Publish ICANSII release"
git push
```

Le workflow construit MkDocs, copie les fichiers de distribution et déploie
l’ensemble sur GitHub Pages.

## 8. Installation de démonstration

Pour le parcours public, utilisez SideStore :

1. installer SideStore avec iloader ;
2. connecter LocalDevVPN ;
3. ajouter la source ICANSII ;
4. installer ICANSII 5 ou ICANSII 6 ;
5. actualiser les applications avant expiration.

Les identifiants Apple, fichiers d’appairage et détails propres au matériel de
démonstration doivent rester dans le runbook interne Microsoft Loop ou dans un
dépôt privé.
