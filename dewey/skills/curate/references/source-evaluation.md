# Source Evaluation Reference

Methods for discovering, evaluating, and cross-validating sources during knowledge base curation. Grounded in established information literacy frameworks (CRAAP, SIFT) and LLM factuality research (SAFE, CoVe).

## Source Hierarchy

Ranked from most to least authoritative. Prefer higher tiers when available.

| Tier | Type | Examples |
|------|------|----------|
| 1 | Official documentation | RFC documents, language specs, official docs sites, API references |
| 2 | Institutional sources | University publications (.edu), government (.gov), standards bodies, professional orgs |
| 3 | Peer-reviewed publications | Academic papers, conference proceedings, journal articles |
| 4 | Recognized expert content | Named experts with verifiable credentials writing in their field |
| 5 | High-quality practitioner content | Well-regarded tech blogs, conference talks, posts by practitioners with demonstrated expertise |
| 6 | Community consensus | Stack Overflow accepted answers, widely-cited GitHub discussions, established wikis |

**Key rule:** Three sources from Tier 5-6 do not outweigh one source from Tier 1-2. Higher-tier sources anchor the topic; lower-tier sources supplement with practical context.

## SIFT Methodology

The SIFT method (Mike Caulfield) mirrors how professional fact-checkers work. The core insight: **read across, not down** -- check what others say about a source rather than deeply analyzing the source itself.

### The Four Moves

1. **Stop** -- Before engaging deeply, pause. A professional-looking page, a confident tone, or a `.org` domain does not guarantee quality. Resist the urge to accept at face value.

2. **Investigate the source** -- Leave the page. Search for what others say *about* this source, author, or organization. Check:
   - Is the author identified with verifiable credentials?
   - Is the organization recognized in this domain?
   - Do other credible sources cite or reference this source?
   - Are there known controversies or retractions?

3. **Find better coverage** -- Search for the same topic elsewhere. Do other credible sources agree? Can you find the claim stated in a higher-tier source? If a blog post makes a claim, can you find the same claim in official documentation?

4. **Trace claims** -- Follow claims back to their origin. A blog citing a study? Find the actual study. A statistic without attribution? Find where it first appeared. This catches circular citations where multiple sources trace to a single origin.

### Worked Example

> Evaluating a blog post: "Python 3.12 reduces GIL contention by 40%"

1. **Stop** -- Sounds specific and measurable. Worth checking.
2. **Investigate** -- Search for the author. They have a Medium blog with no credentials listed. No institutional backing.
3. **Find better coverage** -- Search `site:docs.python.org GIL 3.12`. Find PEP 703 and the "What's New in 3.12" page. Neither mentions a 40% figure. The actual claim is about per-interpreter GIL, not reduced contention.
4. **Trace** -- The blog cites a tweet that cites a benchmark that measured something different (import lock contention, not GIL contention).

**Result:** Exclude the blog post. Use PEP 703 and the official What's New page instead. The 40% claim is unsupported.

## Scoring Rubric

For each candidate source, score on five dimensions (1-5 scale). Document the reasoning for each score.

### Authority (Who created this?)

| Score | Meaning | Anchor Examples |
|-------|---------|-----------------|
| 5 | Primary authority | RFC author, language core team member, official documentation maintainer |
| 4 | Recognized domain expert | Published author in the field, senior engineer at major company with public track record |
| 3 | Credentialed practitioner | Identified author with relevant job title, some public work history |
| 2 | Anonymous but institutional | Unattributed content on a recognized organization's site |
| 1 | Anonymous or unverifiable | Anonymous blog, no credentials visible, no institutional backing |

### Accuracy (Can claims be verified?)

| Score | Meaning | Anchor Examples |
|-------|---------|-----------------|
| 5 | Peer-reviewed or self-evidently verifiable | Published paper, claims with inline citations, reproducible code examples |
| 4 | Claims checkable against primary sources | Technical post with links to specs/docs, assertions that can be verified |
| 3 | Mix of verifiable and unverifiable claims | Some citations provided, some assertions unsupported |
| 2 | Mostly unverifiable | Opinion presented as fact, few or no references, anecdotal evidence |
| 1 | Contains known errors or contradicts primary sources | Factual mistakes found, contradicts official documentation |

### Currency (Is it current?)

