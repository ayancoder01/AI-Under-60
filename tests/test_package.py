from pathlib import Path
import sys
import unittest

# Ensure src directory is on sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))



class TestPackage(unittest.TestCase):
    """Test package importability and metadata."""

    def test_package_import(self) -> None:
        """Verify the package can be imported and has version metadata."""
        import ai_under_60

        self.assertTrue(hasattr(ai_under_60, "__version__"))
        self.assertIsInstance(ai_under_60.__version__, str)
        self.assertEqual(ai_under_60.__version__, "0.1.0")

    def test_health_check_exported(self) -> None:
        """Verify health_check is exported at the package root."""
        from ai_under_60 import health_check

        self.assertTrue(callable(health_check))

    def test_generate_text_exported(self) -> None:
        """Verify generate_text is exported at the package root."""
        from ai_under_60 import generate_text

        self.assertTrue(callable(generate_text))


    def test_submodules_import(self) -> None:
        """Verify internal submodules can be imported cleanly."""
        from ai_under_60 import ai, config, content, logger, main

        self.assertIsNotNone(ai)
        self.assertIsNotNone(config)
        self.assertIsNotNone(content)
        self.assertIsNotNone(logger)
        self.assertIsNotNone(main)



if __name__ == "__main__":
    unittest.main()
