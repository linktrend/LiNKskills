import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]


class ScopeAndEvidenceTests(unittest.TestCase):
    def test_skill_contains_no_live_or_privileged_material_markers(self):
        for path in (ROOT / "skills" / "commercial-contracts-legal-operations").rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                for marker in ("sk_live_", "BEGIN PRIVATE KEY", "customer@example.com"):
                    self.assertNotIn(marker, text, str(path))

    def test_prohibited_paths_are_not_inside_packet(self):
        self.assertFalse((ROOT / "skills" / "commercial-contracts-legal-operations" / "tools").exists())
        self.assertFalse((ROOT / "skills" / "commercial-contracts-legal-operations" / "catalog" / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
