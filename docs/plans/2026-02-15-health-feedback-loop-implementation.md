# Health Feedback Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the feedback loop in the health system so inventory regressions, shallow citations, and stale reports are caught automatically.

**Architecture:** Add `file_list` to history snapshots, a new inventory regression validator, a new citation quality trigger, and update the audit workflow with calibration anchors, remediation standards, and a verification step.

**Tech Stack:** Python 3.9+ stdlib only. unittest.TestCase. No external dependencies.

**Design doc:** `docs/plans/2026-02-15-health-feedback-loop-design.md`

---

### Task 1: History schema — add file_list to snapshots

**Files:**
- Modify: `dewey/skills/health/scripts/history.py:21-57`
- Test: `tests/skills/health/test_history.py`

**Step 1: Write the failing tests**

Add to `tests/skills/health/test_history.py`:

```python
# In the import section, also import _extract_source_urls helper if needed
# No new imports needed — record_snapshot and read_history already imported

class TestFileListInSnapshots(unittest.TestCase):
    """Tests for file_list field in history snapshots."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_snapshot_includes_file_list(self):
        """file_list is stored in the snapshot entry."""
        files = ["area/overview.md", "area/topic.md"]
        record_snapshot(self.tmpdir, _tier1_summary(), file_list=files)
        log_path = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = json.loads(log_path.read_text().strip())
        self.assertEqual(entry["file_list"], files)

    def test_file_list_defaults_to_empty(self):
        """file_list defaults to empty list when not provided."""
        record_snapshot(self.tmpdir, _tier1_summary())
        log_path = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = json.loads(log_path.read_text().strip())
        self.assertEqual(entry["file_list"], [])

    def test_file_list_preserved_in_read_history(self):
        """read_history returns entries with file_list intact."""
        files = ["sagemaker/overview.md", "sagemaker/mlops.md"]
        record_snapshot(self.tmpdir, _tier1_summary(), file_list=files)
        history = read_history(self.tmpdir)
        self.assertEqual(history[0]["file_list"], files)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_history.py::TestFileListInSnapshots -v`
Expected: FAIL — `record_snapshot()` does not accept `file_list` parameter

**Step 3: Implement the change**

In `dewey/skills/health/scripts/history.py`, modify `record_snapshot`:

```python
def record_snapshot(
    kb_root: Path,
    tier1_summary: dict,
    tier2_summary: Optional[dict] = None,
    file_list: Optional[list[str]] = None,
) -> Path:
    """Append a timestamped health snapshot to the log file.

    Parameters
    ----------
    kb_root:
        Root directory of the knowledge base (the log is written
        inside ``kb_root/.dewey/history/``).
    tier1_summary:
        Summary dict from ``run_health_check``.
    tier2_summary:
        Optional summary dict from ``run_tier2_prescreening``.
    file_list:
        Optional list of relative file paths discovered during this run.

    Returns
    -------
    Path
        Absolute path to the log file.
    """
    log_dir = kb_root / _LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / _LOG_FILE

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tier1": tier1_summary,
        "tier2": tier2_summary,
        "file_list": file_list or [],
    }

    with log_path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    return log_path
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_history.py -v`
Expected: ALL PASS (new tests + existing tests)

**Step 5: Commit**

```bash
git add dewey/skills/health/scripts/history.py tests/skills/health/test_history.py
git commit -m "Add file_list field to history snapshots"
```

---

### Task 2: Inventory regression validator

**Files:**
- Modify: `dewey/skills/health/scripts/validators.py`
- Test: `tests/skills/health/test_validators.py`

**Step 1: Write the failing tests**

Add to `tests/skills/health/test_validators.py`:

