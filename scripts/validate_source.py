#!/usr/bin/env python3
"""Validate the ICANSII SideStore source and its published GitHub Releases."""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

try:
    import certifi
except ImportError:  # pragma: no cover - optional fallback outside the project venv
    certifi = None


GITHUB_API_VERSION = "2026-03-10"
DEFAULT_REPOSITORY = "ICANSII/icansii-sidestore"
STABLE_IPA_PATTERN = re.compile(r"^ICANSII-v(?P<version>\d+\.\d+\.\d+)\.ipa$")

REQUIRED_APP_FIELDS = {
    "name",
    "bundleIdentifier",
    "developerName",
    "localizedDescription",
    "iconURL",
    "versions",
}

REQUIRED_VERSION_FIELDS = {
    "version",
    "date",
    "downloadURL",
    "size",
}


class ValidationError(RuntimeError):
    """Raised when apps.json and the published Releases are inconsistent."""


@dataclass(frozen=True)
class ExpectedAsset:
    app_name: str
    version: str
    tag_name: str
    asset_name: str
    download_url: str
    size: int


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def version_key(value: str) -> tuple[int, ...]:
    try:
        parts = tuple(int(part) for part in value.split("."))
    except ValueError as exc:
        raise ValidationError(f"Version non numérique: {value}") from exc

    if len(parts) != 3:
        raise ValidationError(
            f"Version invalide: {value}. Utiliser exactement le format X.Y.Z."
        )
    return parts


def local_pages_path(url: str, repository_root: Path) -> Path | None:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "icansii.github.io":
        return None

    prefix = "/icansii-sidestore/"
    if not parsed.path.startswith(prefix):
        return None

    relative = parsed.path[len(prefix) :]
    return repository_root / relative


def expected_release_url(repository: str, version: str) -> str:
    return (
        f"https://github.com/{repository}/releases/download/"
        f"v{version}/ICANSII-v{version}.ipa"
    )


def build_ssl_context() -> ssl.SSLContext:
    """Create a verified TLS context for GitHub API requests.

    An explicitly configured SSL_CERT_FILE has priority so corporate or
    organization-specific certificate authorities remain supported. The
    project environment otherwise uses certifi's public CA bundle when it is
    installed, then falls back to Python's default trust configuration.
    """

    explicit_ca_file = os.environ.get("SSL_CERT_FILE")
    if explicit_ca_file:
        return ssl.create_default_context(cafile=explicit_ca_file)

    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())

    return ssl.create_default_context()


def describe_url_error(reason: object) -> str:
    """Return an actionable, secure message for a network failure."""

    if isinstance(reason, ssl.SSLCertVerificationError):
        return (
            f"{reason}. Le certificat TLS n’a pas pu être validé. "
            "Utilisez d’abord l’environnement du projet (`make install`, puis "
            "`make validate-releases`), qui installe certifi. Avec le Python "
            "officiel de macOS, exécutez aussi `Install Certificates.command` "
            "dans `/Applications/Python 3.x/`. Sur un réseau d’entreprise, "
            "définissez `SSL_CERT_FILE` vers le bundle CA fourni par "
            "l’organisation. Ne désactivez pas la vérification TLS."
        )

    return str(reason)


