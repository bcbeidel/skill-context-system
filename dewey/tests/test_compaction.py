"""Tests for compaction modules (file splitting, deduplication)."""

import shutil
import tempfile
from pathlib import Path

import pytest

from dewey.core.compaction.file_splitter import (
    create_backup,
    generate_split_report,
    parse_wikilinks,
    scan_and_update_wikilinks,
    split_file,
    update_wikilinks,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample markdown file for testing."""
    file_path = temp_dir / "test-file.md"
    content = "\n".join([f"Line {i}" for i in range(1, 601)])  # 600 lines
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_parse_wikilinks():
    """Test wikilink parsing."""
    content = "See [[file1]] and [[file2]] for details."
    links = parse_wikilinks(content)
    assert links == ["file1", "file2"]


def test_parse_wikilinks_empty():
    """Test parsing content with no wikilinks."""
    content = "No links here."
    links = parse_wikilinks(content)
    assert links == []


def test_update_wikilinks():
    """Test wikilink updating."""
    content = "See [[old-path]] for details."
    updated, count = update_wikilinks(content, "old-path", "new-path")
    assert "[[new-path]]" in updated
    assert "[[old-path]]" not in updated
    assert count == 1


def test_update_wikilinks_multiple():
    """Test updating multiple occurrences."""
    content = "See [[file]] and [[file]] again."
    updated, count = update_wikilinks(content, "file", "new-file")
    assert updated.count("[[new-file]]") == 2
    assert count == 2


def test_create_backup(temp_dir):
    """Test backup creation."""
    file_path = temp_dir / "test.md"
    file_path.write_text("Test content", encoding="utf-8")

    backup_dir = temp_dir / "backups"
    backup_path = create_backup(file_path, backup_dir)

    assert backup_path.exists()
    assert backup_path.read_text(encoding="utf-8") == "Test content"
    assert "test" in backup_path.name
    assert backup_path.suffix == ".md"


def test_create_backup_nonexistent():
    """Test backup creation with nonexistent file."""
    with pytest.raises(FileNotFoundError):
        create_backup(Path("nonexistent.md"))


def test_split_file(sample_file):
    """Test file splitting."""
    result = split_file(sample_file, max_lines=500, main_lines=150)

    # Check result structure
    assert result.original_file == sample_file
    assert result.main_file == sample_file
    assert len(result.reference_files) == 1
    assert result.backup_file is not None
    assert result.backup_file.exists()

    # Check line counts
    assert result.lines_in_main == 150
    assert result.lines_in_references == 450  # 600 - 150
    assert result.total_lines == 600

    # Check files were created
    assert result.main_file.exists()
    assert result.reference_files[0].exists()

    # Check main file has link to reference
    main_content = result.main_file.read_text()
    assert "references" in main_content.lower()


def test_split_file_too_small(temp_dir):
    """Test splitting a file that's too small."""
    small_file = temp_dir / "small.md"
    small_file.write_text("\n".join([f"Line {i}" for i in range(1, 51)]))  # 50 lines

    with pytest.raises(ValueError, match="under the.*line threshold"):
        split_file(small_file, max_lines=500)


def test_split_file_no_backup(sample_file):
    """Test splitting without creating backup."""
    result = split_file(sample_file, max_lines=500, backup=False)
    assert result.backup_file is None


def test_generate_split_report(sample_file):
    """Test report generation."""
    result = split_file(sample_file, max_lines=500, main_lines=150)
    report = generate_split_report(result)

    assert "File Split Report" in report
    assert str(result.original_file) in report
    assert "600" in report  # Total lines
    assert "150" in report  # Main file lines
    assert "450" in report  # Reference lines


def test_scan_and_update_wikilinks(temp_dir):
    """Test scanning and updating wikilinks across directory."""
    # Create files with wikilinks
    file1 = temp_dir / "file1.md"
    file2 = temp_dir / "file2.md"
    file1.write_text("See [[target]] for info.", encoding="utf-8")
    file2.write_text("Link to [[target]] here.", encoding="utf-8")

    # Update wikilinks
    updates = scan_and_update_wikilinks(
        temp_dir, "target", ["new-target"]
    )

    # Check updates were made
    assert updates == 2
    assert "[[new-target]]" in file1.read_text()
    assert "[[new-target]]" in file2.read_text()


def test_scan_and_update_wikilinks_subdirectories(temp_dir):
    """Test updating wikilinks in subdirectories."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    file1 = temp_dir / "file1.md"
    file2 = subdir / "file2.md"
    file1.write_text("See [[old]] for info.", encoding="utf-8")
    file2.write_text("Link to [[old]] here.", encoding="utf-8")

    updates = scan_and_update_wikilinks(
        temp_dir, "old", ["new"]
    )

    assert updates == 2


def test_end_to_end_split_workflow(temp_dir):
    """Test complete split workflow."""
    # Create a large file
    large_file = temp_dir / "large-guide.md"
    content = "\n".join([f"# Section {i}\n\nContent {i}" for i in range(1, 201)])
    large_file.write_text(content, encoding="utf-8")

    # Create another file that links to it
    linking_file = temp_dir / "index.md"
    linking_file.write_text("See [[large-guide]] for details.", encoding="utf-8")

    # Split the file
    result = split_file(large_file, max_lines=500, main_lines=100)

    # Verify split
    assert result.main_file.exists()
    assert len(result.reference_files) == 1
    assert result.backup_file.exists()

    # Update wikilinks
    updates = scan_and_update_wikilinks(
        temp_dir,
        str(large_file.relative_to(temp_dir)).replace(".md", ""),
        [str(large_file.relative_to(temp_dir)).replace(".md", "")],
    )

    # Verify the linking file still works (no changes needed since main file path stayed same)
    assert "[[large-guide]]" in linking_file.read_text()
