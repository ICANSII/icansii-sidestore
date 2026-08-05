# Publier une version

L’asset IPA et son entrée dans `apps.json` doivent finalement être cohérents.
La CI accepte les deux ordres de travail et ne déploie le nouveau catalogue que
lorsque les deux éléments existent.

La procédure recommandée reste :

```text
mise à jour de apps.json
→ commit
→ tag annoté
→ push du commit et du tag
→ création de la Release avec l’IPA
→ validation et déploiement automatiques
```

!!! info "CI rouge temporaire"
    Après le push du JSON et avant la publication de la Release, la validation
    distante peut être rouge. C’est attendu : GitHub Pages conserve la dernière
    version valide. La publication de la Release relance automatiquement la CI.

## 1. Préparer la version

Créez l’IPA final et relevez sa taille exacte. Mettez ensuite à jour
`apps.json` :

- ajoutez la nouvelle version au début de `versions` ;
- conservez les versions précédentes en dessous ;
- mettez à jour `version`, `versionDate`, `versionDescription`, `downloadURL`
  et `size` au niveau supérieur s’ils sont présents ;
- ne modifiez pas l’autre application si elle n’a pas changé.

Exécutez les validations locales :

```bash
python3 scripts/validate_source.py apps.json \
  --repository ICANSII/icansii-sidestore
python3 -m unittest discover --start-directory tests --verbose
```

## 2. Créer le commit et le tag

Synchronisez d’abord la branche :

```bash
git switch main
git pull --ff-only origin main
```

Créez le commit de publication :

```bash
git add apps.json docs/
git commit -m "Publish ICANSII 6.1.0"
```

Créez un tag annoté sur ce commit précis :

```bash
git tag -a v6.1.0 -m "ICANSII 6.1.0"
git show v6.1.0 --no-patch
```

Poussez le commit et le tag dans une même transaction :

```bash
git push --atomic origin main v6.1.0
```

Ne déplacez pas un tag déjà publié. Une correction doit recevoir un nouveau
numéro de version.

## 3. Créer la Release

### Avec GitHub CLI

> Si GitHub CLI n’est pas installé, suivez les instructions sur
> <https://cli.github.com/>, puis exécutez `gh auth login`.

Dans le répertoire où se trouve l’IPA :

```bash
gh release create v6.1.0 \
  ./ICANSII-v6.1.0.ipa \
  --repo ICANSII/icansii-sidestore \
  --verify-tag \
  --title "ICANSII 6.1.0" \
  --notes "Version publique avec stimuli haptiques améliorés."
```

`--verify-tag` interdit à GitHub CLI de fabriquer implicitement le tag sur un
autre commit.

Pour ICANSII 5 :

```bash
gh release create v5.1.0 \
  ./ICANSII-v5.1.0.ipa \
  --repo ICANSII/icansii-sidestore \
  --verify-tag \
  --title "ICANSII 5.1.0" \
  --notes "Description de la version ICANSII 5.1.0."
```

### Avec GitHub Web

1. Allez sur la page des [Releases](https://github.com/ICANSII/icansii-sidestore/releases).
2. Cliquez sur **Draft a new release**.
3. Ouvrez **Choose a tag**.
4. Sélectionnez le tag existant, par exemple `v6.1.0`.
5. Ne choisissez pas **Create new tag**.
6. Entrez le titre et les notes de version.
7. Glissez l’IPA dans la zone **Attach binaries by dropping them here or selecting them**.
8. Attendez que le téléversement soit terminé.
9. Cliquez sur **Publish release**.

## 4. Vérifier la Release

L’URL doit déclencher le téléchargement :

```text
https://github.com/ICANSII/icansii-sidestore/releases/download/v6.1.0/ICANSII-v6.1.0.ipa
```

Suivez ensuite le workflow :

```text
Actions
→ Documentation and SideStore source
```

Lorsque la validation est verte, la CI republie automatiquement :

```text
https://icansii.github.io/icansii-sidestore/apps.json
```

## 5. En cas d’ordre inversé

Une personne peut publier la Release avant de modifier `apps.json`. Dans ce
cas, la CI signale un **asset publié non référencé**. Il suffit ensuite de :

```bash
git switch main
git pull --ff-only origin main
# modifier apps.json
git add apps.json
git commit -m "Reference ICANSII 6.1.0 in SideStore source"
git push
```

Le push relance la validation et déploie le catalogue si tout correspond.

[Comprendre la validation automatique](ci-validation.md){ .md-button }
