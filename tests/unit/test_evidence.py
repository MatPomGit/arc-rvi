import hashlib
from pathlib import Path
import tempfile
import unittest

from rvi.evidence import build_image_manifest, sha256_file


class EvidenceTests(unittest.TestCase):
    def test_manifest_hash_and_relative_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "images").mkdir()
            sample = root / "images" / "a.bin"
            sample.write_bytes(b"synthetic")
            manifest = build_image_manifest(root, [sample])
            self.assertEqual(manifest[0]["relative_path"], "images/a.bin")
            self.assertEqual(manifest[0]["size_bytes"], 9)
            self.assertEqual(manifest[0]["sha256"], hashlib.sha256(b"synthetic").hexdigest())
            self.assertEqual(manifest[0]["sha256"], sha256_file(sample))

    def test_out_of_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "run").mkdir()
            external = root / "external.bin"
            external.write_bytes(b"secret")
            with self.assertRaises(ValueError):
                build_image_manifest(root / "run", [external])

    def test_duplicate_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample = root / "a.bin"
            sample.write_bytes(b"data")
            with self.assertRaises(ValueError):
                build_image_manifest(root, [sample, sample])

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample = root / "a.bin"
            sample.write_bytes(b"data")
            link = root / "link.bin"
            try:
                link.symlink_to(sample)
            except (NotImplementedError, OSError):
                self.skipTest("symlink support unavailable")
            with self.assertRaises(ValueError):
                build_image_manifest(root, [link])


if __name__ == "__main__":
    unittest.main()
