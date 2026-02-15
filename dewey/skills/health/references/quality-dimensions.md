# Quality Dimensions

The three quality dimensions used to assess knowledge base health. Every health check, audit, and review maps back to one or more of these dimensions.

## 1. Relevance

**What it means:** The content serves the role's actual needs. It is the right content for the right audience at the right time.

**How it's measured:**

| Tier | Method | Checks |
|------|--------|--------|
| Tier 1 | Deterministic | `relevance` field is present and non-empty |
| Tier 2 | LLM-assisted | Relevance statement accurately describes who benefits and when; content matches the role's responsibilities |
| Tier 3 | Human judgment | Is this topic still needed? Should it be pruned? Does scope need adjustment? |

**Signals of poor relevance:**
- Relevance statement is generic ("useful for the role")
- Content covers a topic no longer part of the role
- Low utilization data in `.dewey/utilization/` (if available)
- Content duplicates information available elsewhere

## 2. Accuracy / Freshness

**What it means:** The content is correct, current, and traceable to authoritative sources. Claims can be verified and the content reflects the current state of its domain.

**How it's measured:**

| Tier | Method | Checks |
|------|--------|--------|
| Tier 1 | Deterministic | `last_validated` within 90 days; `sources` present and well-formed; date format valid |
| Tier 2 | LLM-assisted | Source drift detection (KB claims vs. source content); factual accuracy of key claims |
| Tier 3 | Human judgment | Conflict resolution when KB and sources disagree; deciding which source is authoritative |

**Signals of poor accuracy/freshness:**
- `last_validated` is stale (> 90 days)
- Sources are inaccessible or return errors
- KB claims contradict updated source material
- Industry practices have evolved since last validation

## 3. Structural Fitness

**What it means:** The content follows the KB specification. Files have the right format, required metadata, correct depth labels, expected sections, and proper companion files.

**How it's measured:**

| Tier | Method | Checks |
|------|--------|--------|
| Tier 1 | Deterministic | Frontmatter fields present; section ordering correct; size within bounds; cross-references resolve; coverage (overview.md, .ref.md companions) |
| Tier 2 | LLM-assisted | Depth label accuracy (does content match its declared depth?); "Why This Matters" explains why, not what; "In Practice" is concrete, not abstract |
| Tier 3 | Human judgment | Scope decisions about area consolidation; deciding whether thin areas need expansion |

**Signals of poor structural fitness:**
- Missing required frontmatter fields
- Content at wrong depth (e.g., detailed how-to in an overview file)
- Missing companion files (overview.md, .ref.md)
- Sections out of order (abstract before concrete)
- File too short or too long for its depth

## Dimension-to-Check Mapping

| Check | Relevance | Accuracy / Freshness | Structural Fitness |
|-------|-----------|---------------------|-------------------|
| `check_frontmatter` | relevance field | sources, last_validated | depth field |
| `check_section_ordering` | | | In Practice before Key Guidance |
| `check_cross_references` | | | Internal links resolve |
| `check_size_bounds` | | | Line count within range |
| `check_source_urls` | | Source URL format | |
| `check_freshness` | | last_validated age | |
| `check_coverage` | | | overview.md, .ref.md presence |
| Tier 2: Source drift | | KB claims vs. sources | |
| Tier 2: Depth accuracy | | | Content matches depth label |
| Tier 2: Why quality | Explains motivation | | |
| Tier 2: In Practice quality | | | Concrete, actionable |
| Tier 3: Relevance decisions | Still needed? | | |
| Tier 3: Scope decisions | Right scope? | | Right structure? |
| Tier 3: Conflict resolution | | Which source is right? | |
