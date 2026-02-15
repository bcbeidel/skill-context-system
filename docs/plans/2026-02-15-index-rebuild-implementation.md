# Index Rebuild & Structural File Exclusion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `index.md` auto-generated from filesystem contents (Python-driven, no LLM needed) and exclude structural files from frontmatter validation.

**Architecture:** Enhance `render_index_md()` to include per-area topic listings. Add a `build_index_from_disk()` function that discovers topics by scanning the knowledge directory and reading frontmatter. Add a `check_index_sync` validator that detects when `index.md` is stale. Exclude `index.md` from per-file validators (it's structural, not a knowledge topic).

**Tech Stack:** Python 3.9+ stdlib only, unittest, existing `parse_frontmatter` from validators.py

---

### Task 1: Exclude index.md from per-file health validators

`index.md` is a structural file (table of contents), not a knowledge topic. It should not be subject to frontmatter, section ordering, size bounds, source URL, or freshness checks.

**Files:**
- Modify: `dewey/skills/health/scripts/check_kb.py:41-55`
- Test: `tests/skills/health/test_check_kb.py`

**Step 1: Write the failing test**

Add to `tests/skills/health/test_check_kb.py`:

```python
class TestIndexMdExclusion(unittest.TestCase):
    """index.md is structural, not a knowledge topic — skip per-file validators."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / ".dewey").mkdir()
        (self.tmpdir / ".dewey" / "config.json").write_text('{"knowledge_dir": "docs"}')
        (self.tmpdir / ".dewey" / "history").mkdir()
        kb = self.tmpdir / "docs" / "area"
        kb.mkdir(parents=True)
        # A valid overview file
        _write(kb / "overview.md", FM_OVERVIEW, "# Area\n## What This Covers\n## How It's Organized\n## Key Sources\n")
        # index.md with NO frontmatter (should not cause failures)
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n\n## Domain Areas\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_index_md_without_frontmatter_no_failures(self):
        result = run_health_check(self.tmpdir)
        fail_messages = [i["message"] for i in result["issues"] if i["severity"] == "fail"]
        self.assertEqual(fail_messages, [], f"index.md should not trigger failures: {fail_messages}")

    def test_discover_md_files_excludes_index(self):
        from check_kb import _discover_md_files
        files = _discover_md_files(self.tmpdir, "docs")
        filenames = [f.name for f in files]
        self.assertNotIn("index.md", filenames)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/skills/health/test_check_kb.py::TestIndexMdExclusion -v`
Expected: FAIL — `_discover_md_files` currently returns `index.md`, so missing frontmatter causes a fail.

**Step 3: Modify `_discover_md_files` to exclude index.md**

In `dewey/skills/health/scripts/check_kb.py`, update the `_discover_md_files` function:

```python
def _discover_md_files(kb_root: Path, knowledge_dir_name: str = "docs") -> list[Path]:
    """Return all .md files under the knowledge directory, excluding _proposals/ and index.md."""
    knowledge_dir = kb_root / knowledge_dir_name
    if not knowledge_dir.is_dir():
        return []

    md_files: list[Path] = []
    for md_file in sorted(knowledge_dir.rglob("*.md")):
        # Skip files inside directories that start with _
        parts = md_file.relative_to(knowledge_dir).parts
        if any(part.startswith("_") for part in parts):
            continue
        # Skip structural files (not knowledge topics)
        if md_file.name == "index.md":
            continue
        md_files.append(md_file)

    return md_files
```

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/skills/health/test_check_kb.py::TestIndexMdExclusion -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass. Existing tests should be unaffected because they don't create index.md in their test fixtures.

**Step 6: Commit**

```bash
git add dewey/skills/health/scripts/check_kb.py tests/skills/health/test_check_kb.py
git commit -m "Exclude index.md from per-file health validators

index.md is a structural file (table of contents), not a knowledge topic.
It should not require frontmatter or pass topic-level validators."
```

---

### Task 2: Enhance render_index_md to support per-area topic listings

Currently `render_index_md()` only renders area-level overview links. Enhance it to render topics within each area when topic data is provided.

**Files:**
- Modify: `dewey/skills/init/scripts/templates.py:135-162`
- Test: `tests/skills/init/test_templates.py`

**Step 1: Write the failing tests**

Add to `tests/skills/init/test_templates.py` inside the existing `TestRenderIndexMd` class:

```python
def test_includes_topics_when_provided(self, mock_date):
    mock_date.today.return_value = FIXED_DATE
    areas = [
        {
            "name": "Backend Development",
            "dirname": "backend-development",
            "topics": [
                {"name": "API Design", "filename": "api-design.md", "depth": "working"},
                {"name": "Error Handling", "filename": "error-handling.md", "depth": "working"},
            ],
        },
    ]
    result = render_index_md("Dev", areas)
    self.assertIn("API Design", result)
    self.assertIn("api-design.md", result)
    self.assertIn("Error Handling", result)

def test_topics_show_depth(self, mock_date):
    mock_date.today.return_value = FIXED_DATE
    areas = [
        {
            "name": "Testing",
            "dirname": "testing",
            "topics": [
                {"name": "Unit Testing", "filename": "unit-testing.md", "depth": "working"},
            ],
        },
    ]
    result = render_index_md("Dev", areas)
    self.assertIn("working", result)

def test_no_topics_key_shows_overview_only(self, mock_date):
    """Backward compat: areas without 'topics' key still render overview link."""
    mock_date.today.return_value = FIXED_DATE
    areas = [{"name": "Testing", "dirname": "testing"}]
    result = render_index_md("Dev", areas)
    self.assertIn("testing/overview.md", result)
    self.assertIn("Testing", result)

def test_no_frontmatter_in_output(self, mock_date):
    """index.md is structural — no YAML frontmatter."""
    mock_date.today.return_value = FIXED_DATE
    areas = [{"name": "Testing", "dirname": "testing"}]
    result = render_index_md("Dev", areas)
    self.assertFalse(result.startswith("---"))

def test_ref_md_files_excluded_from_topics(self, mock_date):
    """Reference companions should not appear as separate topic rows."""
    mock_date.today.return_value = FIXED_DATE
    areas = [
        {
            "name": "Testing",
            "dirname": "testing",
            "topics": [
                {"name": "Unit Testing", "filename": "unit-testing.md", "depth": "working"},
            ],
        },
    ]
    result = render_index_md("Dev", areas)
    self.assertNotIn(".ref.md", result)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/init/test_templates.py::TestRenderIndexMd::test_includes_topics_when_provided -v`
Expected: FAIL — current `render_index_md` ignores `topics` key.

**Step 3: Update render_index_md in templates.py**

Replace the existing `render_index_md` function (lines 135-162):

```python
def render_index_md(role_name: str, domain_areas: list[dict]) -> str:
    """Render docs/index.md (human-readable TOC).

    No frontmatter — index.md is structural, not a knowledge topic.

    Parameters
    ----------
    role_name:
        Included for context in the preamble.
    domain_areas:
        List of ``{"name": "Area Name", "dirname": "area-name"}``.
        Each area can optionally include ``"topics"`` — a list of
        ``{"name": ..., "filename": ..., "depth": ...}`` dicts.
        When topics are present, they appear in a table under the area.
        When absent, only the overview link is shown.
    """
    sections: list[str] = []

    sections.append("# Knowledge Base")
    sections.append("")
    sections.append(f"> Domain knowledge for **{role_name}**.")

    if not domain_areas:
        sections.append("")
        sections.append("<!-- No domain areas yet. Use init --role to create them. -->")
        return "\n".join(sections) + "\n"

    for area in domain_areas:
        sections.append("")
        sections.append(f"## {area['name']}")
        sections.append("")

        topics = area.get("topics", [])
        if topics:
            sections.append("| Topic | Depth |")
            sections.append("|-------|-------|")
            # Overview row first
            sections.append(
                f"| [Overview]({area['dirname']}/overview.md) | overview |"
            )
            for topic in topics:
                sections.append(
                    f"| [{topic['name']}]({area['dirname']}/{topic['filename']}) | {topic['depth']} |"
                )
        else:
            sections.append(
                f"| [Overview]({area['dirname']}/overview.md) |"
            )

    return "\n".join(sections) + "\n"
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/init/test_templates.py::TestRenderIndexMd -v`
Expected: All pass (including existing tests — backward compat maintained by the `topics` key being optional).

**Step 5: Verify no trailing whitespace or type issues**

Run: `python3 -m pytest tests/skills/init/test_templates.py::TestNoTrailingWhitespace -v`
Expected: PASS

**Step 6: Commit**

```bash
git add dewey/skills/init/scripts/templates.py tests/skills/init/test_templates.py
git commit -m "Enhance render_index_md to include per-area topic listings

When domain_areas entries include a 'topics' key, index.md now renders
a table per area with topic name, link, and depth. Falls back to
overview-only links when no topics are provided (backward compatible)."
```

---

### Task 3: Add filesystem discovery for index data

Add a function that scans the knowledge directory and returns the data structure `render_index_md` needs — area names, dirnames, and their topics with name/filename/depth.

**Files:**
- Modify: `dewey/skills/init/scripts/scaffold.py`
- Test: `tests/skills/init/test_scaffold.py`

**Step 1: Write the failing tests**

Add to `tests/skills/init/test_scaffold.py`:

```python
class TestDiscoverIndexData(unittest.TestCase):
    """Tests for _discover_index_data filesystem scanner."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()
        (self.tmpdir / ".dewey").mkdir()
        (self.tmpdir / ".dewey" / "config.json").write_text('{"knowledge_dir": "docs"}')

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_discovers_area_with_topics(self):
        from scaffold import _discover_index_data
        area = self.kb / "backend"
        self._write(area / "overview.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: overview\n---\n# Backend\n")
        self._write(area / "api-design.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# API Design\n")
        self._write(area / "api-design.ref.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: reference\n---\n# API Design\n")

        result = _discover_index_data(self.tmpdir, "docs")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "backend")
        self.assertEqual(result[0]["dirname"], "backend")
        # Should include working topic but NOT ref.md or overview.md
        topic_filenames = [t["filename"] for t in result[0]["topics"]]
        self.assertIn("api-design.md", topic_filenames)
        self.assertNotIn("api-design.ref.md", topic_filenames)
        self.assertNotIn("overview.md", topic_filenames)

    def test_reads_depth_from_frontmatter(self):
        from scaffold import _discover_index_data
        area = self.kb / "testing"
        self._write(area / "overview.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: overview\n---\n# Testing\n")
        self._write(area / "unit-testing.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# Unit Testing\n")

        result = _discover_index_data(self.tmpdir, "docs")
        topic = result[0]["topics"][0]
        self.assertEqual(topic["depth"], "working")

    def test_extracts_heading_as_name(self):
        from scaffold import _discover_index_data
        area = self.kb / "testing"
        self._write(area / "overview.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: overview\n---\n# Testing\n")
        self._write(area / "my-topic.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# My Great Topic\n")

        result = _discover_index_data(self.tmpdir, "docs")
        topic = result[0]["topics"][0]
        self.assertEqual(topic["name"], "My Great Topic")

    def test_skips_proposals_directory(self):
        from scaffold import _discover_index_data
        area = self.kb / "_proposals"
        area.mkdir()
        self._write(area / "draft.md", "---\ndepth: working\n---\n# Draft\n")

        result = _discover_index_data(self.tmpdir, "docs")
        self.assertEqual(len(result), 0)

    def test_empty_knowledge_dir(self):
        from scaffold import _discover_index_data
        result = _discover_index_data(self.tmpdir, "docs")
        self.assertEqual(result, [])

    def test_areas_sorted_alphabetically(self):
        from scaffold import _discover_index_data
        for name in ["zebra", "alpha", "middle"]:
            area = self.kb / name
            self._write(area / "overview.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: overview\n---\n# " + name.title() + "\n")

        result = _discover_index_data(self.tmpdir, "docs")
        names = [a["dirname"] for a in result]
        self.assertEqual(names, ["alpha", "middle", "zebra"])

    def test_topics_sorted_alphabetically(self):
        from scaffold import _discover_index_data
        area = self.kb / "testing"
        self._write(area / "overview.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: overview\n---\n# Testing\n")
        self._write(area / "z-topic.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# Z Topic\n")
        self._write(area / "a-topic.md", "---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# A Topic\n")

        result = _discover_index_data(self.tmpdir, "docs")
        filenames = [t["filename"] for t in result[0]["topics"]]
        self.assertEqual(filenames, ["a-topic.md", "z-topic.md"])
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/init/test_scaffold.py::TestDiscoverIndexData -v`
Expected: FAIL — `_discover_index_data` doesn't exist yet.

**Step 3: Implement _discover_index_data in scaffold.py**

Add to `dewey/skills/init/scripts/scaffold.py`, after the existing imports:

```python
from validators import parse_frontmatter
```

Add a new `_init_scripts` path setup to import from health scripts (for `parse_frontmatter`). Actually, `validators.py` is in `health/scripts/`, not `init/scripts/`. We need to either:
- Duplicate `parse_frontmatter` (bad)
- Move it to a shared location (too big a refactor)
- Import it from health scripts path

Best approach: Add the health scripts path to sys.path at the top of scaffold.py, similar to how check_kb.py adds init scripts. OR: write a minimal frontmatter parser inline since we only need `depth` and the `# Heading`.

Actually, `parse_frontmatter` is simple and we only need depth + heading. Let's write a focused helper in scaffold.py:

```python
def _read_topic_metadata(file_path: Path) -> dict:
    """Read depth from frontmatter and title from first H1 heading.

    Returns {"name": str, "depth": str} or empty dict if unparseable.
    """
    try:
        text = file_path.read_text()
    except OSError:
        return {}

    # Parse depth from frontmatter
    depth = ""
    lines = text.split("\n")
    in_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        if in_frontmatter:
            match = re.match(r"^depth:\s*(.+)$", line)
            if match:
                depth = match.group(1).strip().strip('"').strip("'")

    # Parse first H1 heading
    name = file_path.stem.replace("-", " ").title()  # fallback
    heading_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if heading_match:
        name = heading_match.group(1).strip()

    if not depth:
        return {}

    return {"name": name, "depth": depth}


def _discover_index_data(kb_root: Path, knowledge_dir_name: str = "docs") -> list[dict]:
    """Scan the knowledge directory and return area/topic data for index.md.

    Returns list of ``{"name": str, "dirname": str, "topics": [...]}``.
    Topics exclude overview.md and .ref.md files.
    """
    knowledge_dir = kb_root / knowledge_dir_name
    if not knowledge_dir.is_dir():
        return []

    areas: list[dict] = []
    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_"):
            continue

        topics: list[dict] = []
        for md_file in sorted(child.glob("*.md")):
            if md_file.name == "overview.md":
                continue
            if md_file.name.endswith(".ref.md"):
                continue
            meta = _read_topic_metadata(md_file)
            if not meta:
                continue
            topics.append({
                "name": meta["name"],
                "filename": md_file.name,
                "depth": meta["depth"],
            })

        # Use directory name as both name and dirname
        # (human-readable name comes from overview.md heading)
        overview = child / "overview.md"
        area_name = child.name
        if overview.exists():
            heading_match = re.search(
                r"^#\s+(.+)$", overview.read_text(), re.MULTILINE
            )
            if heading_match:
                area_name = heading_match.group(1).strip()

        areas.append({
            "name": area_name,
            "dirname": child.name,
            "topics": topics,
        })

    return areas
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/init/test_scaffold.py::TestDiscoverIndexData -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add dewey/skills/init/scripts/scaffold.py tests/skills/init/test_scaffold.py
git commit -m "Add _discover_index_data for filesystem-driven index generation

Scans the knowledge directory for areas and topics, reads depth from
frontmatter and title from H1 headings. Excludes overview.md, .ref.md,
and _proposals/."
```

---

### Task 4: Wire index rebuild into scaffold and add CLI entry point

Update `scaffold_kb()` to use `_discover_index_data` when regenerating `index.md`. Add a `--rebuild-index` CLI flag so curate workflows can trigger a rebuild with one Python command.

**Files:**
- Modify: `dewey/skills/init/scripts/scaffold.py:248-254` and CLI section
- Test: `tests/skills/init/test_scaffold.py`

**Step 1: Write the failing tests**

Add to `tests/skills/init/test_scaffold.py`:

```python
class TestScaffoldIndexIncludesTopics(unittest.TestCase):
    """scaffold_kb regenerates index.md with discovered topics."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_index_md_includes_topics_on_reinit(self):
        """After adding topic files, re-scaffold picks them up in index.md."""
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])
        # Manually create a topic file (simulating curate workflow)
        topic = self.tmpdir / "docs" / "testing" / "unit-testing.md"
        topic.write_text("---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# Unit Testing\n")
        # Re-scaffold
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("Unit Testing", index)
        self.assertIn("unit-testing.md", index)

    def test_index_md_has_no_frontmatter(self):
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertFalse(index.startswith("---"))


class TestRebuildIndex(unittest.TestCase):
    """Tests for the rebuild_index standalone function."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        scaffold_kb(self.tmpdir, "Dev", domain_areas=["Testing"])

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_rebuild_index_updates_from_disk(self):
        from scaffold import rebuild_index
        # Add a topic file
        topic = self.tmpdir / "docs" / "testing" / "api.md"
        topic.write_text("---\nsources:\n  - url: https://example.com\n    title: Ex\nlast_validated: 2026-01-15\nrelevance: core\ndepth: working\n---\n# API Patterns\n")
        rebuild_index(self.tmpdir)
        index = (self.tmpdir / "docs" / "index.md").read_text()
        self.assertIn("API Patterns", index)

    def test_rebuild_index_respects_knowledge_dir_config(self):
        from scaffold import rebuild_index
        rebuild_index(self.tmpdir)
        self.assertTrue((self.tmpdir / "docs" / "index.md").exists())
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/init/test_scaffold.py::TestScaffoldIndexIncludesTopics -v`
Expected: FAIL

**Step 3: Update scaffold_kb and add rebuild_index**

In `dewey/skills/init/scripts/scaffold.py`, update the index.md section (around line 248):

```python
    # ------------------------------------------------------------------
    # 5. index.md inside the knowledge directory (filesystem-driven)
    # ------------------------------------------------------------------
    index_path = knowledge_path / "index.md"
    index_existed = index_path.exists()
    index_data = _discover_index_data(target_dir, knowledge_dir)
    # Fall back to area_slugs if no files on disk yet (fresh scaffold)
    if not index_data:
        index_data = area_slugs
    index_path.write_text(render_index_md(role_name, index_data))
    created.append(f"{knowledge_dir}/index.md" + (" (updated)" if index_existed else ""))
```

Add the `rebuild_index` public function:

```python
def rebuild_index(target_dir: Path) -> str:
    """Regenerate index.md from the current filesystem contents.

    Parameters
    ----------
    target_dir:
        Root directory containing the knowledge base.

    Returns
    -------
    str
        Path to the written index.md relative to target_dir.
    """
    knowledge_dir_name = read_knowledge_dir(target_dir)
    knowledge_path = target_dir / knowledge_dir_name

    # Read role name from AGENTS.md heading
    agents_path = target_dir / "AGENTS.md"
    role_name = "Knowledge Base"
    if agents_path.exists():
        heading_match = re.search(
            r"^# Role:\s*(.+)$", agents_path.read_text(), re.MULTILINE
        )
        if heading_match:
            role_name = heading_match.group(1).strip()

    index_data = _discover_index_data(target_dir, knowledge_dir_name)
    index_path = knowledge_path / "index.md"
    index_path.write_text(render_index_md(role_name, index_data))
    return f"{knowledge_dir_name}/index.md"
```

Update the CLI `__main__` section to add `--rebuild-index`:

```python
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scaffold a knowledge base.")
    parser.add_argument("--target", required=True, help="Target directory")
    parser.add_argument("--role", default="", help="Role name")
    parser.add_argument(
        "--areas",
        default="",
        help="Comma-separated domain area names",
    )
    parser.add_argument(
        "--starter-topics",
        default="",
        help='JSON mapping of area name to starter topics, e.g. \'{"Area": ["Topic1"]}\'',
    )
    parser.add_argument(
        "--knowledge-dir",
        default="docs",
        help="Name of the knowledge directory (default: docs)",
    )
    parser.add_argument(
        "--rebuild-index",
        action="store_true",
        help="Regenerate index.md from filesystem contents and exit.",
    )
    args = parser.parse_args()

    if args.rebuild_index:
        result = rebuild_index(Path(args.target))
        print(f"Rebuilt {result}")
    else:
        areas = (
            [a.strip() for a in args.areas.split(",") if a.strip()]
            if args.areas
            else []
        )
        topics = json.loads(args.starter_topics) if args.starter_topics else None
        result = scaffold_kb(Path(args.target), args.role, areas, topics, knowledge_dir=args.knowledge_dir)
        print(result)
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/init/test_scaffold.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add dewey/skills/init/scripts/scaffold.py tests/skills/init/test_scaffold.py
git commit -m "Wire filesystem-driven index into scaffold, add rebuild_index CLI

scaffold_kb now discovers topics from disk when regenerating index.md.
New rebuild_index() function and --rebuild-index CLI flag for curate
workflows to call after adding topics."
```

---

### Task 5: Add check_index_sync validator

Add a Tier 1 validator that detects when `index.md` is out of sync with the actual files on disk. This catches staleness deterministically.

**Files:**
- Modify: `dewey/skills/health/scripts/validators.py`
- Modify: `dewey/skills/health/scripts/check_kb.py`
- Test: `tests/skills/health/test_check_kb.py`

**Step 1: Write the failing tests**

Add to `tests/skills/health/test_check_kb.py`:

```python
class TestCheckIndexSync(unittest.TestCase):
    """Tier 1 validator: detect when index.md is out of sync with disk."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        (self.tmpdir / ".dewey").mkdir()
        (self.tmpdir / ".dewey" / "config.json").write_text('{"knowledge_dir": "docs"}')
        (self.tmpdir / ".dewey" / "history").mkdir()
        kb = self.tmpdir / "docs" / "area"
        kb.mkdir(parents=True)
        _write(kb / "overview.md", FM_OVERVIEW, "# Area\n## What This Covers\n## How It's Organized\n## Key Sources\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_missing_index_md_warns(self):
        from validators import check_index_sync
        issues = check_index_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertTrue(any("index.md" in i["message"] and i["severity"] == "warn" for i in issues))

    def test_synced_index_no_issues(self):
        from validators import check_index_sync
        # Create index.md that lists the area
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n\n## Area\n\n| [Overview](area/overview.md) |\n")
        issues = check_index_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertEqual(issues, [])

    def test_topic_on_disk_not_in_index_warns(self):
        from validators import check_index_sync
        # Create a topic file not listed in index
        _write(
            self.tmpdir / "docs" / "area" / "new-topic.md",
            FM_WORKING,
            "# New Topic\n## Why This Matters\n## In Practice\n## Key Guidance\n## Watch Out For\n## Go Deeper\n",
        )
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n\n## Area\n\n| [Overview](area/overview.md) |\n")
        issues = check_index_sync(self.tmpdir, knowledge_dir_name="docs")
        self.assertTrue(any("new-topic.md" in i["message"] for i in issues))

    def test_check_index_sync_in_health_check(self):
        """check_index_sync is included in the Tier 1 health check."""
        (self.tmpdir / "docs" / "index.md").write_text("# Knowledge Base\n")
        _write(
            self.tmpdir / "docs" / "area" / "unlisted.md",
            FM_WORKING,
            "# Unlisted\n## Why This Matters\n## In Practice\n## Key Guidance\n## Watch Out For\n## Go Deeper\n",
        )
        result = run_health_check(self.tmpdir)
        index_issues = [i for i in result["issues"] if "index.md" in i["message"]]
        self.assertGreater(len(index_issues), 0)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_check_kb.py::TestCheckIndexSync -v`
Expected: FAIL — `check_index_sync` doesn't exist.

**Step 3: Implement check_index_sync in validators.py**

Add to `dewey/skills/health/scripts/validators.py`:

```python
def check_index_sync(kb_root: Path, *, knowledge_dir_name: str = "docs") -> list[dict]:
    """Check that index.md lists all topic files that exist on disk.

    Warns when:
    - index.md is missing entirely
    - A topic file exists on disk but is not referenced in index.md
    """
    issues: list[dict] = []
    knowledge_dir = kb_root / knowledge_dir_name
    index_path = knowledge_dir / "index.md"

    if not index_path.exists():
        issues.append({
            "file": str(index_path),
            "message": "Missing index.md — run scaffold --rebuild-index to generate",
            "severity": "warn",
        })
        return issues

    index_text = index_path.read_text()

    # Collect all topic .md files on disk (excluding overview, ref, proposals, index)
    for child in sorted(knowledge_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_"):
            continue
        for md_file in sorted(child.glob("*.md")):
            if md_file.name == "overview.md":
                continue
            if md_file.name.endswith(".ref.md"):
                continue
            # Check if this file is referenced in index.md
            relative_ref = f"{child.name}/{md_file.name}"
            if relative_ref not in index_text:
                issues.append({
                    "file": str(md_file),
                    "message": f"Topic not in index.md: {relative_ref} — run scaffold --rebuild-index",
                    "severity": "warn",
                })

    return issues
```

**Step 4: Wire into check_kb.py**

In `dewey/skills/health/scripts/check_kb.py`, add to the imports:

```python
from validators import (
    check_coverage,
    check_cross_references,
    check_freshness,
    check_frontmatter,
    check_index_sync,
    check_section_ordering,
    check_size_bounds,
    check_source_urls,
)
```

And add after the `check_coverage` call in `run_health_check()`:

```python
    # Structural validators (run once)
    all_issues.extend(check_coverage(kb_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_index_sync(kb_root, knowledge_dir_name=knowledge_dir_name))
```

**Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_check_kb.py::TestCheckIndexSync -v`
Expected: All PASS

**Step 6: Run full test suite**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: All pass.

**Step 7: Commit**

```bash
git add dewey/skills/health/scripts/validators.py dewey/skills/health/scripts/check_kb.py tests/skills/health/test_check_kb.py
git commit -m "Add check_index_sync validator to detect stale index.md

Tier 1 health checks now warn when topic files exist on disk but are
not referenced in index.md. Suggests running --rebuild-index to fix."
```

---

### Task 6: Update curate workflows and documentation

Update the curate workflows to call `--rebuild-index` after adding/promoting topics. Update SKILL.md docs.

**Files:**
- Modify: `dewey/skills/curate/workflows/curate-add.md`
- Modify: `dewey/skills/curate/workflows/curate-promote.md`
- Modify: `dewey/skills/health/SKILL.md`

**Step 1: Update curate-add.md**

After the existing manifest update steps (Step 5), add a new step:

```markdown
**Step 6: Rebuild index.md**

Regenerate the table of contents so the new topic appears:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <kb_root> --rebuild-index
```
```

**Step 2: Update curate-promote.md**

After the existing manifest update steps (Step 6), add a new step:

```markdown
**Step 7: Rebuild index.md**

Regenerate the table of contents so the promoted topic appears:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <kb_root> --rebuild-index
```
```

**Step 3: Update health SKILL.md**

Add `check_index_sync` to the validators list and add `--rebuild-index` to the scaffold CLI docs.

**Step 4: Commit**

```bash
git add dewey/skills/curate/workflows/curate-add.md dewey/skills/curate/workflows/curate-promote.md dewey/skills/health/SKILL.md
git commit -m "Update curate workflows to rebuild index.md after topic changes

Both curate-add and curate-promote now call scaffold.py --rebuild-index
as a final step, keeping index.md in sync without LLM intervention."
```

---

### Task 7: End-to-end validation against sandbox

Verify everything works together using the sandbox knowledge base.

**Steps:**

1. Run `--rebuild-index` against sandbox:
   ```bash
   python3 dewey/skills/init/scripts/scaffold.py --target sandbox --rebuild-index
   ```
2. Verify new `index.md` lists all 15 topics across 4 domain areas
3. Verify no frontmatter in the new `index.md`
4. Run health check:
   ```bash
   python3 dewey/skills/health/scripts/check_kb.py --kb-root sandbox
   ```
5. Verify 0 fails, 0 warns related to index.md
6. Run full test suite: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
7. Verify all tests pass
