#!/usr/bin/env python3
"""Run every modular unit, integration, and GUI headless test."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


TEST_DIR = Path(__file__).resolve().parent
ROOT = TEST_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_test_module(path: Path) -> ModuleType:
    """Load one test module without requiring third-party test runners."""
    module_name = f"ludo_test_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def build_suite() -> unittest.TestSuite:
    """Collect all test modules except the aggregate runner and fuzz suite."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    excluded = {"test_suite.py", "parity_test.py"}
    for path in sorted(TEST_DIR.glob("test_*.py")):
        if path.name in excluded:
            continue
        suite.addTests(loader.loadTestsFromModule(load_test_module(path)))
    return suite


def main() -> int:
    """Execute the complete standard-library test suite."""
    suite = build_suite()
    print(f"Collected {suite.countTestCases()} modular tests.")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