```python
# Add to imports at top:
from validators import check_inventory_regression

class TestCheckInventoryRegression(unittest.TestCase):
    """Tests for check_inventory_regression validator."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        # Create the history directory structure
        history_dir = self.tmpdir / ".dewey" / "history"
        history_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_snapshot(self, file_list):
        """Write a single history snapshot with the given file_list."""
        import json
        from datetime import datetime
        log_path = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "tier1": {"total_files": len(file_list), "fail_count": 0, "warn_count": 0, "pass_count": len(file_list)},
            "tier2": None,
            "file_list": file_list,
        }
        with log_path.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")

    def test_no_history_returns_empty(self):
        """No prior snapshots means no regression to detect."""
        current = ["area/overview.md", "area/topic.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(issues, [])

    def test_same_files_no_issues(self):
        """Identical file list produces no warnings."""
        files = ["area/overview.md", "area/topic.md"]
        self._write_snapshot(files)
        issues = check_inventory_regression(self.tmpdir, files)
        self.assertEqual(issues, [])

    def test_missing_file_warns(self):
        """File in last snapshot but not current produces a warning."""
        self._write_snapshot(["area/overview.md", "area/topic.md", "area/removed.md"])
        current = ["area/overview.md", "area/topic.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(len(issues), 1)
        self.assertIn("removed.md", issues[0]["message"])
        self.assertEqual(issues[0]["severity"], "warn")

    def test_added_file_no_issue(self):
        """New file not in last snapshot is fine (not a regression)."""
        self._write_snapshot(["area/overview.md"])
        current = ["area/overview.md", "area/new-topic.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(issues, [])

    def test_multiple_missing_files(self):
        """Multiple removals produce multiple warnings."""
        self._write_snapshot(["area/a.md", "area/b.md", "area/c.md"])
        current = ["area/a.md"]
        issues = check_inventory_regression(self.tmpdir, current)
        self.assertEqual(len(issues), 2)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_validators.py::TestCheckInventoryRegression -v`
Expected: FAIL — `check_inventory_regression` not defined

**Step 3: Implement the validator**

Add to `dewey/skills/health/scripts/validators.py` at the bottom, before any `if __name__` block:

```python
def check_inventory_regression(kb_root: Path, current_files: list[str]) -> list[dict]:
    """Warn when files from the last health snapshot are missing.

    Compares *current_files* (relative paths like ``area/topic.md``)
    against the ``file_list`` recorded in the most recent history
    snapshot.  Returns a warning for each file that was present
    previously but is absent now.
    """
    from history import read_history

    issues: list[dict] = []
    history = read_history(kb_root, limit=1)
    if not history:
        return issues

    last_snapshot = history[-1]
    last_files = set(last_snapshot.get("file_list", []))
    current_set = set(current_files)

    for missing in sorted(last_files - current_set):
        issues.append({
            "file": missing,
            "message": f"File was present in last health check but is now missing: {missing}",
            "severity": "warn",
        })

    return issues
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_validators.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add dewey/skills/health/scripts/validators.py tests/skills/health/test_validators.py
git commit -m "Add check_inventory_regression validator"
```

---

### Task 3: Citation quality trigger

**Files:**
- Modify: `dewey/skills/health/scripts/tier2_triggers.py`
- Test: `tests/skills/health/test_tier2_triggers.py`

**Step 1: Write the failing tests**

Add to `tests/skills/health/test_tier2_triggers.py`:

