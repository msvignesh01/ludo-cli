#!/usr/bin/env python3
"""Automated Perfection Gate Verifier for CIA1 Multiplayer Ludo.

Checks:
1. Static AST audit:
   - ludo_func.py MUST have 0 class definitions.
   - ludo_oop.py MUST define core OOP classes (Token, Player, Board, CLIRenderer, LudoGame).
2. Stdlib-only import audit (zero third-party dependencies).
3. CLI --help and invalid-arg smoke tests on both implementations.
4. Execution of testing/test_suite.py and testing/parity_test.py (if present).
5. Submission completeness & placeholder scan (for --stage final).

Usage:
    python scripts/verify_gates.py --stage v1
    python scripts/verify_gates.py --stage v2
    python scripts/verify_gates.py --stage final
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STDLIB_MODULES = set(getattr(sys, "stdlib_module_names", set()))
REQUIRED_OOP_CLASSES = {"Token", "Player", "Board", "CLIRenderer", "LudoGame"}


def get_imported_root_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                modules.add(node.module.split(".")[0])
    return modules


def audit_python_file(path: Path, expect_classes: bool) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Missing required file: {path.relative_to(ROOT)}"]

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"SyntaxError in {path.relative_to(ROOT)}: {exc}"]

    # 1. Class audit
    class_names = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    if expect_classes:
        missing = REQUIRED_OOP_CLASSES - set(class_names)
        if missing:
            errors.append(
                f"{path.relative_to(ROOT)}: Missing required OOP classes: {sorted(missing)}"
            )
    else:
        if class_names:
            errors.append(
                f"{path.relative_to(ROOT)}: VIOLATION — Functional version must have 0 classes, "
                f"found {class_names}"
            )

    # 2. Stdlib-only import audit
    imported = get_imported_root_modules(tree)
    non_stdlib = sorted(m for m in imported if m not in STDLIB_MODULES and m != "__future__")
    if non_stdlib:
        errors.append(
            f"{path.relative_to(ROOT)}: Non-stdlib imports detected: {non_stdlib}"
        )

    # 3. Placeholder check
    for marker in ("TODO", "FIXME", "NotImplementedError"):
        if marker in source:
            errors.append(f"{path.relative_to(ROOT)}: Contains unfinished marker '{marker}'")

    return errors


def smoke_test_cli(path: Path) -> list[str]:
    errors: list[str] = []
    # --help must succeed
    res_help = subprocess.run(
        [sys.executable, str(path), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if res_help.returncode != 0:
        errors.append(f"{path.relative_to(ROOT)} --help failed: {res_help.stderr.strip()}")
    for flag in ("--mode", "--seed", "--max-turns", "--no-color"):
        if flag not in res_help.stdout:
            errors.append(f"{path.relative_to(ROOT)} --help missing required flag {flag}")

    # --max-turns 0 must fail cleanly
    res_bad = subprocess.run(
        [sys.executable, str(path), "--max-turns", "0"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if res_bad.returncode == 0:
        errors.append(f"{path.relative_to(ROOT)} accepted invalid '--max-turns 0'")

    return errors


def run_test_script(script_path: Path, stage_dir: str) -> list[str]:
    if not script_path.exists():
        return [f"Missing test script: {script_path.relative_to(ROOT)}"]
    env = dict(**__import__("os").environ)
    env["LUDO_TARGET_DIR"] = stage_dir
    print(f"\n>>> Running {script_path.relative_to(ROOT)} against {stage_dir}/ ...")
    res = subprocess.run([sys.executable, str(script_path)], cwd=str(ROOT), env=env)
    if res.returncode != 0:
        return [f"Test script failed: {script_path.relative_to(ROOT)} (exit code {res.returncode})"]
    return []


def audit_final_submission() -> list[str]:
    errors: list[str] = []
    required_files = [
        "docs/01_game_design_document.md",
        "docs/02_flowchart_pseudocode.md",
        "docs/03_comparison_report.md",
        "docs/04_ai_interaction_log.md",
        "v1_initial/ludo_oop.py",
        "v1_initial/ludo_func.py",
        "testing/team1_report.md",
        "testing/team2_report.md",
        "v2_final/ludo_oop.py",
        "v2_final/ludo_func.py",
        "v2_final/CHANGELOG.md",
    ]
    for rel in required_files:
        p = ROOT / rel
        if not p.exists():
            errors.append(f"Missing final submission deliverable: {rel}")
            continue
        text = p.read_text(encoding="utf-8")
        if len(text.strip()) < 100:
            errors.append(f"Deliverable appears empty or stubbed: {rel}")
        for marker in ("TODO", "TBD", "[Fill from", "[Name 1"):
            if marker in text:
                errors.append(f"Unfilled placeholder '{marker}' found in {rel}")
    return errors


def verify_stage(stage_dir: str) -> list[str]:
    errors: list[str] = []
    oop_path = ROOT / stage_dir / "ludo_oop.py"
    func_path = ROOT / stage_dir / "ludo_func.py"

    print(f"=== Auditing {stage_dir}/ ===")
    errors.extend(audit_python_file(oop_path, expect_classes=True))
    errors.extend(audit_python_file(func_path, expect_classes=False))

    if not errors:
        errors.extend(smoke_test_cli(oop_path))
        errors.extend(smoke_test_cli(func_path))

    if not errors:
        errors.extend(run_test_script(ROOT / "testing" / "test_suite.py", stage_dir))
        errors.extend(run_test_script(ROOT / "testing" / "parity_test.py", stage_dir))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="CIA1 Ludo Perfection Gate Verifier")
    parser.add_argument(
        "--stage",
        choices=["v1", "v2", "final"],
        required=True,
        help="Verification stage to run",
    )
    args = parser.parse_args()

    errors: list[str] = []
    if args.stage == "v1":
        errors.extend(verify_stage("v1_initial"))
    elif args.stage == "v2":
        errors.extend(verify_stage("v2_final"))
    elif args.stage == "final":
        errors.extend(verify_stage("v1_initial"))
        errors.extend(verify_stage("v2_final"))
        errors.extend(audit_final_submission())

    print("\n" + "=" * 64)
    if errors:
        print(f"GATE FAILED ({len(errors)} issue(s)):")
        for idx, err in enumerate(errors, 1):
            print(f"  [{idx}] {err}")
        print("=" * 64)
        return 1

    print(f"GATE PASSED: Stage '{args.stage}' achieved 100% perfection!")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
