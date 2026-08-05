# Dépannage

## SideStore demande LocalDevVPN

Symptôme : SideStore refuse d’installer, de mettre à jour ou d’actualiser une
application.

Solution :

1. ouvrez LocalDevVPN ;
2. touchez **Connect** ;
3. revenez dans SideStore ;
4. relancez l’opération.

## SideStore ne détermine pas l’UDID

Message :

```text
SideStore could not determine this device's UDID.
Please replace your pairing using iloader.
```

1. Connectez l’iPhone au PC par USB.
2. Dans SideStore, ouvrez **Settings → Reset Pairing File**.
3. Dans iloader, supprimez le pairing stocké si nécessaire.
4. Refaire l’appairage avec l’iPhone.
5. Dans **Manage Pairing File**, utilisez **Place** pour SideStore.
6. Fermez complètement SideStore.
7. Connectez LocalDevVPN.
8. Rouvrez SideStore.


## Le validateur échoue avec `CERTIFICATE_VERIFY_FAILED`

Message typique :

```text
API GitHub inaccessible pour https://api.github.com/...:
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate
```

La validation locale de `apps.json` a déjà réussi. L’échec concerne uniquement
la vérification TLS effectuée par le Python local avant l’appel à l’API GitHub.
Le jeton `GITHUB_TOKEN` n’est pas en cause.

### Solution recommandée

Utilisez l’environnement Python du projet, qui installe un bundle de
certificats publics avec `certifi` :

```bash
make install
export GITHUB_TOKEN="$(gh auth token)"
make validate-releases
```

### Python installé depuis python.org sur macOS

Exécutez le script fourni avec la version de Python installée :

```bash
open "/Applications/Python 3.13/Install Certificates.command"
```

Adaptez `3.13` à la version présente dans `/Applications`, puis relancez :

```bash
make validate-releases
```

### Réseau d’entreprise avec autorité de certification interne

Demandez le bundle CA à l’équipe informatique, puis indiquez-le explicitement :

```bash
export SSL_CERT_FILE="/chemin/vers/entreprise-ca.pem"
export GITHUB_TOKEN="$(gh auth token)"
make validate-releases
```

!!! danger "Ne pas désactiver la vérification TLS"
    N’ajoutez pas de mode `--insecure` et ne remplacez pas le contexte SSL par
    un contexte non vérifié. Cela masquerait le problème tout en supprimant la
    vérification de l’identité de `api.github.com`.

## La source ICANSII ne se charge pas

Vérifiez dans Safari :

```text
https://icansii.github.io/icansii-sidestore/apps.json
```

Si le fichier ne s’affiche pas :

- vérifiez le workflow GitHub Actions ;
- vérifiez que GitHub Pages utilise **GitHub Actions** comme source ;
- vérifiez la validité de `apps.json`.

## L’installation d’une troisième application échoue

Avec un compte Apple gratuit, SideStore utilise déjà un emplacement.
ICANSII 5 et ICANSII 6 utilisent les deux autres. Supprimez une autre
application sideloadée ou n’installez qu’une version d’ICANSII.