```python
# Add to imports at top:
from tier2_triggers import trigger_citation_quality

class TestTriggerCitationQuality(unittest.TestCase):
    """Tests for trigger_citation_quality."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_unique_urls_no_trigger(self):
        """All inline citations use different URLs — no trigger."""
        body = (
            "## Key Guidance\n"
            "- Do this [source](https://example.com/one)\n"
            "- Do that [source](https://example.com/two)\n"
            "- Also this [ref](https://example.com/three)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        self.assertEqual(trigger_citation_quality(f), [])

    def test_duplicate_url_triggers(self):
        """Same URL used 3+ times triggers."""
        body = (
            "## Key Guidance\n"
            "- Do this [source](https://example.com/same)\n"
            "- Do that [source](https://example.com/same)\n"
            "- Also [ref](https://example.com/same)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        results = trigger_citation_quality(f)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["trigger"], "citation_quality")

    def test_two_duplicates_no_trigger(self):
        """Same URL used only twice does not trigger (threshold is 3)."""
        body = (
            "## Key Guidance\n"
            "- Do this [source](https://example.com/same)\n"
            "- Do that [source](https://example.com/same)\n"
            "- Also [ref](https://example.com/other)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        self.assertEqual(trigger_citation_quality(f), [])

    def test_only_working_depth(self):
        """Non-working depth files should not trigger."""
        body = (
            "## Key Guidance\n"
            "- Do this [s](https://example.com/same)\n"
            "- Do that [s](https://example.com/same)\n"
            "- Also [s](https://example.com/same)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("overview") + body)
        self.assertEqual(trigger_citation_quality(f), [])

    def test_checks_watch_out_for_section(self):
        """Duplicate URLs in Watch Out For section also trigger."""
        body = (
            "## Watch Out For\n"
            "- Danger [s](https://example.com/same)\n"
            "- Risk [s](https://example.com/same)\n"
            "- Pitfall [s](https://example.com/same)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        results = trigger_citation_quality(f)
        self.assertEqual(len(results), 1)

    def test_duplicates_across_sections(self):
        """URLs counted across both Key Guidance and Watch Out For."""
        body = (
            "## Key Guidance\n"
            "- Do this [s](https://example.com/same)\n"
            "- Do that [s](https://example.com/same)\n"
            "\n"
            "## Watch Out For\n"
            "- Danger [s](https://example.com/same)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        results = trigger_citation_quality(f)
        self.assertEqual(len(results), 1)

    def test_context_includes_duplicate_urls(self):
        """Context should include duplicate_urls map and counts."""
        body = (
            "## Key Guidance\n"
            "- A [s](https://example.com/dup)\n"
            "- B [s](https://example.com/dup)\n"
            "- C [s](https://example.com/dup)\n"
            "- D [s](https://example.com/other)\n"
        )
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        results = trigger_citation_quality(f)
        ctx = results[0]["context"]
        self.assertIn("duplicate_urls", ctx)
        self.assertEqual(ctx["duplicate_urls"]["https://example.com/dup"], 3)
        self.assertEqual(ctx["total_inline_citations"], 4)
        self.assertEqual(ctx["unique_inline_citations"], 2)

    def test_no_sections_no_trigger(self):
        """File without Key Guidance or Watch Out For should not trigger."""
        body = "## In Practice\nSome [link](https://example.com/same) repeated [here](https://example.com/same) and [here](https://example.com/same).\n"
        f = _write(self.tmpdir / "topic.md", _fm("working") + body)
        self.assertEqual(trigger_citation_quality(f), [])
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_tier2_triggers.py::TestTriggerCitationQuality -v`
Expected: FAIL — `trigger_citation_quality` not defined

**Step 3: Implement the trigger**

Add to `dewey/skills/health/scripts/tier2_triggers.py` at the bottom:

```python
def trigger_citation_quality(file_path: Path) -> list[dict]:
    """Trigger when the same inline citation URL appears 3+ times.

    Working-depth only.  Checks "Key Guidance" and "Watch Out For"
    sections for duplicate ``[text](url)`` links.  Repeated URLs
    suggest shallow sourcing — a single generic page cited to cover
    multiple distinct claims.
    """
    results: list[dict] = []
    name = str(file_path)
    fm = parse_frontmatter(file_path)

    if fm.get("depth") != "working":
        return results

    text = file_path.read_text()
    body = _body_without_frontmatter(text)

    url_counts: dict[str, int] = {}

    for section_name in ("Key Guidance", "Watch Out For"):
        section = _extract_section(body, section_name)
        if section is None:
            continue
        links = re.findall(r"\[([^\]]*)\]\((https?://[^)]+)\)", section)
        for _text, url in links:
            url_counts[url] = url_counts.get(url, 0) + 1

    if not url_counts:
        return results

    duplicate_urls = {url: count for url, count in url_counts.items() if count >= 3}

    if duplicate_urls:
        total = sum(url_counts.values())
        unique = len(url_counts)
        results.append({
            "file": name,
            "trigger": "citation_quality",
            "reason": (
                f"{len(duplicate_urls)} URL(s) cited 3+ times; "
                f"possible shallow sourcing"
            ),
            "context": {
                "duplicate_urls": duplicate_urls,
                "total_inline_citations": total,
                "unique_inline_citations": unique,
            },
        })

    return results
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/test_tier2_triggers.py -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add dewey/skills/health/scripts/tier2_triggers.py tests/skills/health/test_tier2_triggers.py
git commit -m "Add trigger_citation_quality for duplicate URL detection"
```

