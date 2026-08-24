import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]


class ScopeAndEvidenceTests(unittest.TestCase):
    def test_no_live_or_private_material_markers(self):
        for path in (ROOT / "skills" / "procurement-vendor-management").rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                for marker in ("sk_live_", "BEGIN PRIVATE KEY", "customer@example.com"):
                    self.assertNotIn(marker, text, str(path))

    def test_prohibited_paths_are_absent(self):
        skill = ROOT / "skills" / "procurement-vendor-management"
        self.assertFalse((skill / "tools").exists())
        self.assertFalse((skill / "catalog" / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
