import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]


def _iter_scannable_files(root):
    """Yield source files while excluding generated Python bytecode caches."""
    return (
        path
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


class ScopeAndEvidenceTests(unittest.TestCase):
    def test_no_live_or_private_material_markers(self):
        for path in _iter_scannable_files(ROOT / "skills" / "procurement-vendor-management"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for marker in ("sk_live_", "BEGIN PRIVATE KEY", "customer@example.com"):
                self.assertNotIn(marker, text, str(path))

    def test_generated_bytecode_is_excluded_from_marker_scan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            source = root / "source.txt"
            source.write_text("safe source", encoding="utf-8")
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "helper_tool.cpython-312.pyc").write_bytes(b"BEGIN PRIVATE KEY")

            self.assertEqual((source,), tuple(_iter_scannable_files(root)))

    def test_prohibited_paths_are_absent(self):
        skill = ROOT / "skills" / "procurement-vendor-management"
        self.assertFalse((skill / "tools").exists())
        self.assertFalse((skill / "catalog" / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
