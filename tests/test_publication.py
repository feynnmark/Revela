import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from tools.collect_licenses import is_license_document
from tools.audit_public import Audit


class LicenseCollectionTests(unittest.TestCase):
    def test_python_caches_are_not_license_documents(self):
        for file in ('package/licenses/__pycache__/module.pyc', 'package/licenses/__init__.py', 'package/licenses/_spdx.py', 'package/LICENSE.pyc'):
            with self.subTest(file=file):
                self.assertFalse(is_license_document(Path(file)))

    def test_original_license_notices_are_kept(self):
        for file in ('package.dist-info/licenses/LICENSE', 'package.dist-info/LICENSE.LibRaw', 'package/licenses/NOTICE.txt', 'package/COPYING.LESSER', 'package/licenses/codec.txt'):
            with self.subTest(file=file):
                self.assertTrue(is_license_document(Path(file)))


class PublicAuditTests(unittest.TestCase):
    def test_private_profile_is_rejected_even_in_upstream_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder) / 'private-account'
            with patch('pathlib.Path.home', return_value=profile):
                audit = Audit()
            audit.inspect('Revela.exe/numpy.lib._datasource', str(profile / 'file').encode('utf-8'))
            self.assertTrue(any(rule == 'local-profile-path' for _, rule in audit.findings))

    def test_known_public_github_runner_is_not_a_private_profile(self):
        profile = Path('C:/') / 'Users' / 'runneradmin'
        with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}), patch('pathlib.Path.home', return_value=profile):
            audit = Audit()
        audit.inspect('upstream-build-metadata', str(profile / 'build').encode('utf-8'))
        self.assertFalse(audit.findings)

    def test_ci_environment_does_not_exempt_a_private_account(self):
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder) / 'private-account'
            with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true', 'RUNNER_ENVIRONMENT': 'github-hosted'}), patch('pathlib.Path.home', return_value=profile):
                audit = Audit()
            audit.inspect('metadata', str(profile / 'file').encode('utf-8'))
            self.assertTrue(any(rule == 'local-profile-path' for _, rule in audit.findings))


if __name__ == '__main__':
    unittest.main()