---

### Task 4: Wire inventory + citations into check_kb.py

**Files:**
- Modify: `dewey/skills/health/scripts/check_kb.py`
- Test: `tests/skills/health/test_check_kb.py`

**Step 1: Write the failing tests**

Add to `tests/skills/health/test_check_kb.py`:

```python
class TestInventoryIntegration(unittest.TestCase):
    """Tests for inventory regression detection in the health check runner."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_file_list_recorded_in_snapshot(self):
        """run_health_check records discovered files in history snapshot."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))
        run_health_check(self.tmpdir)

        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertIn("file_list", entry)
        self.assertEqual(len(entry["file_list"]), 3)
        self.assertTrue(all("area/" in f for f in entry["file_list"]))

    def test_missing_file_detected_on_second_run(self):
        """Second health check detects file removed since first run."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        topic = _write(area / "topic.md", _valid_md("working"))
        _write(area / "topic.ref.md", _valid_md("reference"))

        # First run records all 3 files
        run_health_check(self.tmpdir)

        # Remove a file
        topic.unlink()

        # Second run should detect the regression
        result = run_health_check(self.tmpdir)
        regression_issues = [
            i for i in result["issues"] if "missing" in i["message"].lower()
            and "topic.md" in i["message"]
        ]
        self.assertTrue(len(regression_issues) > 0)

    def test_combined_report_records_file_list(self):
        """run_combined_report also records file_list in snapshot."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        run_combined_report(self.tmpdir)

        log = self.tmpdir / ".dewey" / "history" / "health-log.jsonl"
        entry = json.loads(log.read_text().strip())
        self.assertIn("file_list", entry)


class TestCitationQualityIntegration(unittest.TestCase):
    """Tests for citation quality trigger in the prescreening runner."""

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.kb = self.tmpdir / "docs"
        self.kb.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_duplicate_citations_appear_in_queue(self):
        """File with repeated inline citations produces a citation_quality trigger."""
        area = self.kb / "area"
        area.mkdir()
        _write(area / "overview.md", _valid_md("overview"))
        body = (
            "## In Practice\nConcrete guidance.\n\n"
            "## Key Guidance\n"
            "- A [s](https://example.com/dup)\n"
            "- B [s](https://example.com/dup)\n"
            "- C [s](https://example.com/dup)\n"
        )
        _write(area / "topic.md", _valid_md("working", extra_body=body))
        _write(area / "topic.ref.md", _valid_md("reference"))

        result = run_tier2_prescreening(self.tmpdir)
        citation_items = [i for i in result["queue"] if i["trigger"] == "citation_quality"]
        self.assertTrue(len(citation_items) > 0)
```

Also update the existing `TestTier2OutputSchema.test_valid_trigger_names` to include the new trigger. In `tests/skills/health/test_check_kb.py`, find the `test_valid_trigger_names` method and change the `known_triggers` set:

```python
    def test_valid_trigger_names(self):
        """Every trigger name must be one of the 6 known triggers."""
        known_triggers = {
            "source_drift",
            "depth_accuracy",
            "source_primacy",
            "why_quality",
            "concrete_examples",
            "citation_quality",
        }
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/skills/health/test_check_kb.py::TestInventoryIntegration tests/skills/health/test_check_kb.py::TestCitationQualityIntegration -v`
Expected: FAIL — check_kb.py doesn't pass file_list to history, doesn't run citation trigger