def validate_local_source(
    source_path: Path,
    *,
    repository: str = DEFAULT_REPOSITORY,
) -> list[ExpectedAsset]:
    """Validate apps.json without network access and return expected Release assets."""

    source_path = source_path.resolve()
    require(source_path.is_file(), f"Fichier introuvable: {source_path}")

    raw = source_path.read_text(encoding="utf-8")
    require(
        "ICanSii" not in raw,
        "La casse historique « ICanSii » est encore présente. Utiliser « ICANSII ».",
    )

    try:
        source = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"JSON invalide à la ligne {exc.lineno}, colonne {exc.colno}: {exc.msg}"
        ) from exc

    require(source.get("name") == "ICANSII", 'Le champ racine "name" doit valoir "ICANSII".')

    apps = source.get("apps")
    require(isinstance(apps, list) and bool(apps), 'Le champ racine "apps" doit être une liste non vide.')

    repository_root = source_path.parent
    bundle_ids: set[str] = set()
    release_keys: set[tuple[str, str]] = set()
    expected_assets: list[ExpectedAsset] = []

    for app in apps:
        require(isinstance(app, dict), "Chaque entrée de apps doit être un objet JSON.")
        app_name = app.get("name", "<application sans nom>")

        missing = REQUIRED_APP_FIELDS - app.keys()
        require(
            not missing,
            f"{app_name}: champs manquants: {', '.join(sorted(missing))}",
        )

        bundle_id = app["bundleIdentifier"]
        require(bundle_id not in bundle_ids, f"Bundle identifier dupliqué: {bundle_id}")
        bundle_ids.add(bundle_id)

        require(
            isinstance(app_name, str) and app_name.startswith("ICANSII"),
            f'{app_name}: le nom doit commencer par "ICANSII".',
        )

        icon_path = local_pages_path(app["iconURL"], repository_root)
        if icon_path is not None:
            require(icon_path.is_file(), f"{app_name}: icône introuvable dans le dépôt: {icon_path}")

        for screenshot_url in app.get("screenshotURLs", []):
            screenshot_path = local_pages_path(screenshot_url, repository_root)
            if screenshot_path is not None:
                require(
                    screenshot_path.is_file(),
                    f"{app_name}: capture introuvable dans le dépôt: {screenshot_path}",
                )

        versions = app["versions"]
        require(
            isinstance(versions, list) and bool(versions),
            f"{app_name}: versions doit être une liste non vide.",
        )

        seen_versions: set[str] = set()
        parsed_versions: list[tuple[int, ...]] = []

        for version in versions:
            require(isinstance(version, dict), f"{app_name}: chaque version doit être un objet JSON.")
            missing = REQUIRED_VERSION_FIELDS - version.keys()
            require(
                not missing,
                f"{app_name}: version incomplète, champs manquants: {', '.join(sorted(missing))}",
            )

            value = version["version"]
            require(isinstance(value, str), f"{app_name}: version doit être une chaîne.")
            require(value not in seen_versions, f"{app_name}: version dupliquée: {value}")
            seen_versions.add(value)
            parsed_versions.append(version_key(value))

            size = version["size"]
            require(
                isinstance(size, int) and not isinstance(size, bool) and size > 0,
                f"{app_name} {value}: size doit être un entier strictement positif.",
            )

            tag_name = f"v{value}"
            asset_name = f"ICANSII-v{value}.ipa"
            canonical_url = expected_release_url(repository, value)
            download_url = version["downloadURL"]
            require(
                download_url == canonical_url,
                f"{app_name} {value}: URL GitHub Release attendue: {canonical_url}; reçue: {download_url}",
            )

            key = (tag_name, asset_name)
            require(key not in release_keys, f"Asset Release référencé plusieurs fois: {tag_name}/{asset_name}")
            release_keys.add(key)

            expected_assets.append(
                ExpectedAsset(
                    app_name=app_name,
                    version=value,
                    tag_name=tag_name,
                    asset_name=asset_name,
                    download_url=download_url,
                    size=size,
                )
            )

        require(
            parsed_versions == sorted(parsed_versions, reverse=True),
            f"{app_name}: les versions doivent être classées de la plus récente à la plus ancienne.",
        )

        newest = versions[0]
        compatibility_fields = {
            "version": newest["version"],
            "versionDate": newest["date"],
            "versionDescription": newest.get("localizedDescription"),
            "downloadURL": newest["downloadURL"],
            "size": newest["size"],
        }
        for field, expected_value in compatibility_fields.items():
            if field in app:
                require(
                    app[field] == expected_value,
                    f"{app_name}: le champ {field} supérieur ne correspond pas à la dernière version.",
                )

    return expected_assets


def is_published_stable_release(release: dict[str, Any]) -> bool:
    return bool(
        not release.get("draft")
        and not release.get("prerelease")
        and release.get("published_at")
    )


def validate_release_catalog(
    expected_assets: Iterable[ExpectedAsset],
    releases: list[dict[str, Any]],
) -> None:
    """Cross-check apps.json against published, stable GitHub Releases."""

    expected = list(expected_assets)
    releases_by_tag = {
        release.get("tag_name"): release
        for release in releases
        if isinstance(release, dict) and release.get("tag_name")
    }

    expected_keys = {(asset.tag_name, asset.asset_name) for asset in expected}

    for item in expected:
        release = releases_by_tag.get(item.tag_name)
        require(
            release is not None,
            f"{item.app_name} {item.version}: Release {item.tag_name} introuvable sur GitHub.",
        )
        require(
            not release.get("draft"),
            f"{item.app_name} {item.version}: la Release {item.tag_name} est encore en brouillon.",
        )
        require(
            not release.get("prerelease"),
            f"{item.app_name} {item.version}: la Release {item.tag_name} est marquée comme préversion.",
        )
        require(
            bool(release.get("published_at")),
            f"{item.app_name} {item.version}: la Release {item.tag_name} n’est pas publiée.",
        )

        assets = release.get("assets") or []
        matching = [asset for asset in assets if asset.get("name") == item.asset_name]
        require(
            len(matching) == 1,
            f"{item.app_name} {item.version}: asset {item.asset_name} introuvable dans la Release {item.tag_name}.",
        )
        asset = matching[0]

        require(
            asset.get("state") == "uploaded",
            f"{item.app_name} {item.version}: l’asset {item.asset_name} n’est pas complètement téléversé.",
        )
        require(
            asset.get("browser_download_url") == item.download_url,
            f"{item.app_name} {item.version}: URL GitHub réelle différente de apps.json. "
            f"GitHub: {asset.get('browser_download_url')}; apps.json: {item.download_url}",
        )
        require(
            asset.get("size") == item.size,
            f"{item.app_name} {item.version}: taille GitHub {asset.get('size')} octets, "
            f"mais apps.json déclare {item.size} octets.",
        )

    orphan_assets: list[str] = []
    legacy_assets: list[str] = []
    for release in releases:
        if not is_published_stable_release(release):
            continue
        tag_name = release.get("tag_name", "<tag inconnu>")
        for asset in release.get("assets") or []:
            asset_name = asset.get("name", "")
            if "ICanSii" in asset_name and asset_name.endswith(".ipa"):
                legacy_assets.append(f"{tag_name}/{asset_name}")
            if STABLE_IPA_PATTERN.fullmatch(asset_name) and (tag_name, asset_name) not in expected_keys:
                orphan_assets.append(f"{tag_name}/{asset_name}")

    require(
        not legacy_assets,
        "Release incohérente: asset public avec l’ancienne casse ICanSii: "
        + ", ".join(sorted(legacy_assets)),
    )
    require(
        not orphan_assets,
        "Release incohérente: asset publié non référencé dans apps.json: "
        + ", ".join(sorted(orphan_assets)),
    )


