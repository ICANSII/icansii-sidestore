# Vérifications avant publication

## IPA

- [ ] Le nom utilise `ICANSII` en majuscules.
- [ ] Le nom suit `ICANSII-vX.Y.Z.ipa`.
- [ ] L’archive contient exactement une application dans `Payload/`.
- [ ] Le bundle identifier est celui de la bonne application.
- [ ] `CFBundleShortVersionString` correspond à la version publiée.
- [ ] `CFBundleVersion` a été incrémenté.
- [ ] L’IPA a été testé sur un appareil.

## GitHub Release

- [ ] Le tag correspond à la version.
- [ ] L’asset IPA a le bon nom.
- [ ] L’URL directe télécharge effectivement l’IPA.
- [ ] La taille en octets a été relevée après l’export final.

## `apps.json`

- [ ] Aucune occurrence de `ICanSii` ne subsiste.
- [ ] Les bundle identifiers V5 et V6 sont distincts.
- [ ] La dernière version est placée en premier.
- [ ] `downloadURL` correspond exactement au nom de l’asset.
- [ ] `size` est un nombre sans guillemets.
- [ ] Les icônes et captures répondent sur GitHub Pages.

## CI et publication

- [ ] `python3 scripts/validate_source.py apps.json` réussit.
- [ ] `mkdocs build --strict` réussit.
- [ ] Le workflow GitHub Actions est vert.
- [ ] `/apps.json` affiche la dernière révision.
- [ ] L’ajout de la source fonctionne depuis Safari sur iPhone.
