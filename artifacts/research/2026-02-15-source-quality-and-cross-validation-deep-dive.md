# Deep Dive: Source Quality & Cross-Validation for Knowledge Base Curation

## Strategic Summary

Finding authoritative sources and verifying that synthesized content accurately reflects them are two distinct but interconnected problems. Established information literacy frameworks (CRAAP, SIFT, lateral reading) provide domain-agnostic heuristics for source discovery and evaluation, while recent research in LLM factuality (SAFE, CoVe, claim decomposition) offers concrete methods for cross-validating synthesized content against sources. For Dewey specifically, the gap between what the design principles promise (source primacy, provenance) and what the system currently enforces is significant -- most source quality checks exist only as workflow instructions with no validation.

## Key Questions

- How do you systematically find high-quality, authoritative sources across any domain?
- What frameworks exist for evaluating source credibility without domain-specific expertise?
- How can you verify that synthesized content accurately reflects its sources?
- What does a practical cross-validation pipeline look like using only Claude + web search?
- How do you document *why* a source was deemed credible (audit trail)?
- Where does Dewey's current system fall short, and what's the highest-impact improvement?

## Overview

Source quality in knowledge curation operates at three levels: **discovery** (finding the right sources), **evaluation** (assessing whether they're credible), and **grounding** (ensuring synthesized content faithfully represents them). Most knowledge systems focus heavily on the first two and almost entirely neglect the third -- the same gap Dewey currently has.

The research literature converges on a key insight: **lateral verification beats deep reading**. Professional fact-checkers don't spend time deeply analyzing a single source; they quickly check what *other* sources say about it. This "read across, not down" pattern maps directly to how Claude can be instructed to validate sources during curation.

A second insight from LLM factuality research: **claim-level verification outperforms document-level verification**. Rather than asking "is this article accurate?", decomposing content into atomic claims and checking each one individually produces dramatically better results. Google DeepMind's SAFE method achieves 72% agreement with human annotators at this level, winning 76% of disagreement cases -- and it costs 20x less than human review.

## How It Works

### Phase 1: Source Discovery

Source discovery is the process of finding candidate sources before evaluating them. The goal isn't to find *all* sources -- it's to find sources that are **primary** (created by the entity with direct knowledge), **authoritative** (recognized by the domain), and **current** (reflecting the latest understanding).

**Search Strategy Hierarchy** (most to least authoritative):

1. **Official documentation** -- The source of truth from the creator/maintainer (e.g., RFC documents, language specs, official docs sites)
2. **Institutional sources** -- Universities (.edu), government (.gov), standards bodies, professional organizations
3. **Peer-reviewed publications** -- Academic papers, conference proceedings, journal articles
4. **Recognized expert content** -- Named experts with verifiable credentials writing in their field
5. **High-quality practitioner content** -- Well-regarded blogs, conference talks, technical posts by practitioners with demonstrated expertise
6. **Community consensus** -- Stack Overflow accepted answers, widely-cited GitHub discussions, established wikis

**Practical Search Techniques:**

- **Site-scoped searches**: `site:docs.python.org`, `site:*.edu`, `site:*.gov` to target authoritative domains
- **Quoted exact terms**: `"specification" OR "RFC" OR "standard"` to find primary documents
- **Recency filtering**: Restrict to last 1-2 years for fast-moving domains, wider for stable ones
- **Author-focused**: Search for known domain experts by name + topic
- **Reverse citation**: Find who cites a source to assess its standing in the field

### Phase 2: Source Evaluation

Two complementary frameworks provide domain-agnostic evaluation:

**CRAAP Test** (Currency, Relevance, Authority, Accuracy, Purpose):

| Dimension | Key Questions | Signals |
|-----------|--------------|---------|
| Currency | When was it published/updated? | Date visible, version numbers, changelog |
| Relevance | Does it address the specific topic at the right depth? | Topical match, audience alignment |
| Authority | Who created it? What are their credentials? | Author identified, institutional backing, domain expertise |
| Accuracy | Can claims be verified elsewhere? Are sources cited? | References provided, claims checkable, peer reviewed |
| Purpose | Why does this exist? Is it informational, persuasive, commercial? | Bias indicators, funding disclosure, commercial intent |

**SIFT Method** (Stop, Investigate, Find, Trace):

1. **Stop** -- Before engaging deeply, pause. Don't let a professional-looking page bypass your judgment.
2. **Investigate the source** -- Leave the page. Search for what others say *about* this source. Is the author/org recognized? (This is lateral reading.)
3. **Find better coverage** -- Search for the same claim/topic elsewhere. Do other credible sources agree? Do they cite this source?
4. **Trace claims** -- Follow claims back to their origin. A blog citing a study? Find the actual study. A stat without attribution? Find where it first appeared.

**Combined Scoring Rubric:**

For each source, assess on a 1-5 scale across these dimensions and document the reasoning:

```
Source: [URL]
Title: [Title]
Authority:    [1-5] Reasoning: [why this score]
Accuracy:     [1-5] Reasoning: [why this score]
Currency:     [1-5] Reasoning: [why this score]
Purpose:      [1-5] Reasoning: [why this score]
Corroboration:[1-5] Reasoning: [how many other sources agree]
Overall:      [avg] Decision: [include / exclude / conditional]
```

### Phase 3: Cross-Validation of Synthesized Content

This is where most systems fail. Once you have good sources and write content from them, how do you verify the content actually reflects the sources? Four methods, in order of increasing rigor:

#### Method 1: Claim Decomposition + Verification (adapted from SAFE)

Break synthesized content into atomic, verifiable claims. Verify each independently.

```
Input:  "React uses a virtual DOM for efficient updates,
         diffing the previous and current trees to minimize
         real DOM operations."

Decomposed claims:
  1. React uses a virtual DOM
  2. The virtual DOM is used for efficient updates
  3. React diffs previous and current virtual DOM trees
  4. The purpose of diffing is to minimize real DOM operations

For each claim:
  - Is this stated or implied in Source A? [yes/no/partially]
  - Is this stated or implied in Source B? [yes/no/partially]
  - Does any source contradict this? [yes/no]
  - Confidence: [high/medium/low]
```

#### Method 2: Source Triangulation

Verify key claims across 3+ independent sources. Track agreement/disagreement.

```
Claim: "Container orchestration reduces deployment downtime by 60-80%"

Source A (vendor whitepaper): States 70% reduction -> supports (but note: vendor bias)
Source B (academic study):   States 45-65% reduction -> partially contradicts
Source C (practitioner blog): States "significant reduction, varies by setup" -> vague support

Triangulation result: PARTIAL SUPPORT
  - Claim should be softened: "typically reduces deployment downtime,
    with studies showing 45-80% improvement depending on implementation"
  - Note: vendor sources skew high
```

#### Method 3: Consensus Scoring

For each key claim, compute a simple agreement score:

```
Agreement Score = (supporting sources) / (total sources consulted)

> 0.8  = Strong consensus -> state as fact
0.5-0.8 = Moderate consensus -> qualify with "generally" or "typically"
0.3-0.5 = Weak consensus -> present as "some evidence suggests"
< 0.3  = No consensus -> present competing views or omit
```

#### Method 4: Chain-of-Verification (CoVe)

Self-checking loop where the synthesizer interrogates its own output:

1. **Generate** initial content from sources
2. **Extract** key claims from the generated content
3. **Challenge** each claim: "What evidence from the sources supports this specific claim?"
4. **Search** for counter-evidence: "What would contradict this claim?"
5. **Revise** content based on verification results
6. **Document** which claims were modified and why

### Phase 4: Audit Trail Documentation

Every source inclusion decision should be documented with:

```yaml
source_evaluation:
  url: "https://example.com/article"
  title: "Article Title"
  evaluated: "2026-02-15"
  evaluator: "claude"  # or "human"

  authority_assessment:
    author: "Jane Smith, Principal Engineer at ExampleCorp"
    credentials: "15 years in distributed systems, conference speaker"
    institutional_backing: "Major tech company engineering blog"
    score: 4

  accuracy_assessment:
    peer_reviewed: false
    claims_verifiable: true
    corroborating_sources: 2
    contradicting_sources: 0
    score: 4

  currency_assessment:
    published: "2025-11-01"
    domain_velocity: "fast-moving"
    still_current: true
    score: 5

  purpose_assessment:
    type: "informational"
    commercial_interest: "low"
    bias_indicators: "company blog, but technical depth suggests genuine sharing"
    score: 4

  decision: "include"
  reasoning: "Primary practitioner source from credentialed expert. Claims verified against official documentation and one academic paper. No commercial bias detected despite company blog hosting."
```

## History & Context

### Information Literacy Foundations

Source evaluation isn't new. The CRAAP test was developed by Sarah Blakeslee at California State University, Chico and has been the standard in higher education for over a decade. Mike Caulfield's SIFT method emerged later as a faster, more practical alternative focused on lateral reading -- the technique professional fact-checkers actually use. Both methods are domain-agnostic and translate well to automated/semi-automated workflows.

### LLM Factuality Research

The explosion of LLM-generated content has driven significant research into automated fact-checking:

- **Google DeepMind's SAFE** (2024) demonstrated that LLM-based fact-checking via claim decomposition + search can match or exceed human annotators at lower cost
- **Chain-of-Verification (CoVe)** from Meta showed that having an LLM generate verification questions about its own output, then answer them, reduces hallucination rates
- **VeriFact-CoT** extended this by making the LLM ask "is my reasoning based on facts?" and "what are the sources for these facts?" -- improving factual accuracy and citation quality
- **Multi-agent debate frameworks** (Tool-MAD, DelphiAgent) use multiple LLM agents with different "perspectives" to reach consensus on factual claims

### Triangulation in Research

Triangulation -- using multiple independent sources/methods to verify findings -- is a foundational concept in qualitative research methodology. Four types apply to KB curation:

1. **Data triangulation**: Same claim verified across different source types (documentation, papers, practitioner content)
2. **Methodological triangulation**: Multiple verification approaches (search, cite-check, expert review)
3. **Investigator triangulation**: Multiple reviewers (Claude + human) assess the same content
4. **Theory triangulation**: Claims examined through different conceptual lenses

## Patterns & Best Practices

### 1. Source Hierarchy Enforcement
**When:** Every time sources are selected for a topic.
**Why:** Not all sources carry equal weight. A vendor whitepaper and an RFC are not equivalent evidence. Explicitly ranking sources by type prevents "source quality averaging" where a weak source dilutes the credibility of strong ones.

### 2. Lateral Reading Before Deep Reading
**When:** Evaluating any unfamiliar source.
**Why:** Professional fact-checkers spend less than 30 seconds on a page before leaving to check what others say about it. Deep reading a low-quality source wastes time and can lead to anchoring bias. Always verify the source's reputation *laterally* first.

### 3. Claim Decomposition at Draft Time
**When:** After synthesizing content from sources, before publishing.
**Why:** Document-level review misses subtle inaccuracies. Breaking content into atomic claims and checking each against sources catches errors that holistic review misses. The SAFE methodology showed this approach outperforms human reviewers.

### 4. Consensus Thresholds for Confidence Language
**When:** Writing claims about contested or complex topics.
**Why:** The language used to present a claim should reflect the strength of evidence. "X is true" vs "X is generally accepted" vs "some evidence suggests X" should map directly to how many independent sources agree. This prevents overconfident claims from weak evidence.

### 5. Provenance Documentation as a First-Class Output
**When:** Every source inclusion/exclusion decision.
**Why:** The audit trail isn't metadata -- it's a deliverable. When a source is questioned later (during health checks, by a user, or during updates), the reasoning for its inclusion should be immediately accessible. This also prevents "source amnesia" where content drifts from its original basis during updates.

### 6. Counter-Evidence Search as Standard Practice
**When:** After finding supporting sources, before finalizing.
**Why:** Confirmation bias is the biggest risk in research. Actively searching for "why X is wrong" or "alternatives to X" after finding supporting evidence catches blind spots. If no counter-evidence exists, that's a strong signal. If it does, the content should acknowledge it.

### 7. Source Diversity Requirements
**When:** Selecting the source set for any topic.
**Why:** Three sources from the same organization or author provide less validation than three sources from independent entities. Require source diversity: at least 2 different organizations/authors, at least 2 different source types (e.g., documentation + practitioner content).

## Limitations & Edge Cases

### Limitation: Web Search Coverage
**Problem:** Web search doesn't index everything. Paywalled academic papers, internal documentation, and recent content may be invisible.
**Mitigation:** Acknowledge coverage gaps explicitly. When a topic relies heavily on paywalled sources, note this in the source evaluation. Use freely accessible versions (preprints, author's website copies) when available.

### Limitation: Authority in Emerging Fields
**Problem:** In new or rapidly evolving fields, there may be no established authorities. The CRAAP test's "Authority" dimension breaks down when the field is 6 months old.
**Mitigation:** Shift weight to Currency and Corroboration. For emerging fields, practitioner consensus (multiple independent practitioners saying the same thing) substitutes for institutional authority.

### Limitation: Circular Citation
**Problem:** Multiple sources may all trace back to a single original source, creating an illusion of consensus.
**Mitigation:** The SIFT "Trace" step catches this. When sources cite each other or share a common ancestor, count them as one source for triangulation purposes. Always trace claims to their origin.

### Limitation: LLM Verification of LLM Output
**Problem:** Using Claude to verify Claude's own synthesized content introduces a self-referential loop. The same biases and knowledge gaps persist.
**Mitigation:** Ground verification in *external* evidence (web search results), not internal reasoning. The CoVe approach works because it forces new information retrieval, not just re-reasoning over the same context.

### Edge Case: Contradictory Authoritative Sources
**Problem:** Two equally credible sources disagree. Who wins?
**Mitigation:** Present both perspectives. Use consensus scoring -- if 3/4 authoritative sources agree and 1 disagrees, note the majority view and the dissent. Never silently pick one side.

### Edge Case: Source Available But Changed
**Problem:** A source URL works but the content has been updated since the KB entry was written.
**Mitigation:** This is what `trigger_source_drift()` is designed to catch. Record content hashes or key quotes at curation time to detect drift. Capture the "as of" date prominently.

## Current State & Trends

### Active Research Areas (2025-2026)

- **Multi-agent debate for fact verification** -- Multiple LLM agents with assigned perspectives debate claims before reaching consensus (Tool-MAD, DelphiAgent). Early results show improved accuracy over single-agent verification.
- **Claim decomposition optimization** -- Research shows a tradeoff between granularity and noise. Too-fine decomposition creates trivially true claims that miss the bigger picture. Current work focuses on "meaningful atomic claims" that balance verifiability with usefulness.
- **Grounding classifiers** -- Small, specialized models (like MiniCheck) trained specifically for fact-checking can achieve GPT-4-level performance at 400x lower cost. These could eventually run as local validators.
- **Source-level disagreement modeling** -- Rather than just "supported/not supported," newer systems model the *degree* of inter-source agreement, making verification results more nuanced.

### Practical Trend: Verification as Pipeline

The trend is moving from "verify after writing" to embedding verification into the generation pipeline itself. VeriFact-CoT, for example, makes the LLM verify its claims *during* reasoning, not as a separate post-hoc step. For Dewey, this suggests integrating verification into the curate-add workflow rather than only checking in health.

## Key Takeaways

1. **Lateral reading is the single highest-leverage improvement.** Instead of deeply reading each source, verify what *other* sources say about it. This is how professional fact-checkers work, and it maps directly to web search patterns Claude can execute during curation.

2. **Claim-level verification dramatically outperforms document-level review.** Break synthesized content into atomic claims and check each against sources independently. Google DeepMind's SAFE methodology validates this approach at scale.

3. **The audit trail is not optional -- it's the mechanism that makes everything else sustainable.** Without documented reasoning for source inclusion, every health check and update cycle starts from scratch. Provenance documentation is what turns a one-time quality check into a maintainable system.

4. **Consensus scoring provides a principled way to calibrate confidence language.** Map the strength of multi-source agreement directly to the certainty of your prose. This eliminates the common failure mode of stating weakly-supported claims as facts.

5. **Counter-evidence search is the most neglected practice.** Actively searching for "why X is wrong" after finding supporting evidence is uncomfortable but catches the biggest errors. Make it a required step, not an optional one.

## Remaining Unknowns

- [ ] What's the optimal claim decomposition granularity for KB topics? Too fine = noise, too coarse = misses errors.
- [ ] How to handle source evaluation for topics where all quality sources are behind paywalls?
- [ ] What's the right threshold for consensus scoring in fast-moving vs stable domains?
- [ ] Can source diversity requirements be quantified (e.g., minimum 2 independent organizations), or do they need to be contextual?
- [ ] What's the cost/benefit of running verification at creation time vs health-check time vs both?
- [ ] How to detect circular citation chains automatically (multiple sources tracing to the same origin)?

## Dewey Gap Analysis

### What Dewey Currently Enforces

| Check | Tier | What It Catches |
|-------|------|----------------|
| `check_frontmatter()` | 1 | Sources field exists and is non-empty |
| `check_source_urls()` | 1 | URLs start with http/https |
| `check_go_deeper_links()` | 1 | External links exist in Go Deeper section |
| `trigger_source_drift()` | 2 | Content older than 90 days |
| `trigger_source_primacy()` | 2 | Fewer than 1 inline citation per 3 recommendations |
| `trigger_citation_quality()` | 2 | Same URL cited 3+ times (shallow sourcing) |

### What's Missing (Ordered by Impact)

1. **Source accessibility** -- No HTTP check. Dead links pass all validators.
2. **Citation grounding** -- No check that inline citations match frontmatter sources.
3. **Source authority assessment** -- No distinction between an RFC and a random blog post.
4. **Claim-source alignment** -- No verification that synthesized claims reflect what sources actually say.
5. **Comprehensive coverage** -- No requirement that every recommendation cites at least one source.
6. **Placeholder detection** -- No check for unfilled "Key Sources" placeholders in overview files.
7. **Source diversity** -- No check that sources come from independent entities.

### Recommended Integration Points

**During curate-add (creation time):**
- Source evaluation rubric applied to each source before inclusion
- Lateral reading step: verify source reputation via web search
- Counter-evidence search: actively look for contradicting sources
- Claim decomposition + verification on the draft before presenting to user
- Provenance documentation generated for each source

**During health checks (ongoing):**
- Source accessibility validator (HTTP check) -- new Tier 1
- Citation grounding validator (inline URLs match frontmatter) -- new Tier 1
- Placeholder detection -- new Tier 1
- Source diversity check -- new Tier 2 trigger
- Claim-source alignment (re-verify claims against sources) -- new Tier 2 trigger

## Implementation Context

<claude_context>
<application>
- when_to_use: Any time content is being curated into the KB from external sources, and any time existing content is being validated for accuracy
- when_not_to_use: Internal documentation, user-generated notes, or content where "source" is the user's own experience
- prerequisites: Web search capability, ability to fetch and analyze URLs, structured source metadata in frontmatter
</application>
<technical>
- libraries: No external dependencies needed -- all methods work with Claude + web search
- patterns: CRAAP scoring rubric, SIFT lateral reading, SAFE-style claim decomposition, consensus scoring, CoVe self-verification loop
- gotchas:
  - Circular citations create false consensus -- always trace to origin
  - LLM self-verification without new information retrieval just reinforces existing biases
  - Vendor/commercial sources aren't inherently wrong but need explicit bias acknowledgment
  - Source diversity matters more than source count -- 3 independent sources > 5 from the same org
  - Paywalled sources are a coverage gap, not a quality signal
</technical>
<integration>
- works_with: Dewey's existing source primacy principle, frontmatter metadata, tier 1/2 health model, curate-add and curate-ingest workflows
- conflicts_with: Nothing -- these methods extend, not replace, existing checks
- alternatives: External fact-checking APIs (Semantic Scholar, CrossRef), dedicated fact-checking models (MiniCheck), multi-agent debate frameworks -- all ruled out per Claude+web-search-only constraint
</integration>
</claude_context>

**Next Action:** Apply this methodology by updating the curate-add workflow to include source evaluation rubric, lateral reading, claim decomposition, and provenance documentation steps. Or run `/taches-cc-resources:create-plan` to design the implementation.

## Sources

- [CREDIBLE Framework for Critical Source Evaluation](https://www.mdpi.com/3042-8130/2/1/3) - 2026-02-15
- [Evaluating Sources: Methods & Examples (Scribbr)](https://www.scribbr.com/working-with-sources/evaluating-sources/) - 2026-02-15
- [CRAAP Test (Wikipedia)](https://en.wikipedia.org/wiki/CRAAP_test) - 2026-02-15
- [SIFT Method - Merritt College LibGuide](https://merritt.libguides.com/c.php?g=1235656&p=9066623) - 2026-02-15
- [SIFT / CRAAP Evaluation Tests - ECU LibGuide](https://ecu.au.libguides.com/information-essentials/evaluation-tests) - 2026-02-15
- [Triangulation in Research (Scribbr)](https://www.scribbr.com/methodology/triangulation/) - 2026-02-15
- [Triangulation (BetterEvaluation)](https://www.betterevaluation.org/methods-approaches/methods/triangulation) - 2026-02-15
- [Fact-Checking LLM-Generated Content (Toloka)](https://toloka.ai/blog/fact-checking-llm-generated-content/) - 2026-02-15
- [OpenFactCheck: Unified Framework for Factuality Evaluation](https://openfactcheck.com/) - 2026-02-15
- [SAFE: Search-Augmented Factuality Evaluator (Google DeepMind)](https://deepmind.google/research/publications/85420/) - 2026-02-15
- [SAFE: Enhancing Factuality Evaluation (MarkTechPost)](https://www.marktechpost.com/2024/03/29/researchers-from-google-deepmind-and-stanford-introduce-search-augmented-factuality-evaluator-safe-enhancing-factuality-evaluation-in-large-language-models/) - 2026-02-15
- [Hallucination to Truth: Fact-Checking and Factuality in LLMs](https://arxiv.org/html/2508.03860v1) - 2026-02-15
- [Chain-of-Verification Reduces Hallucination (ETH Zurich)](https://www.research-collection.ethz.ch/server/api/core/bitstreams/468e77de-b21f-4ede-b179-8a52b01a1c5a/content) - 2026-02-15
- [VeriFact-CoT: Enhancing Factual Accuracy and Citation Generation](https://arxiv.org/pdf/2509.05741) - 2026-02-15
- [Contradiction to Consensus: Multi-Source Fact Verification](https://openreview.net/forum?id=JjvVyml8gf) - 2026-02-15
- [Tool-MAD: Multi-Agent Debate for Fact Verification](https://www.arxiv.org/pdf/2601.04742) - 2026-02-15
- [DelphiAgent: Multi-Agent Verification Framework](https://www.sciencedirect.com/science/article/abs/pii/S0306457325001827) - 2026-02-15
- [Claim Decomposition: Boost or Burden?](https://openreview.net/pdf?id=wT6R0z9kbx) - 2026-02-15
- [Authoritative Sources in a Hyperlinked Environment (Kleinberg)](https://www.cs.cornell.edu/home/kleinber/auth.pdf) - 2026-02-15
- [Audit Trails for Accountability in LLMs](https://arxiv.org/html/2601.20727v1) - 2026-02-15
- [Data Provenance: Defined and Explained (IBM)](https://www.ibm.com/think/topics/data-provenance) - 2026-02-15
- [VALUE Rubrics - Information Literacy (AAC&U)](https://www.aacu.org/initiatives/value-initiative/value-rubrics/value-rubrics-information-literacy) - 2026-02-15
- [Search Strategies for Primary Sources (Yale)](https://primarysources.yale.edu/find-discover/search-strategies) - 2026-02-15
- [Confidence Improves Self-Consistency in LLMs](https://aclanthology.org/2025.findings-acl.1030/) - 2026-02-15
- [FACTS Benchmark Suite (Google DeepMind)](https://deepmind.google/blog/facts-benchmark-suite-systematically-evaluating-the-factuality-of-large-language-models/) - 2026-02-15
