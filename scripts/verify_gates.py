#!/usr/bin/env python3
"""Audit modular Ludo packages and run every automated verification gate."""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STDLIB_MODULES = set(getattr(sys, "stdlib_module_names", set()))
REQUIRED_OOP_CLASSES = {"Token", "Player", "Board", "CLIRenderer", "LudoGame"}
REQUIRED_STAGE_FILES = (
    "ludo_oop.py",
    "ludo_func.py",
    "shared/__init__.py",
    "shared/contracts.py",
    "shared/cli_support.py",
    "shared/view.py",
    "shared/geometry.py",
    "shared/gui_support.py",
    "shared/gui_drawing.py",
    "oop_ludo/__init__.py",
    "oop_ludo/models.py",
    "oop_ludo/engine.py",
    "oop_ludo/bot.py",
    "oop_ludo/commentary.py",
    "oop_ludo/renderer.py",
    "oop_ludo/cli.py",
    "oop_ludo/gui_session.py",
    "oop_ludo/gui.py",
    "func_ludo/__init__.py",
    "func_ludo/state.py",
    "func_ludo/rules.py",
    "func_ludo/bot.py",
    "func_ludo/commentary.py",
    "func_ludo/renderer.py",
    "func_ludo/cli.py",
    "func_ludo/gui_session.py",
    "func_ludo/gui.py",
)
PLACEHOLDERS = ("TODO", "TBD", "FIXME", "NotImplementedError")


def get_imported_root_modules(tree: ast.AST) -> set[str]:
    """Collect absolute import roots while ignoring package-relative imports."""
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules


def parse_source(path: Path) -> tuple[ast.AST | None, list[str]]:
    """Read and parse one source file, returning readable audit errors."""
    relative = path.relative_to(ROOT)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return None, [f"Cannot read {relative}: {exc}"]
    try:
        return ast.parse(source, filename=str(path)), []
    except SyntaxError as exc:
        return None, [f"SyntaxError in {relative}: {exc}"]


def audit_python_file(path: Path, internal_root: str, forbid_classes: bool) -> list[str]:
    """Audit one file for syntax, imports, placeholders, and class constraints."""
    relative = path.relative_to(ROOT)
    tree, errors = parse_source(path)
    if tree is None:
        return errors
    source = path.read_text(encoding="utf-8")

    class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    if forbid_classes and class_names:
        errors.append(
            f"{relative}: zero-class violation; found {len(class_names)} class definition(s)"
        )

    imported = get_imported_root_modules(tree)
    allowed = STDLIB_MODULES | {internal_root, "__future__"}
    non_stdlib = sorted(module for module in imported if module not in allowed)
    if non_stdlib:
        errors.append(f"{relative}: non-stdlib imports detected: {non_stdlib}")

    for marker in PLACEHOLDERS:
        if marker in source:
            errors.append(f"{relative}: unfinished marker '{marker}'")
    return errors


