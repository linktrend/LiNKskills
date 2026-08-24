import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
ALLOWED = ("skills/sales-customer-management/", "tests/skills/sales_customer_management/")


class ScopeAndEvidenceTests(unittest.TestCase):
    def test_fixture_and_skill_scope_are_safe(self):
        for path in (ROOT / "skills" / "sales-customer-management").rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                self.assertNotIn("sk_live_", text)
                self.assertNotIn("BEGIN PRIVATE KEY", text)
                self.assertNotIn("customer@example.com", text)

    def test_prohibited_paths_are_not_inside_packet(self):
        self.assertFalse((ROOT / "skills" / "sales-customer-management" / "tools").exists())
        self.assertFalse((ROOT / "skills" / "sales-customer-management" / "catalog" / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
