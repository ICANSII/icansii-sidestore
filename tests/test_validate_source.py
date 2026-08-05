from __future__ import annotations

import json
import os
import ssl
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.validate_source import (
    ValidationError,
    build_ssl_context,
    describe_url_error,
    validate_local_source,
    validate_release_catalog,
)


REPOSITORY = "ICANSII/icansii-sidestore"


def source_document(*, version: str = "6.1.0", size: int = 25_036_467) -> dict:
    return {
        "name": "ICANSII",
        "identifier": "fr.icansii.sidestore",
        "sourceURL": "https://icansii.github.io/icansii-sidestore/apps.json",
        "apps": [
            {
                "name": "ICANSII 6",
                "bundleIdentifier": "fr.icansii.app.v6",
                "developerName": "SII Sud Ouest R&D",
                "localizedDescription": "Description",
                "iconURL": "https://example.com/icon.png",
                "version": version,
                "versionDate": "2026-08-05",
                "versionDescription": "Release",
                "downloadURL": (
                    f"https://github.com/{REPOSITORY}/releases/download/"
                    f"v{version}/ICANSII-v{version}.ipa"
                ),
                "size": size,
                "versions": [
                    {
                        "version": version,
                        "date": "2026-08-05",
                        "localizedDescription": "Release",
                        "downloadURL": (
                            f"https://github.com/{REPOSITORY}/releases/download/"
                            f"v{version}/ICANSII-v{version}.ipa"
                        ),
                        "size": size,
                    }
                ],
            }
        ],
        "news": [],
    }


def published_release(*, version: str = "6.1.0", size: int = 25_036_467) -> dict:
    return {
        "tag_name": f"v{version}",
        "draft": False,
        "prerelease": False,
        "published_at": "2026-08-05T12:00:00Z",
        "assets": [
            {
                "name": f"ICANSII-v{version}.ipa",
                "state": "uploaded",
                "size": size,
                "browser_download_url": (
                    f"https://github.com/{REPOSITORY}/releases/download/"
                    f"v{version}/ICANSII-v{version}.ipa"
                ),
            }
        ],
    }


class LocalValidationTests(unittest.TestCase):
    def write_source(self, document: dict, root: Path) -> Path:
        path = root / "apps.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_valid_source_produces_expected_release_asset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_source(source_document(), Path(directory))
            expected = validate_local_source(path, repository=REPOSITORY)

        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0].tag_name, "v6.1.0")
        self.assertEqual(expected[0].asset_name, "ICANSII-v6.1.0.ipa")
        self.assertEqual(expected[0].size, 25_036_467)

    def test_download_url_must_use_the_version_tag_and_canonical_asset_name(self) -> None:
        document = source_document()
        document["apps"][0]["versions"][0]["downloadURL"] = (
            f"https://github.com/{REPOSITORY}/releases/download/"
            "v6.0.0/ICANSII-v6.1.0.ipa"
        )
        document["apps"][0]["downloadURL"] = document["apps"][0]["versions"][0]["downloadURL"]

        with tempfile.TemporaryDirectory() as directory:
            path = self.write_source(document, Path(directory))
            with self.assertRaisesRegex(ValidationError, "URL GitHub Release attendue"):
                validate_local_source(path, repository=REPOSITORY)

    def test_top_level_compatibility_fields_must_match_latest_version(self) -> None:
        document = source_document()
        document["apps"][0]["versionDate"] = "2026-08-04"

        with tempfile.TemporaryDirectory() as directory:
            path = self.write_source(document, Path(directory))
            with self.assertRaisesRegex(ValidationError, "versionDate supérieur"):
                validate_local_source(path, repository=REPOSITORY)


class SSLConfigurationTests(unittest.TestCase):
    @patch("scripts.validate_source.ssl.create_default_context")
    def test_explicit_ssl_cert_file_has_priority(self, create_default_context) -> None:
        with patch.dict(os.environ, {"SSL_CERT_FILE": "/tmp/company-ca.pem"}, clear=False):
            build_ssl_context()

        create_default_context.assert_called_once_with(cafile="/tmp/company-ca.pem")

    def test_certificate_error_message_recommends_secure_repairs(self) -> None:
        reason = ssl.SSLCertVerificationError(1, "certificate verify failed")

        message = describe_url_error(reason)

        self.assertIn("Install Certificates.command", message)
        self.assertIn("certifi", message)
        self.assertIn("SSL_CERT_FILE", message)
        self.assertNotIn("désactiver", message.lower())


class ReleaseCatalogTests(unittest.TestCase):
    def expected_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "apps.json"
            path.write_text(json.dumps(source_document()), encoding="utf-8")
            return validate_local_source(path, repository=REPOSITORY)

    def test_matching_published_release_passes(self) -> None:
        validate_release_catalog(self.expected_assets(), [published_release()])

    def test_missing_release_fails(self) -> None:
        with self.assertRaisesRegex(ValidationError, "Release v6.1.0 introuvable"):
            validate_release_catalog(self.expected_assets(), [])

    def test_missing_asset_fails(self) -> None:
        release = published_release()
        release["assets"] = []
        with self.assertRaisesRegex(ValidationError, "asset ICANSII-v6.1.0.ipa introuvable"):
            validate_release_catalog(self.expected_assets(), [release])

    def test_size_mismatch_fails(self) -> None:
        release = published_release(size=25_036_468)
        with self.assertRaisesRegex(ValidationError, "taille GitHub 25036468"):
            validate_release_catalog(self.expected_assets(), [release])

    def test_orphan_stable_ipa_fails(self) -> None:
        orphan = published_release(version="6.2.0", size=26_000_000)
        with self.assertRaisesRegex(ValidationError, "asset publié non référencé"):
            validate_release_catalog(self.expected_assets(), [published_release(), orphan])

    def test_draft_and_prerelease_assets_are_ignored_for_orphan_check(self) -> None:
        draft = published_release(version="6.2.0", size=26_000_000)
        draft["draft"] = True
        prerelease = published_release(version="6.3.0", size=27_000_000)
        prerelease["prerelease"] = True

        validate_release_catalog(
            self.expected_assets(),
            [published_release(), draft, prerelease],
        )

    def test_referenced_prerelease_is_rejected(self) -> None:
        release = published_release()
        release["prerelease"] = True
        with self.assertRaisesRegex(ValidationError, "marquée comme préversion"):
            validate_release_catalog(self.expected_assets(), [release])

    def test_legacy_mixed_case_public_ipa_is_rejected(self) -> None:
        release = published_release()
        release["assets"].append(
            {
                "name": "ICanSii-v6.1.0.ipa",
                "state": "uploaded",
                "size": 25_036_467,
                "browser_download_url": (
                    f"https://github.com/{REPOSITORY}/releases/download/"
                    "v6.1.0/ICanSii-v6.1.0.ipa"
                ),
            }
        )
        with self.assertRaisesRegex(ValidationError, "ancienne casse ICanSii"):
            validate_release_catalog(self.expected_assets(), [release])


if __name__ == "__main__":
    unittest.main()
