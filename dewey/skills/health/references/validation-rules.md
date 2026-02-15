# Validation Rules

Complete list of Tier 1 deterministic checks performed by `validators.py`.

## Frontmatter Checks (`check_frontmatter`)

| Field | Required | Expected Value | Severity |
|-------|----------|---------------|----------|
| `sources` | Yes | Non-empty list of URLs | fail |
| `last_validated` | Yes | ISO date (YYYY-MM-DD) | fail |
| `relevance` | Yes | Non-empty string | fail |
| `depth` | Yes | One of: `overview`, `working`, `reference` | fail |

## Section Ordering (`check_section_ordering`)

| Rule | Applies To | Expected | Severity |
|------|-----------|----------|----------|
| "In Practice" before "Key Guidance" | `depth: working` files | Concrete before abstract | warn |

## Cross-Reference Integrity (`check_cross_references`)

| Rule | Check | Severity |
|------|-------|----------|
| Internal links resolve | `[text](path)` links (non-URL, non-anchor, non-mailto) must point to existing files | warn |

## Size Bounds (`check_size_bounds`)

| Depth | Min Lines | Max Lines | Severity |
|-------|-----------|-----------|----------|
| `overview` | 5 | 150 | warn |
| `working` | 10 | 400 | warn |
| `reference` | 3 | 150 | warn |

## Source URL Format (`check_source_urls`)

| Rule | Check | Severity |
|------|-------|----------|
| Well-formed URLs | Each source must start with `http://` or `https://` | fail |
| Placeholder comments | Lines containing `<!--` are skipped | -- |

## Freshness (`check_freshness`)

| Rule | Threshold | Severity |
|------|-----------|----------|
| Content age | `last_validated` must be within 90 days of today | warn |
| Invalid date | `last_validated` must parse as ISO date | warn |

## Structural Coverage (`check_coverage`)

| Rule | Scope | Severity |
|------|-------|----------|
| Area has overview | Every directory under `docs/` (excluding `_` prefixed) must contain `overview.md` | fail |
| Topic has companion reference | Every `.md` file (excluding `overview.md` and `.ref.md`) must have a matching `.ref.md` | warn |

## Severity Definitions

| Severity | Meaning | CI Behavior |
|----------|---------|-------------|
| **fail** | Structural violation that must be fixed | Fails the health check |
| **warn** | Quality concern that should be addressed | Passes but reported |

## Issue Format

Every validator returns issues as:

```json
{
  "file": "<absolute path to file>",
  "message": "<human-readable description>",
  "severity": "fail | warn"
}
```