**Step 3: Implement the wiring**

Modify `dewey/skills/health/scripts/check_kb.py`:

1. Add imports:
```python
from tier2_triggers import (
    trigger_citation_quality,
    trigger_concrete_examples,
    trigger_depth_accuracy,
    trigger_source_drift,
    trigger_source_primacy,
    trigger_why_quality,
)
from validators import (
    check_coverage,
    check_cross_references,
    check_freshness,
    check_frontmatter,
    check_index_sync,
    check_inventory_regression,
    check_section_ordering,
    check_size_bounds,
    check_source_urls,
)
```

2. Add `trigger_citation_quality` to `_TIER2_TRIGGERS`:
```python
_TIER2_TRIGGERS = [
    trigger_source_drift,
    trigger_depth_accuracy,
    trigger_source_primacy,
    trigger_why_quality,
    trigger_concrete_examples,
    trigger_citation_quality,
]
```

3. In `run_health_check`, compute relative file paths, run inventory check, and pass file_list to `record_snapshot`:
```python
def run_health_check(kb_root: Path, *, _persist_history: bool = True) -> dict:
    knowledge_dir_name = read_knowledge_dir(kb_root)
    all_issues: list[dict] = []
    md_files = _discover_md_files(kb_root, knowledge_dir_name)

    # Compute relative paths for history tracking
    knowledge_dir = kb_root / knowledge_dir_name
    file_list = [
        str(f.relative_to(knowledge_dir)) for f in md_files
    ]

    # Per-file validators
    for md_file in md_files:
        all_issues.extend(check_frontmatter(md_file))
        all_issues.extend(check_section_ordering(md_file))
        all_issues.extend(check_cross_references(md_file, kb_root))
        all_issues.extend(check_size_bounds(md_file))
        all_issues.extend(check_source_urls(md_file))
        all_issues.extend(check_freshness(md_file))

    # Structural validators (run once)
    all_issues.extend(check_coverage(kb_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_index_sync(kb_root, knowledge_dir_name=knowledge_dir_name))
    all_issues.extend(check_inventory_regression(kb_root, file_list))

    # Build summary
    files_with_fails = set()
    files_with_warns = set()
    all_mentioned_files = set()

    for issue in all_issues:
        f = issue.get("file", "")
        all_mentioned_files.add(f)
        if issue["severity"] == "fail":
            files_with_fails.add(f)
        elif issue["severity"] == "warn":
            files_with_warns.add(f)

    fail_count = sum(1 for i in all_issues if i["severity"] == "fail")
    warn_count = sum(1 for i in all_issues if i["severity"] == "warn")

    result = {
        "issues": all_issues,
        "summary": {
            "total_files": len(md_files),
            "fail_count": fail_count,
            "warn_count": warn_count,
            "pass_count": len(md_files) - len(files_with_fails),
        },
    }
    if _persist_history:
        record_snapshot(kb_root, result["summary"], None, file_list=file_list)
    return result
```

4. Similarly update `run_tier2_prescreening` and `run_combined_report` to pass `file_list`:

In `run_tier2_prescreening`, compute file_list and pass it:
```python
def run_tier2_prescreening(kb_root: Path, *, _persist_history: bool = True) -> dict:
    knowledge_dir_name = read_knowledge_dir(kb_root)
    md_files = _discover_md_files(kb_root, knowledge_dir_name)

    knowledge_dir = kb_root / knowledge_dir_name
    file_list = [str(f.relative_to(knowledge_dir)) for f in md_files]

    queue: list[dict] = []
    trigger_counts: dict[str, int] = {}

    for md_file in md_files:
        for trigger_fn in _TIER2_TRIGGERS:
            for item in trigger_fn(md_file):
                queue.append(item)
                t = item["trigger"]
                trigger_counts[t] = trigger_counts.get(t, 0) + 1

    files_with_triggers = len({item["file"] for item in queue})

    result = {
        "queue": queue,
        "summary": {
            "total_files_scanned": len(md_files),
            "files_with_triggers": files_with_triggers,
            "trigger_counts": trigger_counts,
        },
    }
    if _persist_history:
        record_snapshot(kb_root, None, result["summary"], file_list=file_list)
    return result
```

