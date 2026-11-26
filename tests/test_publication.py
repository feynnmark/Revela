import unittest
from pathlib import Path

from tools.collect_licenses import is_license_document


class LicenseCollectionTests(unittest.TestCase):
    def test_python_caches_are_not_license_documents(self):
        for file in ('package/licenses/__pycache__/module.pyc', 'package/licenses/__init__.py', 'package/licenses/_spdx.py', 'package/LICENSE.pyc'):
            with self.subTest(file=file):
                self.assertFalse(is_license_document(Path(file)))

    def test_original_license_notices_are_kept(self):
        for file in ('package.dist-info/licenses/LICENSE', 'package.dist-info/LICENSE.LibRaw', 'package/licenses/NOTICE.txt', 'package/COPYING.LESSER', 'package/licenses/codec.txt'):
            with self.subTest(file=file):
                self.assertTrue(is_license_document(Path(file)))


if __name__ == '__main__':
    unittest.main()