| Score | Meaning | Anchor Examples |
|-------|---------|-----------------|
| 5 | Published/updated within 6 months, or covers a stable topic | Official docs with recent changelog, evergreen content on stable APIs |
| 4 | Published/updated within 1 year | Recent blog post, conference talk from last year |
| 3 | Published/updated within 2 years | Still broadly accurate but may miss recent developments |
| 2 | 2-4 years old in a fast-moving domain | Outdated library versions, deprecated APIs may be referenced |
| 1 | Outdated or explicitly superseded | Pre-dates major version changes, author has posted corrections |

### Purpose/Bias (Why does this exist?)

| Score | Meaning | Anchor Examples |
|-------|---------|-----------------|
| 5 | Purely informational, no commercial interest | Official documentation, academic paper, standards document |
| 4 | Informational with minor commercial context | Company engineering blog sharing genuine technical insights |
| 3 | Mixed informational and promotional | Tutorial that recommends the author's product alongside genuine advice |
| 2 | Primarily promotional with some informational value | Vendor whitepaper, product comparison by a competitor |
| 1 | Primarily promotional or misleading | Advertorial, SEO content farm, content designed to sell rather than inform |

### Corroboration (Do others agree?)

| Score | Meaning | Anchor Examples |
|-------|---------|-----------------|
| 5 | Key claims confirmed by 3+ independent sources | Multiple official sources, academic consensus, widespread practitioner agreement |
| 4 | Key claims confirmed by 2 independent sources | Two unrelated authors/orgs make the same claims |
| 3 | Key claims confirmed by 1 other source | One other credible source agrees, others don't address the topic |
| 2 | No corroboration found, but no contradiction | Unique perspective, not verified elsewhere, not contradicted |
| 1 | Contradicted by other credible sources | Other authoritative sources disagree with key claims |

### Making the Decision

- **Include** (average >= 3.5): Source meets quality bar. Use in content and cite.
- **Include with caveat** (average 2.5-3.4): Usable for supplementary context but not as a primary source. Note limitations.
- **Exclude** (average < 2.5): Does not meet quality bar. Do not use. Document why in provenance.

## Counter-Evidence Search

After finding supporting sources, actively search for contradicting perspectives. This counters confirmation bias -- the biggest risk in research.

### Search Patterns

For a topic X, run these searches:

- `"problems with X"` or `"limitations of X"`
- `"why X is wrong"` or `"X considered harmful"`
- `"alternatives to X"` or `"X vs Y"`
- `"X criticism"` or `"X drawbacks"`
- `site:news.ycombinator.com X` (practitioner skepticism)

### Interpreting Results

- **No credible counter-evidence found** -- Positive signal. Note in provenance as "counter-evidence search performed, none found from credible sources."
- **Counter-evidence from credible sources** -- Include in Watch Out For section or as qualifying language in Key Guidance. Do not suppress.
- **Counter-evidence from non-credible sources** -- Note in provenance but do not incorporate. Document why the source was deemed non-credible.

## Claim Decomposition

Adapted from Google DeepMind's SAFE (Search-Augmented Factuality Evaluator). Break synthesized content into atomic, verifiable claims before cross-validation.

### Method

1. **Extract** factual and recommendation claims from Key Guidance and Watch Out For sections
2. **Decompose** compound claims into atomic statements (one verifiable assertion each)
3. **Classify** each claim as:
   - **Factual** -- can be verified against sources (e.g., "Python 3.12 introduced per-interpreter GIL")
   - **Recommendation** -- a best practice claim (e.g., "prefer dataclasses over named tuples for mutable data")
   - **Judgment** -- subjective assessment (e.g., "this approach is more elegant") -- skip verification
4. **Verify** each factual and recommendation claim against 2+ evaluated sources

### Example

```
Input: "Use connection pooling to reduce database latency.
       Most ORMs handle this automatically, but you should
       configure pool size based on your concurrent connection
       needs, typically 5-10 for small applications."

Decomposed claims:
  1. Connection pooling reduces database latency [factual]
  2. Most ORMs handle connection pooling automatically [factual]
  3. Pool size should be configured based on concurrent connection needs [recommendation]
  4. Typical pool size for small applications is 5-10 [factual]
```

### Granularity Guidance

- **Too fine:** "Python is a language" -- trivially true, not worth verifying
- **Too coarse:** "Use Python for data science because it has good libraries and community support" -- multiple claims bundled together
- **Right level:** "pandas is the most widely used Python library for tabular data manipulation" -- single verifiable assertion