In `run_combined_report`:
```python
def run_combined_report(kb_root: Path) -> dict:
    knowledge_dir_name = read_knowledge_dir(kb_root)
    md_files = _discover_md_files(kb_root, knowledge_dir_name)
    knowledge_dir = kb_root / knowledge_dir_name
    file_list = [str(f.relative_to(knowledge_dir)) for f in md_files]

    result = {
        "tier1": run_health_check(kb_root, _persist_history=False),
        "tier2": run_tier2_prescreening(kb_root, _persist_history=False),
    }
    record_snapshot(
        kb_root, result["tier1"]["summary"], result["tier2"]["summary"],
        file_list=file_list,
    )
    return result
```

**Step 4: Run all tests to verify they pass**

Run: `python3 -m pytest tests/skills/health/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add dewey/skills/health/scripts/check_kb.py tests/skills/health/test_check_kb.py
git commit -m "Wire inventory regression + citation quality into health runner"
```

---

### Task 5: Update health-audit.md workflow

**Files:**
- Modify: `dewey/skills/health/workflows/health-audit.md`

**Step 1: Read the current workflow**

Read: `dewey/skills/health/workflows/health-audit.md`
(Already read above — 130 lines, 5 steps)

**Step 2: Add calibration anchors after Step 1, before Step 2**

Insert after the trigger summary table (line ~28) and before "## Step 2":

```markdown
### Calibration Anchors

Before assessing queue items, review these reference verdicts to ensure consistent thresholds across all evaluations:

**source_drift — Flag:**
The source URL has been updated with new API endpoints, changed pricing tiers, or deprecated features not reflected in the KB entry. The KB makes claims the source no longer supports.

**source_drift — OK:**
Minor wording changes or page redesign, but the substantive claims and recommendations in the KB still align with the source content.

**depth_accuracy — Flag:**
A working-depth file where "In Practice" contains only bold-header + 2-bullet enumeration lists (no scenarios, worked examples, or code). Reads as a reference checklist rather than actionable working guidance.

**depth_accuracy — OK:**
A working-depth file where low prose ratio is caused by code blocks, tables, and markdown link URLs. The non-prose elements ARE the substance.

**why_quality — Flag:**
"Why This Matters" describes *what* the topic is ("Fair lending laws regulate marketing practices") without explaining *why* it matters to this role ("Non-compliant targeting can trigger regulatory action and halt campaigns").

**why_quality — OK:**
"Why This Matters" connects the topic to role outcomes, stakes, or consequences. The reader understands what they risk by ignoring this topic.

**concrete_examples — Flag:**
"In Practice" describes a process in abstract terms ("configure the schema," "set up the pipeline") without a single code block, config snippet, table, or specific value. A prose description of what an example "might look like" also counts as a flag.

**concrete_examples — OK:**
"In Practice" includes worked scenarios with specific names, values, or artifacts (code blocks, tables, inventory entries, SQL snippets). Someone could follow this in a real implementation.

**source_primacy — Flag:**
10 recommendations with only 1 inline citation. OR: the same generic documentation URL cited 3+ times for different claims. The citations don't trace to information that specifically supports each claim.

**source_primacy — OK:**
8 recommendations with 3 inline citations from distinct, specific sources. Each cited URL leads to content directly addressing the claim it backs. Uncited items are standard practice or experience-based cautions.

**citation_quality — Flag:**
A single documentation index page (e.g., the Feature Store overview) cited to back claims about PII handling, offline stores, AND encoding strategies. The URL is technically relevant but too broad to serve as provenance for any specific claim.

**citation_quality — OK:**
Each inline citation links to a page or section that directly addresses the specific claim. Different claims cite different URLs, or the same URL only when it genuinely covers both claims.
```

