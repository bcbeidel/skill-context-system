# Health System Feedback Loop Design

**Date:** 2026-02-15
**Status:** Approved

## Problem

Testing the health system against a real sandbox knowledge base revealed seven gaps where the system fails to catch problems or where the audit workflow produces fixes that don't meet the project's own principles.

### Findings

1. **File inventory regression undetected.** File count dropped from 35 to 34 during remediation. No validator tracks inventory between runs.
2. **No post-remediation Tier 2 re-validation.** After fixing 10 files, only Tier 1 was re-run. The tier2-report.json became stale.
3. **Lost edits undetected.** An index.md edit was silently lost (likely overwritten by index rebuild). Nothing caught it.
4. **Citations added as decoration, not provenance.** Generic documentation landing pages cited to satisfy count thresholds without actually backing specific claims. Same URL reused 3+ times for different claims.
5. **New content introduced the same gaps it fixed.** Overview text and latency tables added during remediation contained uncited factual claims.
6. **Stale tier2-report.json on disk.** Report reflects pre-remediation state, contradicting current content.
7. **No cross-agent calibration for Tier 2 assessments.** Parallel assessment agents apply inconsistent Flag/OK thresholds across domains.

## Design

### 1. Inventory Regression Detection

**History schema change (`history.py`):**

Add `file_list` field to snapshots. Contains relative paths (relative to knowledge dir) of all discovered .md files.

```python
{
  "timestamp": "2026-02-15T14:32:45",
  "tier1": {"total_files": 35, "fail_count": 0, "warn_count": 0, "pass_count": 35},
  "tier2": {"files_with_triggers": 5, "trigger_counts": {...}},
  "file_list": ["adobe-analytics/overview.md", "adobe-analytics/attribution-reporting.md", ...]
}
```

Breaking change -- old snapshots without `file_list` are not supported. Existing `.dewey/history/health-log.jsonl` files should be cleared when upgrading.

**New validator (`validators.py`):**

`check_inventory_regression(kb_root, knowledge_dir, current_files)` -- reads the last history snapshot via `read_history(kb_root, limit=1)`. Compares `file_list` from last snapshot against current discovered files. Returns a warning for each file present in the last snapshot but missing now.

**Integration (`check_kb.py`):**

- `_discover_md_files()` results passed to `record_snapshot()` as `file_list` parameter
- `check_inventory_regression()` called during `run_health_check()` with current file list

### 2. Citation Quality Trigger

**New trigger (`tier2_triggers.py`):**

`trigger_citation_quality(file_path, frontmatter, body)` -- fires when the same URL appears as an inline citation 3+ times across Key Guidance and Watch Out For sections.

Inline citations are markdown links in the pattern `[text](url)` within those sections. The trigger extracts all inline citation URLs, counts occurrences, and flags duplicates.

**Context provided:**

```python
{
  "file": str,
  "trigger": "citation_quality",
  "reason": "3 inline citations reuse the same URL; possible shallow sourcing",
  "context": {
    "duplicate_urls": {"https://docs.aws.amazon.com/...": 3},
    "total_inline_citations": 5,
    "unique_inline_citations": 3
  }
}
```

**Integration (`check_kb.py`):**

Added to `run_tier2_prescreening()` alongside the existing 5 triggers.

### 3. Post-Remediation Verification Loop

**Workflow change (`health-audit.md`):**

New step after remediation: re-run `check_kb.py --both` on the full KB. Compare against the initial run:

- File count: same, increased, or decreased?
- Previously flagged items: resolved or still present?
- New issues: did remediation introduce problems?

Update `.dewey/health/tier2-report.json` with the post-remediation state. The report on disk always reflects the current state of the knowledge base.

### 4. Cross-Agent Calibration Anchors

**Workflow change (`health-audit.md`):**

Add calibration anchor examples for all 6 triggers (5 existing + citation_quality). Each anchor provides a Flag example and an OK example. Assessment agents consult these before evaluating to ensure consistent thresholds.

Triggers covered: source_drift, depth_accuracy, why_quality, concrete_examples, source_primacy, citation_quality.

### 5. Remediation Content Standards

**Workflow change (`health-audit.md`):**

New section defining quality requirements for content written during remediation:

- **Source Primacy fixes:** Citations must link to pages that directly address the specific claim. No URL reuse for distinct claims. If no source exists, state it as experience-based guidance.
- **Concrete Example fixes:** Must be implementable artifacts (code, config, tables with values), not prose descriptions of what examples might look like.
- **Overview/orientation fixes:** Factual claims (latency values, architectural relationships) must cite sources or qualify with hedging language.
- **Self-check:** Before completing remediation, verify new content would pass the same Tier 2 assessment that flagged the original.

## Files Affected

| File | Changes |
|------|---------|
| `dewey/skills/health/scripts/history.py` | Add `file_list` parameter to `record_snapshot()` |
| `dewey/skills/health/scripts/validators.py` | Add `check_inventory_regression()` |
| `dewey/skills/health/scripts/tier2_triggers.py` | Add `trigger_citation_quality()` |
| `dewey/skills/health/scripts/check_kb.py` | Pass file list to history, run inventory check, run citation trigger |
| `dewey/skills/health/workflows/health-audit.md` | Calibration anchors, remediation standards, verification step |
| `tests/skills/health/test_validators.py` | Tests for `check_inventory_regression` |
| `tests/skills/health/test_tier2_triggers.py` | Tests for `trigger_citation_quality` |
| `tests/skills/health/test_check_kb.py` | Tests for inventory integration, citation trigger integration |
| `tests/skills/health/test_history.py` | Tests for `file_list` in snapshots |

## Not In Scope

- `--verify` CLI flag for targeted re-checks (full re-run is sufficient)
- Backwards compatibility for old history snapshots (breaking changes OK)
- Fixing the sandbox content itself (this addresses the infrastructure that should have caught the problems)
