#!/usr/bin/env python3
"""Validate Dewey plugin structure before testing with Claude Code."""

import json
import sys
from pathlib import Path


def validate_plugin():
    """Validate plugin structure and files."""
    errors = []
    warnings = []
    success = []

    print("🔍 Validating Dewey Plugin Structure\n")
    print("=" * 60)

    # Check plugin manifest
    manifest_path = Path(".claude-plugin/plugin.json")
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            required_fields = ["name", "description", "version"]
            for field in required_fields:
                if field in manifest:
                    success.append(f"✓ Manifest has '{field}': {manifest[field]}")
                else:
                    errors.append(f"✗ Manifest missing '{field}'")

            if manifest.get("name") == "dewey":
                success.append("✓ Plugin name is 'dewey'")
            else:
                errors.append(f"✗ Plugin name should be 'dewey', got '{manifest.get('name')}'")

        except json.JSONDecodeError as e:
            errors.append(f"✗ Invalid JSON in manifest: {e}")
    else:
        errors.append("✗ Missing .claude-plugin/plugin.json")

    # Check commands directory
    commands_dir = Path("commands")
    if commands_dir.exists():
        command_files = list(commands_dir.glob("*.md"))
        if command_files:
            success.append(f"✓ Found {len(command_files)} command files")
            for cmd in command_files:
                # Check for frontmatter
                content = cmd.read_text()
                if content.startswith("---"):
                    success.append(f"  ✓ {cmd.name} has frontmatter")
                else:
                    warnings.append(f"  ⚠ {cmd.name} missing frontmatter")
        else:
            errors.append("✗ No command files in commands/")
    else:
        errors.append("✗ Missing commands/ directory")

    # Check Python source
    src_dir = Path("src/dewey")
    if src_dir.exists():
        py_files = list(src_dir.rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f)]
        success.append(f"✓ Found {len(py_files)} Python modules")

        # Check key modules
        key_modules = [
            "src/dewey/core/measurement/token_counter.py",
            "src/dewey/core/compaction/file_splitter.py",
            "src/dewey/core/compaction/skill_splitter.py",
            "src/dewey/skills/analyze_skill.py",
        ]
        for module in key_modules:
            if Path(module).exists():
                success.append(f"  ✓ {module}")
            else:
                errors.append(f"  ✗ Missing {module}")
    else:
        errors.append("✗ Missing src/dewey/ directory")

    # Check tests
    tests_dir = Path("tests")
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        if test_files:
            success.append(f"✓ Found {len(test_files)} test files")
        else:
            warnings.append("⚠ No test files found")
    else:
        warnings.append("⚠ Missing tests/ directory")

    # Check configuration
    config_files = ["pyproject.toml", "setup.py", ".gitignore"]
    for config in config_files:
        if Path(config).exists():
            success.append(f"✓ {config} exists")
        else:
            warnings.append(f"⚠ Missing {config}")

    # Print results
    print("\n📊 Validation Results\n")
    print("=" * 60)

    if success:
        print(f"\n✅ Success ({len(success)} checks passed):")
        for msg in success:
            print(f"  {msg}")

    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)} items):")
        for msg in warnings:
            print(f"  {msg}")

    if errors:
        print(f"\n❌ Errors ({len(errors)} critical issues):")
        for msg in errors:
            print(f"  {msg}")
        print("\n" + "=" * 60)
        print("❌ Validation FAILED - fix errors before testing")
        return False
    else:
        print("\n" + "=" * 60)
        print("✅ Validation PASSED - plugin is ready for testing!")
        print("\nNext steps:")
        print("  1. Open a new terminal")
        print("  2. Run: claude --plugin-dir ./dewey")
        print("  3. Try: /dewey:analyze .")
        print("  4. Try: /help dewey")
        return True


if __name__ == "__main__":
    success = validate_plugin()
    sys.exit(0 if success else 1)