def smoke_test_cli(path: Path) -> list[str]:
    """Verify help output and clean rejection of an invalid turn cap."""
    errors: list[str] = []
    help_result = subprocess.run(
        [sys.executable, str(path), "--help"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if help_result.returncode != 0:
        errors.append(f"{path.relative_to(ROOT)} --help failed: {help_result.stderr.strip()}")
    for flag in ("--mode", "--seed", "--max-turns", "--no-color", "--wizard", "--autoplay"):
        if flag not in help_result.stdout:
            errors.append(f"{path.relative_to(ROOT)} --help missing required flag {flag}")

    invalid_result = subprocess.run(
        [sys.executable, str(path), "--max-turns", "0"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if invalid_result.returncode == 0:
        errors.append(f"{path.relative_to(ROOT)} accepted invalid --max-turns 0")
    return errors


def run_test_script(script_path: Path, stage_dir: str) -> list[str]:
    """Run one standard-library test script from the repository root."""
    if not script_path.exists():
        return [f"Missing test script: {script_path.relative_to(ROOT)}"]
    environment = dict(os.environ)
    environment["LUDO_TARGET_DIR"] = stage_dir
    print(f"\n>>> Running {script_path.relative_to(ROOT)}")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        env=environment,
        timeout=1200,
    )
    if result.returncode != 0:
        return [f"Test script failed: {script_path.relative_to(ROOT)} (exit {result.returncode})"]
    return []


def audit_stage(stage_dir: str) -> list[str]:
    """Recursively audit one stage and execute its complete test suite."""
    stage_path = ROOT / stage_dir
    print(f"=== Auditing {stage_dir}/ recursively ===")
    if not stage_path.is_dir():
        return [f"Missing stage directory: {stage_dir}"]

    errors: list[str] = []
    for relative in REQUIRED_STAGE_FILES:
        if not (stage_path / relative).is_file():
            errors.append(f"Missing required stage file: {stage_dir}/{relative}")

    python_files = sorted(stage_path.rglob("*.py"))
    if not python_files:
        errors.append(f"No Python files found in {stage_dir}")
    oop_class_names: set[str] = set()
    functional_class_count = 0
    for path in python_files:
        relative = path.relative_to(stage_path)
        forbid_classes = (
            relative.as_posix() == "ludo_func.py"
            or relative.parts[0] in {"func_ludo", "shared"}
        )
        errors.extend(audit_python_file(path, stage_dir, forbid_classes))
        tree, _ = parse_source(path)
        if tree is None:
            continue
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        if relative.parts[0] == "oop_ludo":
            oop_class_names.update(class_names)
        if forbid_classes:
            functional_class_count += len(class_names)

    missing_classes = sorted(REQUIRED_OOP_CLASSES - oop_class_names)
    if missing_classes:
        errors.append(f"{stage_dir}/oop_ludo: missing core classes {missing_classes}")
    print(
        f"AST summary: {len(python_files)} Python files, "
        f"{len(oop_class_names)} OOP classes, {functional_class_count} functional/shared classes"
    )

    if not errors:
        errors.extend(smoke_test_cli(stage_path / "ludo_oop.py"))
        errors.extend(smoke_test_cli(stage_path / "ludo_func.py"))
    if not errors:
        errors.extend(run_test_script(ROOT / "testing" / "test_suite.py", stage_dir))
        errors.extend(run_test_script(ROOT / "testing" / "parity_test.py", stage_dir))
    return errors


def audit_final_submission() -> list[str]:
    """Verify final documentation, peer reports, and the post-peer stage."""
    required_files = (
        "README.md",
        "docs/01_game_design_document.md",
        "docs/02_flowchart_pseudocode.md",
        "docs/03_comparison_report.md",
        "docs/04_ai_interaction_log.md",
        "docs/05_viva_prep.md",
        "docs/06_v3_web_build_plan.md",
        "docs/USER_MANUAL.md",
        "configs/showcase.json",
        "configs/classic.json",
        "v1_initial/ludo_oop.py",
        "v1_initial/ludo_func.py",
        "testing/team1_report.md",
        "testing/team2_report.md",
        "v2_final/ludo_oop.py",
        "v2_final/ludo_func.py",
        "v2_final/CHANGELOG.md",
    )
    errors: list[str] = []
    for relative in required_files:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"Missing final deliverable: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 100:
            errors.append(f"Final deliverable appears empty: {relative}")
        if relative.startswith("testing/team"):
            continue
        for marker in PLACEHOLDERS:
            if marker in text:
                errors.append(f"Unfinished marker '{marker}' in {relative}")
    return errors


def main() -> int:
    """Run the selected verification stage and report a zero-warning result."""
    parser = argparse.ArgumentParser(description="CIA1 Ludo Perfection Gate Verifier")
    parser.add_argument("--stage", choices=("v1", "v2", "final"), required=True)
    args = parser.parse_args()

    errors: list[str] = []
    if args.stage == "v1":
        errors.extend(audit_stage("v1_initial"))
    elif args.stage == "v2":
        errors.extend(audit_stage("v2_final"))
    else:
        errors.extend(audit_stage("v1_initial"))
        errors.extend(audit_stage("v2_final"))
        errors.extend(audit_final_submission())

    print("\n" + "=" * 64)
    if errors:
        print(f"GATE FAILED ({len(errors)} issue(s), 0 warnings):")
        for index, error in enumerate(errors, 1):
            print(f"  [{index}] {error}")
        print("=" * 64)
        return 1
    print(f"GATE PASSED: Stage '{args.stage}' achieved 100% perfection!")
    print("Failures: 0 | Warnings: 0")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