**Step 3: Add remediation standards section after Step 5**

Append after the current Step 5 (suggest next steps):

```markdown
## Step 6: Remediation standards

When fixing flagged items (either now or in a follow-up session), all new content must meet the same standards that triggered the original flag:

**Source Primacy fixes:**
- Each citation must link to a page that directly addresses the specific claim. A generic documentation index is not adequate backing for a specific technical recommendation.
- Do not reuse the same URL for multiple distinct claims unless the page genuinely covers both.
- If you cannot find a specific source for a claim, state it as experience-based guidance ("in most implementations," "typically") rather than fabricating a citation.

**Concrete Example fixes:**
- Examples must be implementable artifacts: code blocks, config snippets, schema fragments, table entries with realistic values.
- A prose description of what an example "might look like" does not satisfy the concrete examples requirement.

**Overview/orientation fixes:**
- New prose making factual claims (latency values, architectural relationships, platform behaviors) must cite sources or qualify with hedging language.
- Do not introduce uncited factual assertions while fixing other issues.

**Self-check:** Before completing remediation, verify that every new paragraph you wrote would pass the same Tier 2 assessment that flagged the original content.

## Step 7: Verify remediation

After making fixes, re-run the combined check to confirm improvements and detect regressions:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/health/scripts/check_kb.py --kb-root <kb_root> --both
```

Compare the results against the initial run from Step 1:

1. **File count:** Same, increased, or decreased? A decrease may indicate lost content.
2. **Previously flagged items:** Are they resolved or still present?
3. **New issues:** Did remediation introduce new Tier 1 failures or Tier 2 triggers?

Update `.dewey/health/tier2-report.json` with the **post-remediation** assessment. The report on disk must always reflect the current state of the knowledge base, not a prior state.

If new issues were introduced, address them before finalizing. The report is not complete until it reflects the actual current content.
```

**Step 4: Update success criteria**

Replace the `<success_criteria>` section:

```xml
<success_criteria>
- Combined `--both` invocation runs successfully, producing tier1 and tier2 sections
- Tier 1 results are presented and Tier 2 pre-screener produces a structured trigger queue with context data
- Assessment agents consult calibration anchors before evaluating
- Each Tier 2 assessment uses pre-computed context to focus evaluation
- Combined report clearly separates Tier 1 and Tier 2 findings
- Results are persisted to `.dewey/health/tier2-report.json`
- Recommendations are actionable and specific to each finding
- Remediation content meets the same quality standards as existing content
- Post-remediation verification confirms fixes and detects regressions
- Final tier2-report.json reflects the current state, not pre-remediation state
</success_criteria>
```

**Step 5: Verify no Python changes broken**

Run: `python3 -m pytest tests/skills/health/ -v`
Expected: ALL PASS (workflow changes don't affect Python tests)

**Step 6: Commit**

```bash
git add dewey/skills/health/workflows/health-audit.md
git commit -m "Add calibration anchors, remediation standards, and verification step to audit workflow"
```

---

### Task 6: Full test suite verification

**Step 1: Run all tests**

Run: `python3 -m pytest tests/ -v -k "not test_scaffold_sandbox"`
Expected: ALL PASS

**Step 2: Run check_kb.py against sandbox to verify end-to-end**

Run: `python3 dewey/skills/health/scripts/check_kb.py --kb-root sandbox --both`
Expected: JSON output with `tier1` and `tier2` sections. Tier 2 queue should now include `citation_quality` triggers if any sandbox files have duplicate inline citations. History snapshot should include `file_list`.

**Step 3: Verify snapshot has file_list**

Run: `python3 -c "import json; print(json.loads(open('sandbox/.dewey/history/health-log.jsonl').readlines()[-1])['file_list'][:3])"`
Expected: Shows first 3 relative file paths from the latest snapshot.

**Step 4: Final commit if any adjustments needed**

```bash
git add -A
git commit -m "Final adjustments from end-to-end verification"
```