## Consensus Scoring

Map source agreement directly to confidence language in the draft.

| Agreement | Threshold | Language Pattern | Example |
|-----------|-----------|-----------------|---------|
| Strong consensus | >80% of sources agree | State as fact | "Connection pooling reduces latency by reusing existing connections." |
| Moderate consensus | 50-80% agree | Use "generally" or "typically" | "Connection pools are typically sized at 5-10 for small applications." |
| Weak consensus | 30-50% agree | Use "some evidence suggests" | "Some evidence suggests that async pooling outperforms sync pooling under high load." |
| No consensus | <30% agree | Present competing views or omit | "Practitioners disagree on optimal pool sizing strategy: some recommend fixed pools while others advocate dynamic sizing." |

**Important:** When consensus is weak or absent, this is signal -- not failure. It means the topic has genuine uncertainty that the KB entry should reflect honestly.

## Edge Cases

### Circular Citations
Multiple sources trace back to a single original. Detect by following citation chains. When found, count them as one source for corroboration purposes.

**Example:** Three blog posts all cite the same conference talk. That's one source of evidence, not three.

### Emerging Fields Without Authorities
In new domains (< 2 years old), traditional authority signals are weak. Shift weight to:
- Currency (very recent content preferred)
- Corroboration (multiple independent practitioners agreeing)
- Accuracy (verifiable claims, reproducible examples)

### Paywalled Sources
A source behind a paywall is a coverage gap, not a quality signal. When important sources are paywalled:
- Check for freely accessible versions (preprints, author's website, institutional repositories)
- Note the access limitation in provenance
- Do not penalize the Accuracy score for inability to verify paywalled content

### Vendor Bias
Vendor-produced content is not automatically disqualified. Evaluate by checking:
- Does the content acknowledge limitations of their product?
- Are claims verifiable against independent sources?
- Is the technical depth genuine or surface-level?

Score Purpose/Bias honestly and note the vendor relationship in provenance. Use vendor content as supplementary, not primary, unless it's official documentation for the product being documented.

## Provenance Block Format

Every working-knowledge file includes a `<!-- dewey:provenance -->` HTML comment block containing structured JSON. This block is the audit trail for source inclusion decisions.

### Format

```html
<!-- dewey:provenance
{
  "evaluated": "2026-02-15",
  "sources": [
    {
      "url": "https://docs.python.org/3/library/asyncio.html",
      "title": "asyncio — Asynchronous I/O",
      "tier": 1,
      "scores": {
        "authority": 5,
        "accuracy": 5,
        "currency": 5,
        "purpose": 5,
        "corroboration": 5
      },
      "decision": "include",
      "reasoning": "Official Python documentation. Primary authoritative source."
    },
    {
      "url": "https://example.com/blog/asyncio-tips",
      "title": "Asyncio Tips and Tricks",
      "tier": 5,
      "scores": {
        "authority": 3,
        "accuracy": 4,
        "currency": 4,
        "purpose": 4,
        "corroboration": 3
      },
      "decision": "include",
      "reasoning": "Practitioner content with verified claims. Supplements official docs with practical examples."
    }
  ],
  "excluded_sources": [
    {
      "url": "https://example.com/seo-article",
      "reason": "SEO content farm. No author credentials. Claims not verifiable."
    }
  ],
  "counter_evidence": {
    "searched": true,
    "findings": "No credible counter-evidence found for key claims."
  },
  "cross_validation": {
    "claims_total": 12,
    "claims_verified": 10,
    "claims_modified": 1,
    "claims_removed": 1,
    "modifications": [
      {
        "original": "asyncio is always faster than threading",
        "revised": "asyncio typically outperforms threading for I/O-bound workloads",
        "reason": "Source B notes threading can outperform asyncio for CPU-bound tasks"
      }
    ]
  }
}
-->
```

### Fields

| Field | Required | Purpose |
|-------|----------|---------|
| `evaluated` | Yes | ISO date when evaluation was performed |
| `sources` | Yes | Array of included sources with tier, scores, decision, and reasoning |
| `excluded_sources` | Yes | Array of sources considered but excluded, with reason |
| `counter_evidence` | Yes | Whether counter-evidence search was performed and what was found |
| `cross_validation` | Yes | Claim verification results: totals, modifications, removals |

This block is invisible to readers but available for health validators and future audits.
