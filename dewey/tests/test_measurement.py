"""Tests for token counting and measurement utilities."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add skills/analyze/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "analyze" / "scripts"))

from token_counter import (
    count_file_tokens,
    estimate_tokens,
    format_summary,
    scan_directory,
)


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_empty_string(self) -> None:
        """Test token counting for empty string."""
        assert estimate_tokens("") == 0

    def test_short_string(self) -> None:
        """Test token counting for short string."""
        # "Hello, world!" = 13 chars = 3 tokens
        assert estimate_tokens("Hello, world!") == 3

    def test_exact_multiple_of_four(self) -> None:
        """Test token counting for string with length multiple of 4."""
        # 8 characters = 2 tokens
        assert estimate_tokens("12345678") == 2

    def test_long_text(self) -> None:
        """Test token counting for longer text."""
        text = "This is a longer piece of text. " * 10
        expected = len(text) // 4
        assert estimate_tokens(text) == expected


class TestCountFileTokens:
    """Tests for count_file_tokens function."""

    def test_count_simple_file(self) -> None:
        """Test counting tokens for a simple file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, world!\nThis is line 2.\n")
            temp_path = Path(f.name)

        try:
            result = count_file_tokens(temp_path)
            assert result["tokens"] > 0
            assert result["lines"] == 2
            assert result["bytes"] > 0
        finally:
            temp_path.unlink()

    def test_count_multiline_file(self) -> None:
        """Test counting tokens for multiline file."""
        content = "\n".join([f"Line {i}" for i in range(10)])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = count_file_tokens(temp_path)
            assert result["lines"] == 10
            assert result["tokens"] == len(content) // 4
        finally:
            temp_path.unlink()

    def test_file_not_found(self) -> None:
        """Test error handling for non-existent file."""
        with pytest.raises(FileNotFoundError):
            count_file_tokens(Path("/nonexistent/file.txt"))

    def test_empty_file(self) -> None:
        """Test counting tokens for empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = count_file_tokens(temp_path)
            assert result["tokens"] == 0
            assert result["lines"] == 0
            assert result["bytes"] == 0
        finally:
            temp_path.unlink()


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_empty_directory(self) -> None:
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_directory(Path(tmpdir))
            assert result == []

    def test_scan_directory_with_files(self) -> None:
        """Test scanning directory with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create test files
            (tmp_path / "file1.md").write_text("Content 1" * 10)
            (tmp_path / "file2.txt").write_text("Content 2" * 20)
            (tmp_path / "file3.md").write_text("Content 3" * 5)

            results = scan_directory(tmp_path, extensions=[".md", ".txt"])

            assert len(results) == 3
            # Results should be sorted by tokens (descending)
            assert results[0]["tokens"] >= results[1]["tokens"]
            assert results[1]["tokens"] >= results[2]["tokens"]

    def test_scan_with_extension_filter(self) -> None:
        """Test scanning with extension filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create files with different extensions
            (tmp_path / "file1.md").write_text("Markdown")
            (tmp_path / "file2.txt").write_text("Text")
            (tmp_path / "file3.py").write_text("Python")

            # Only scan .md files
            results = scan_directory(tmp_path, extensions=[".md"])

            assert len(results) == 1
            assert results[0]["file"] == "file1.md"

    def test_scan_excludes_hidden_dirs(self) -> None:
        """Test that hidden directories are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create regular file
            (tmp_path / "file1.md").write_text("Regular file")

            # Create file in hidden directory
            hidden_dir = tmp_path / ".git"
            hidden_dir.mkdir()
            (hidden_dir / "file2.md").write_text("Hidden file")

            results = scan_directory(tmp_path, extensions=[".md"])

            # Should only find the regular file
            assert len(results) == 1
            assert results[0]["file"] == "file1.md"

    def test_scan_nested_directories(self) -> None:
        """Test scanning nested directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create nested structure
            (tmp_path / "level1").mkdir()
            (tmp_path / "level1" / "level2").mkdir()

            (tmp_path / "file1.md").write_text("Root file")
            (tmp_path / "level1" / "file2.md").write_text("Level 1 file")
            (tmp_path / "level1" / "level2" / "file3.md").write_text("Level 2 file")

            results = scan_directory(tmp_path, extensions=[".md"])

            assert len(results) == 3
            # Check that relative paths are correct
            files = [r["file"] for r in results]
            assert "file1.md" in files
            assert "level1/file2.md" in files or "level1\\file2.md" in files

    def test_directory_not_found(self) -> None:
        """Test error handling for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            scan_directory(Path("/nonexistent/directory"))


class TestFormatSummary:
    """Tests for format_summary function."""

    def test_format_empty_results(self) -> None:
        """Test formatting empty results."""
        summary = format_summary([])
        assert "No files found" in summary

    def test_format_with_results(self) -> None:
        """Test formatting results summary."""
        results = [
            {"file": "file1.md", "tokens": 100, "lines": 50, "bytes": 400},
            {"file": "file2.md", "tokens": 50, "lines": 25, "bytes": 200},
        ]

        summary = format_summary(results)

        assert "Total files:  2" in summary
        assert "Total tokens: 150" in summary
        assert "file1.md" in summary
        assert "100 tokens" in summary

    def test_format_top_10(self) -> None:
        """Test that summary shows top 10 files."""
        results = [
            {"file": f"file{i}.md", "tokens": 100 - i, "lines": 50, "bytes": 400}
            for i in range(20)
        ]

        summary = format_summary(results)

        # Should show top 10
        assert "file0.md" in summary
        assert "file9.md" in summary
        # Should not show beyond top 10
        assert "file15.md" not in summary
