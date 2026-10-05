"""Registry discovery must agree with the canonical catalog boundary."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.skill_runtime.catalog import discover_skill_dirs as catalog_skill_dirs
from validator import discover_skill_dirs


class ValidatorSkillDiscoveryTests(unittest.TestCase):
    def test_missing_registry_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(discover_skill_dirs(Path(tmp) / "skills"), [])

    def test_archived_upstream_packages_are_not_registry_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills = root / "skills"
            for relative in (
                "alpha/SKILL.md",
                "beta/SKILL.md",
                "alpha/references/upstream/vendor/skills/source/SKILL.md",
                "beta/references/library/SKILL.md",
            ):
                path = skills / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Archived or active skill content\n", encoding="utf-8")
            expected = [(skills / "alpha").resolve(), (skills / "beta").resolve()]
            self.assertEqual(discover_skill_dirs(skills), expected)
            self.assertEqual(discover_skill_dirs(skills), catalog_skill_dirs(root))

    def test_invalid_active_entrypoints_are_still_discovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            active = skills / "invalid-active"
            active.mkdir(parents=True)
            (active / "SKILL.md").write_text("Not valid frontmatter\n", encoding="utf-8")
            (skills / "directory-only" / "SKILL.md").mkdir(parents=True)
            self.assertEqual(discover_skill_dirs(skills), [active.resolve()])


if __name__ == "__main__":
    unittest.main()
