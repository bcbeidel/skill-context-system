"""Tests for analyze skill helpers."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from dewey.skills.analyze_skill import (
    AnalysisData,
    analyze_directory,
    compare_to_baseline,
    generate_analysis_prompt,
    load_baseline,
    save_baseline,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_context(temp_dir):
    """Create sample context files for testing."""
    # Small files
    for i in range(5):
        file = temp_dir / f"small-{i}.md"
        file.write_text("# Small File\n" + "Line of text\n" * 50)

    # Medium files
    for i in range(3):
        file = temp_dir / f"medium-{i}.md"
        file.write_text("# Medium File\n" + "Line of text\n" * 300)

    # Large files
    for i in range(2):
        file = temp_dir / f"large-{i}.md"
        file.write_text("# Large File\n" + "Line of text\n" * 600)

    return temp_dir


def test_analyze_directory_basic(sample_context):
    """Test basic directory analysis."""
    data = analyze_directory(sample_context)

    assert data.total_files == 10  # 5 small + 3 medium + 2 large
    assert data.total_tokens > 0
    assert data.total_lines > 0
    assert len(data.files) == 10


def test_analyze_directory_large_files(sample_context):
    """Test identification of large files."""
    data = analyze_directory(sample_context, large_file_threshold=500)

    assert len(data.large_files) == 2  # Only the 600-line files
    for file in data.large_files:
        assert file.lines > 500


def test_analyze_directory_distribution(sample_context):
    """Test token distribution buckets."""
    data = analyze_directory(sample_context)

    assert len(data.distribution) == 4  # 4 buckets defined
    total_percentage = sum(bucket.percentage for bucket in data.distribution)
    assert abs(total_percentage - 100.0) < 0.1  # Should sum to ~100%


def test_analyze_directory_empty(temp_dir):
    """Test analysis of empty directory."""
    data = analyze_directory(temp_dir)

    assert data.total_files == 0
    assert data.total_tokens == 0
    assert data.total_lines == 0
    assert len(data.files) == 0
    assert len(data.large_files) == 0


def test_analyze_directory_custom_extensions(sample_context):
    """Test analysis with custom file extensions."""
    # Create some .txt files
    (sample_context / "test.txt").write_text("Test content")

    # Analyze only .txt files
    data = analyze_directory(sample_context, extensions=[".txt"])

    assert data.total_files == 1
    assert data.files[0].file.endswith(".txt")


def test_generate_analysis_prompt(sample_context):
    """Test prompt generation for analysis."""
    data = analyze_directory(sample_context)
    prompt = generate_analysis_prompt(data)

    # Check that prompt contains key information
    assert str(data.directory) in prompt
    assert str(data.total_files) in prompt
    assert "Total Tokens" in prompt
    assert "Distribution" in prompt
    assert "Large Files" in prompt
    assert "/dewey-" in prompt  # Should mention dewey commands


def test_save_and_load_baseline(sample_context, temp_dir):
    """Test saving and loading baseline data."""
    data = analyze_directory(sample_context)
    baseline_path = temp_dir / "baseline.json"

    # Save baseline
    saved_path = save_baseline(data, baseline_path)
    assert saved_path == baseline_path
    assert baseline_path.exists()

    # Load baseline
    loaded = load_baseline(baseline_path)
    assert loaded is not None
    assert loaded["total_files"] == data.total_files
    assert loaded["total_tokens"] == data.total_tokens
    assert loaded["directory"] == str(data.directory)


def test_load_baseline_not_found(temp_dir):
    """Test loading non-existent baseline."""
    baseline_path = temp_dir / "nonexistent.json"
    loaded = load_baseline(baseline_path)
    assert loaded is None


def test_compare_to_baseline_improved(sample_context, temp_dir):
    """Test comparison when context has improved."""
    # Create initial baseline
    data1 = analyze_directory(sample_context)
    baseline_path = temp_dir / "baseline.json"
    save_baseline(data1, baseline_path)
    baseline = load_baseline(baseline_path)

    # Remove a large file (simulate improvement)
    large_files = list(sample_context.glob("large-*.md"))
    if large_files:
        large_files[0].unlink()

    # Analyze again
    data2 = analyze_directory(sample_context)

    # Compare
    comparison = compare_to_baseline(data2, baseline)

    assert comparison["files_change"] == -1
    assert comparison["tokens_change"] < 0  # Tokens decreased
    assert comparison["improved"] is True


def test_compare_to_baseline_worse(sample_context, temp_dir):
    """Test comparison when context has gotten worse."""
    # Create initial baseline
    data1 = analyze_directory(sample_context)
    baseline_path = temp_dir / "baseline.json"
    save_baseline(data1, baseline_path)
    baseline = load_baseline(baseline_path)

    # Add a large file (simulate worsening)
    new_file = sample_context / "huge.md"
    new_file.write_text("# Huge File\n" + "Line of text\n" * 1000)

    # Analyze again
    data2 = analyze_directory(sample_context)

    # Compare
    comparison = compare_to_baseline(data2, baseline)

    assert comparison["files_change"] == 1
    assert comparison["tokens_change"] > 0  # Tokens increased
    assert comparison["improved"] is False


def test_file_stats_accuracy(sample_context):
    """Test that file stats are accurate."""
    # Create file with known content
    test_file = sample_context / "test.md"
    content = "# Test\nLine 1\nLine 2\nLine 3\n"
    test_file.write_text(content)

    data = analyze_directory(sample_context)

    # Find the test file in results
    test_stats = next(f for f in data.files if f.file == "test.md")

    assert test_stats.lines == 4  # 4 lines
    assert test_stats.tokens == len(content) // 4  # Approximate tokens
    assert test_stats.bytes == len(content.encode())


def test_distribution_buckets_correct(sample_context):
    """Test that distribution buckets categorize files correctly."""
    data = analyze_directory(sample_context)

    # Verify each file is in exactly one bucket
    total_in_buckets = sum(bucket.count for bucket in data.distribution)
    assert total_in_buckets == data.total_files

    # Verify bucket ranges don't overlap
    for i, bucket in enumerate(data.distribution[:-1]):
        next_bucket = data.distribution[i + 1]
        if bucket.max_tokens is not None:
            assert bucket.max_tokens == next_bucket.min_tokens


def test_analysis_timestamp(sample_context):
    """Test that analysis includes timestamp."""
    data = analyze_directory(sample_context)

    assert data.timestamp
    assert "T" in data.timestamp  # ISO format includes T
    from datetime import datetime

    # Should parse as valid datetime
    parsed = datetime.fromisoformat(data.timestamp)
    assert parsed is not None


def test_baseline_includes_top_files(sample_context, temp_dir):
    """Test that baseline includes top 10 files."""
    data = analyze_directory(sample_context)
    baseline_path = temp_dir / "baseline.json"
    save_baseline(data, baseline_path)

    loaded = load_baseline(baseline_path)

    assert "top_10_files" in loaded
    assert len(loaded["top_10_files"]) <= 10
    assert len(loaded["top_10_files"]) == min(10, data.total_files)

    # Should be sorted by tokens (descending)
    if len(loaded["top_10_files"]) > 1:
        tokens = [f["tokens"] for f in loaded["top_10_files"]]
        assert tokens == sorted(tokens, reverse=True)
