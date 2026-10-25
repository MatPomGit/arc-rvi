import tempfile
from pathlib import Path
import unittest

from scripts.check_names import scan_text_files


class NameGuardTests(unittest.TestCase):
    def test_detects_external_token_without_echoing_it(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fixture.txt"
            source.write_text("alpha beta gamma", encoding="utf-8")
            self.assertEqual(scan_text_files([source], ["BETA"]), [(source.as_posix(), 1)])

    def test_ignores_unmatched_token(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "fixture.txt"
            source.write_text("ordinary content", encoding="utf-8")
            self.assertEqual(scan_text_files([source], ["unmatched"]), [])


if __name__ == "__main__":
    unittest.main()