def fetch_github_releases(
    repository: str,
    *,
    token: str | None = None,
    api_url: str = "https://api.github.com",
) -> list[dict[str, Any]]:
    """Retrieve all repository Releases from the versioned GitHub REST API."""

    encoded_repository = "/".join(quote(part, safe="") for part in repository.split("/"))
    releases: list[dict[str, Any]] = []
    page = 1
    ssl_context = build_ssl_context()

    while True:
        url = f"{api_url.rstrip('/')}/repos/{encoded_repository}/releases?per_page=100&page={page}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ICANSII-SideStore-source-validator",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30, context=ssl_context) as response:
                payload = json.load(response)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ValidationError(
                f"API GitHub: HTTP {exc.code} pour {url}. {detail[:500]}"
            ) from exc
        except URLError as exc:
            raise ValidationError(
                f"API GitHub inaccessible pour {url}: {describe_url_error(exc.reason)}"
            ) from exc

        require(isinstance(payload, list), "API GitHub: la réponse List releases n’est pas une liste.")
        releases.extend(payload)
        if len(payload) < 100:
            break
        page += 1

    return releases


def validate_with_retries(
    expected_assets: list[ExpectedAsset],
    *,
    repository: str,
    token: str | None,
    retries: int,
    retry_delay: float,
) -> None:
    attempts = retries + 1
    last_error: ValidationError | None = None

    for attempt in range(1, attempts + 1):
        try:
            releases = fetch_github_releases(repository, token=token)
            validate_release_catalog(expected_assets, releases)
            return
        except ValidationError as exc:
            last_error = exc
            if attempt == attempts:
                break
            print(
                f"Validation GitHub non cohérente (tentative {attempt}/{attempts}): {exc}",
                file=sys.stderr,
            )
            print(f"Nouvelle tentative dans {retry_delay:g} seconde(s)…", file=sys.stderr)
            time.sleep(retry_delay)

    assert last_error is not None
    raise last_error


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valide apps.json et, en option, les Releases GitHub publiées."
    )
    parser.add_argument("source", nargs="?", default="apps.json", type=Path)
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY),
        help="Dépôt GitHub OWNER/REPO utilisé dans les downloadURL.",
    )
    parser.add_argument(
        "--check-releases",
        action="store_true",
        help="Interroge l’API GitHub et vérifie Releases, assets, URLs et tailles.",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="Jeton GitHub. Par défaut: variable GITHUB_TOKEN.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="Nombre de nouvelles tentatives de validation distante.",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=10.0,
        help="Délai en secondes entre deux tentatives.",
    )
    return parser.parse_args(argv)


def emit_error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        escaped = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Validation SideStore::{escaped}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        require(args.retries >= 0, "--retries doit être positif ou nul.")
        require(args.retry_delay >= 0, "--retry-delay doit être positif ou nul.")
        expected_assets = validate_local_source(args.source, repository=args.repository)
        print(
            f"OK local: {args.source} référence {len(expected_assets)} asset(s) IPA cohérent(s)."
        )

        if args.check_releases:
            validate_with_retries(
                expected_assets,
                repository=args.repository,
                token=args.github_token,
                retries=args.retries,
                retry_delay=args.retry_delay,
            )
            print(
                f"OK GitHub: les Releases publiées de {args.repository} correspondent à apps.json."
            )

        return 0
    except ValidationError as exc:
        emit_error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
