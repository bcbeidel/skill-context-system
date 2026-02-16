# Deep Dive: Agent Context Effectiveness -- Curated vs. RAG vs. Long Context

## Strategic Summary

Curated, structured context decisively outperforms both raw RAG and naive long-context approaches for the tasks Dewey targets -- with empirical support from 30+ papers spanning 2023-2026. The "lost in the middle" effect is real, persistent, and architectural; context length *alone* degrades performance even with perfect retrieval; and structured formatting improves output quality by 10-40% depending on model and task. As context windows scale toward 1M+ tokens, curation becomes *more* important, not less, because noise scales faster than signal. Dewey's design principles are strongly validated by the literature, with minor refinements suggested.

## Key Questions Answered

1. When does curated context outperform RAG, and vice versa?
2. Is the "lost in the middle" effect real, and does progressive disclosure help?
3. When does more context beat curated context?
4. Does structured formatting measurably improve agent performance?
5. Does curation matter more or less as context windows grow?
6. What curation strategies push models to the highest benchmarks?

---

## Research Question 1: Curated Context vs. RAG

### When Curated Context Wins

**Small-to-medium knowledge bases (<200K tokens).** Anthropic's contextual retrieval research explicitly states: if your knowledge base is smaller than 200,000 tokens (~500 pages), include the entire knowledge base in the prompt with no need for RAG. Combined with prompt caching, this reduces latency by >2x and costs by up to 90%.
- Source: [Anthropic -- Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)

**Multi-hop reasoning tasks.** Google DeepMind's LOFT benchmark found Gemini 1.5 Pro with the entire corpus in context outperformed RAG on HotpotQA and MuSiQue because RAG fragments reasoning chains across separately retrieved chunks.
- Source: [LOFT Benchmark (arXiv:2406.13121)](https://arxiv.org/abs/2406.13121)

**Self-contained, narrative information.** Li et al. (2025) found long context correctly answers 56.3% of questions versus RAG's 49.0% on Wikipedia-based QA benchmarks.
- Source: [Long Context vs. RAG for LLMs (arXiv:2501.01880)](https://arxiv.org/abs/2501.01880)

**Fixed-pattern analysis.** Contract reviews, fixed-format report analysis, and other predictable query patterns benefit from direct context over RAG.
- Source: [RAGFlow -- 2025 Year-End Review](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)

### When RAG Wins

**Large corpora (>1M tokens).** Enterprise knowledge bases in the gigabytes or terabytes require RAG; no context window can hold them.

**Cost efficiency at scale.** Pinecone found RAG preserves 95% accuracy while using only 25% of the tokens (75% cost reduction). The Self-Route paper found 60%+ of queries produce identical results via RAG or long context -- for those, RAG saves 39-65% on cost.
- Source: [Pinecone -- Less is More](https://www.pinecone.io/blog/why-use-retrieval-instead-of-larger-context/)
- Source: [Self-Route (arXiv:2407.16833)](https://arxiv.org/abs/2407.16833)

**Rapidly changing knowledge.** RAG indexes new documents automatically; curated context requires manual curation cycles.

**Weaker models.** The LaRA benchmark (ICML 2025) found RAG outperformed long context by 6.48% on Llama-3.2-3B and 38.12% on Mistral-Nemo-12B. The weaker the model, the greater RAG's advantage.
- Source: [LaRA Benchmark (arXiv:2502.09977)](https://arxiv.org/abs/2502.09977)

### Crossover Matrix

| Dimension | Curated Context Wins | RAG Wins |
|-----------|---------------------|----------|
| Corpus size | <200K tokens | >1M tokens |
| Query type | Multi-hop reasoning | Single-hop factual lookup |
| Model tier | Frontier (GPT-4o, Claude, Gemini) | Small/mid (3B-12B params) |
| Knowledge velocity | Stable | Frequently changing |
| Cost sensitivity | Low-volume, quality-critical | High-volume, cost-sensitive |
| Task structure | Fixed patterns, narrative | Fragmented, dialogue-based |

### Provider Guidance

- **Anthropic**: <200K tokens = put it all in the prompt. >200K = use Contextual Retrieval (BM25 + contextual embeddings + reranking) for 67% retrieval failure reduction.
- **OpenAI**: Start with prompt engineering, add RAG when knowledge changes frequently, stack fine-tuning + RAG when evals show issues.
- **Google**: Long context and RAG are complementary. RAG should be more generous in what it retrieves; longer contexts reduce the need for aggressive filtering.

---

## Research Question 2: Long Context Attention Patterns

### The "Lost in the Middle" Effect

**Status: Real, replicated, and architectural.** Liu et al. (TACL 2024) established a U-shaped performance curve: models attend best to information at the beginning (primacy bias) and end (recency bias), with >20% degradation for middle-positioned content. Six major follow-up studies have confirmed and extended the finding:

| Paper | Key Finding |
|-------|-------------|
| Liu et al. (TACL 2024) | U-shaped curve; GPT-3.5 drops >20% in middle; worse than closed-book at 20-30 docs |
| "Never Lost in the Middle" (ACL 2024) | PAM QA mitigates with +13.7% gain in shuffled settings |
| "Lost in the Middle, and In-Between" (Dec 2024) | Effect compounds in multi-hop QA across reasoning hops |
| "Hidden in the Haystack" (May 2025) | Smaller gold contexts amplify positional sensitivity; gold context size is an independent predictor |
| "Intelligence Degradation" (Jan 2025) | Critical thresholds at 40-50% of max context; F1 drops 45.5% beyond threshold |
| "Context Rot" (Chroma, Jul 2025) | 18 models tested; 13.9%-85% degradation even with perfect retrieval and whitespace padding |
| "Context Length Alone Hurts" (EMNLP 2025) | Degradation persists even when irrelevant tokens are masked and models attend only to relevant tokens |

- Sources: [arXiv:2307.03172](https://arxiv.org/abs/2307.03172), [ACL 2024](https://aclanthology.org/2024.acl-long.736/), [arXiv:2412.10079](https://arxiv.org/abs/2412.10079), [arXiv:2505.18148](https://arxiv.org/abs/2505.18148), [arXiv:2601.15300](https://arxiv.org/abs/2601.15300), [Chroma Research](https://research.trychroma.com/context-rot), [arXiv:2510.05381](https://arxiv.org/abs/2510.05381)

### Have Newer Models Fixed It?

**Partially mitigated, not eliminated.** Gemini 1.5 Pro achieves >99.7% on single-needle retrieval at 1M tokens. Claude Sonnet 5 introduces "contextual stability." But on complex tasks (multi-hop QA, synthesis), all models still show significant positional degradation. The Chroma study's finding that even *perfect retrieval with whitespace padding* still causes degradation suggests this is an inherent property of transformer attention.

### Does Progressive Disclosure Help?

**Strongly supported by converging evidence.** No single A/B study isolates progressive disclosure by name, but:

- **Token savings**: Progressive context loading cuts token usage by 98% (150K to 2K tokens) while maintaining codebase context. Source: [Progressive Context Loading](https://williamzujkowski.github.io/posts/from-150k-to-2k-tokens-how-progressive-context-loading-revolutionizes-llm-development-workflows/)
- **Anthropic's agent context engineering**: Explicitly recommends compaction, structured note-taking, and multi-agent architectures -- all progressive disclosure patterns. Up to 54% improvement in agent tasks. Source: [Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- **Claude Skills architecture**: Built on progressive disclosure -- brief descriptions in system prompt, full definitions loaded on invocation.
- **Theoretical backing**: Since context length *itself* is the problem (not just irrelevant content), minimizing loaded tokens at any moment is the most effective mitigation.

### Information Placement Strategies

| Strategy | Effect | Source |
|----------|--------|--------|
| Documents first, query last | Up to 30% improvement | [Anthropic Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips) |
| "This is the most relevant sentence" prefacing | 27% to 98% accuracy (Claude 2.1) | [Anthropic](https://www.anthropic.com/news/claude-2-1-prompting) |
| Sandwich method (instructions at beginning AND end) | Best placement strategy for GPT-4.1 | [OpenAI Cookbook](https://cookbook.openai.com/examples/gpt4-1_prompting_guide) |
| Quote-then-answer | Forces explicit attention to middle content | [Anthropic](https://www.anthropic.com/news/prompting-long-context) |
| U-shaped placement (most relevant at high-attention positions) | Consistently outperforms baselines | [ICLR 2026 submission](https://openreview.net/forum?id=XNar6WUIit) |

---

## Research Question 3: Token Efficiency vs. Comprehensiveness

### When More Context Helps

- **Low-resource translation**: Gemini 1.5 translated languages with <200 speakers by ingesting 500-page grammars + 2,000-entry wordlists. Every token adds signal when the model has no prior knowledge.
- **Whole-artifact understanding**: Book summarization, codebase analysis, financial records -- interconnected information that can't be decomposed without loss.
- **Initial retrieval benefit**: Performance increases from 2K to 4K-32K across most models (Databricks, 2,000+ experiments).

### When Curated Context Wins (The Typical Case)

- **QA with retrieved documents**: 20% accuracy drop at 30 docs vs. 5 docs (Pinecone).
- **Math reasoning**: A single irrelevant sentence can cause models to fail problems they solve correctly without it. Macro accuracy falls below 30% with distractors (GSM-IC, Google Research).
- **Security-focused coding**: 47% drop in security feature implementation with 40K dilution tokens (p < 0.001).
- **Coding agents**: Observation masking (trimming tool output history) achieved +2.6% solve rate at 52% lower cost vs. full context (JetBrains, NeurIPS 2025).

### The Inverted-U Pattern

Quality of generated output **initially improves then subsequently declines** as retrieved passages increase (ICLR 2025). The sweet spot varies by model:

| Model | Performance Starts Declining After |
|-------|-----------------------------------|
| Llama-3.1-405B | 32K tokens |
| GPT-4-0125-preview | 64K tokens |
| GPT-4o, Claude 3.5 Sonnet, GPT-4o-mini | Maintained consistency across all sizes |

- Source: [Databricks](https://www.databricks.com/blog/long-context-rag-performance-llms)

### The Strongest Evidence: Context Length Alone Hurts

Even with **perfect retrieval** of all relevant information, performance degrades 13.9%-85% as input length increases. Even when irrelevant tokens are replaced with **whitespace**, degradation persists. Even when models **only attend to relevant tokens** (attention masking), at least 7.9% degradation remains. Context length imposes a "cognitive tax" independent of content quality.
- Source: [arXiv:2510.05381](https://arxiv.org/abs/2510.05381)

### Key Takeaway

The default should be **curate aggressively**. Only expand context when: (1) the model lacks prior knowledge of the domain, (2) the task requires holistic understanding of a single interconnected artifact, or (3) retrieval quality is so poor that more recall helps despite the noise.

---

## Research Question 4: Structured vs. Unstructured Context

### Headline Finding

Structured formatting measurably improves LLM performance, with effects ranging from **+2.7% to +40%** depending on model, task, and format -- though frontier models are more robust to format variation than smaller models.

### Quantitative Evidence

| Finding | Magnitude | Source |
|---------|-----------|--------|
| GPT-3.5 performance variation by format alone | Up to 40% | [He et al. (arXiv:2411.10541)](https://arxiv.org/abs/2411.10541) |
| YAML vs XML accuracy gap (GPT-5 Nano) | 17.7 pp | [ImprovingAgents.com](https://www.improvingagents.com/blog/best-nested-data-format/) |
| Best vs worst format under stress | 54% more correct answers | [ImprovingAgents.com](https://www.improvingagents.com/blog/best-nested-data-format/) |
| Plain text to JSON (Gemini 1.5F-8B) | 64.65 to 86.27 (+21.62 pp) | [MDPI Electronics](https://www.mdpi.com/2079-9292/14/5/888) |
| Markdown-KV vs CSV (tables) | +16 pp | [ImprovingAgents.com](https://www.improvingagents.com/blog/best-input-data-format-for-llms/) |
| HELM underestimates performance without structure | 4% average; 3/7 leaderboard rankings flipped | [arXiv:2511.20836](https://arxiv.org/abs/2511.20836) |
| ACE structured context agent benchmark gain | +10.6% | [arXiv:2510.04618](https://arxiv.org/abs/2510.04618) |
| File-based context for frontier models | +2.7% (p=0.029) | [McMillan (arXiv:2602.05447)](https://arxiv.org/abs/2602.05447) |
| XML citation rate improvement | 28-40% more likely to cite | [Webex Blog](https://developer.webex.com/blog/boosting-ai-performance-the-power-of-llm-friendly-content-in-markdown) |
| XML token overhead vs Markdown | 80% more tokens | [OpenAI Community](https://community.openai.com/t/markdown-is-15-more-token-efficient-than-json/841742) |
| Markdown savings vs JSON | 34-38% fewer tokens | [ImprovingAgents.com](https://www.improvingagents.com/blog/best-nested-data-format/) |

### Format Recommendations by Use Case

| Format | Best For | Avoid For |
|--------|----------|-----------|
| **Markdown** | General knowledge content, human-readable docs, cost-sensitive scenarios | Deep nesting (>4 levels) |
| **YAML** | Frontmatter, metadata, configuration, when accuracy is priority | Large data volumes (tokens add up) |
| **XML tags** | Section delimiters in prompts, Claude-specific prompting | Data serialization (80% more tokens than Markdown) |
| **JSON** | API data, structured output specifications | Prose content, human readability |

### Critical Nuance

- **Frontier models (Claude, GPT-4, Gemini Pro)**: Format effect on aggregate accuracy is *not significant* (p=0.484) -- these models handle multiple formats well. The 21pp model capability gap dwarfs format effects.
- **Smaller models**: Highly sensitive to formatting -- up to 40% variation.
- **Anthropic's position**: "The exact formatting of prompts is likely becoming less important as models become more capable." But: structured formatting still helps with parseability, citation, and information retrieval within context.
- Source: [McMillan (arXiv:2602.05447)](https://arxiv.org/abs/2602.05447)

### Implication for Dewey

Dewey's Markdown + YAML frontmatter approach is well-aligned with the evidence. Markdown provides the best balance of accuracy, token efficiency, and human readability. YAML frontmatter for metadata is supported by the finding that YAML outperforms XML for structured data. The design does not need to change.

---

## Research Question 5: Context Window Scaling

### Core Finding: Curation Becomes MORE Important as Windows Grow

The intuitive assumption -- that bigger context windows reduce the need for curation -- is contradicted by essentially every piece of empirical research published in 2024-2025.

### Evidence

**Effective context is a fraction of advertised context:**

| Source | Finding |
|--------|---------|
| BABILong (NeurIPS 2024) | Popular LLMs effectively utilize only 10-20% of context for reasoning |
| RULER (COLM 2024) | Only half of models claiming 32K+ can maintain satisfactory performance at 32K |
| NoLiMa (Adobe, 2025) | GPT-4o's effective length: 1K tokens with distractors (vs. 128K advertised) |
| MECW paper (2025) | MECW can be >99% smaller than advertised MCW |
| Gemini 1.5 Pro | Multi-needle recall drops from >99.7% (single) to ~60% (100 needles) at 1M tokens |

- Sources: [BABILong (arXiv:2406.10149)](https://arxiv.org/abs/2406.10149), [RULER (arXiv:2404.06654)](https://arxiv.org/abs/2404.06654), [NoLiMa (arXiv:2502.05167)](https://arxiv.org/abs/2502.05167), [MECW (arXiv:2509.21361)](https://arxiv.org/abs/2509.21361), [Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/the-needle-in-the-haystack-test-and-how-gemini-pro-solves-it)

**Coherent documents paradoxically make retrieval harder:** Chroma found that models get "trapped following narrative arcs instead of finding specific information" -- meaning well-written knowledge bases create a harder retrieval environment, making structural organization even more critical.

**Industry consensus:** LangChain's 2025 State of Agent Engineering: 57% of organizations have agents in production, 32% cite quality as top barrier, most failures traced to poor context management. Organizations with robust context architectures see 50% improvement in response times, 40% higher quality outputs.
- Source: [Gartner -- Context Engineering](https://www.gartner.com/en/articles/context-engineering)

**Cost scales linearly.** Even if a model *could* handle 1M tokens well, the per-request cost makes indiscriminate loading economically untenable for production systems.
- Source: [Factory.ai](https://factory.ai/news/context-window-problem)

### Silver Lining

Epoch AI tracking shows the input length where top models reach 80% accuracy has risen by **over 250x in the past 9 months**. Effective utilization is improving faster than window sizes grow. The trend favors better models, but the fundamental architectural constraint (attention dilution) persists.
- Source: [Epoch AI](https://epoch.ai/data-insights/context-windows)

---

## Research Question 6: Optimal Curation Strategies

### Retrieval: Hybrid Three-Way + Reranking

The highest-performing retrieval pipeline combines three retrieval methods with a cross-encoder reranker:

1. **BM25** (keyword/sparse) -- baseline recall
2. **Dense embeddings** (semantic) -- meaning-based matching
3. **Sparse encoder** (e.g., ELSER) -- learned sparse representations

Then **cross-encoder reranking** on the top 50-100 results down to top 10-20.

| Configuration | Performance | Source |
|---------------|------------|--------|
| BM25 alone | nDCG@10: 43.4 (BEIR) | [Elastic](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid) |
| Hybrid (BM25 + dense) | nDCG@10: 52.6 (+21%) | [Elastic](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid) |
| Three-way (BM25 + dense + sparse) | 88.77% (NQ), 98% (TREC-COVID) | [IBM Blended RAG](https://arxiv.org/html/2404.07220) |
| + Cross-encoder reranking | +20-35% accuracy; -35% hallucinations | [Superlinked](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking) |

**Anthropic's Contextual Retrieval** adds chunk-specific context before embedding, achieving 49% retrieval failure reduction (5.7% to 2.9%), and 67% with reranking (5.7% to 1.9%).

### Indexing: Hierarchical + Metadata-Enriched

Top RAG systems use multi-level indexing:

- **Level 1**: Document-level summaries for broad retrieval
- **Level 2**: Section/paragraph chunks for precision
- **Level 3**: Sentence or proposition-level for fine-grained matching

Proposition-level retrieval outperforms sentence-level by 35% and passage-level by 22.5% on precision.
- Source: [ARAGOG (arXiv:2404.01037)](https://arxiv.org/pdf/2404.01037)

**Parent-child chunk architecture**: Index small leaf chunks for precise matching; at retrieval time, replace clustered leaf chunks with their parent for richer context.

### Chunk Size: Task-Dependent, No Universal Optimum

| Task Type | Optimal Chunk Size | Evidence |
|-----------|-------------------|----------|
| Fact-based, concise answers | 64-128 tokens | 37.8% recall@1 at 64 tokens (NewsQA) |
| General-purpose RAG | 256-512 tokens | Practical sweet spot across benchmarks |
| Narrative comprehension | 512-1024 tokens | 10.7% recall@1 at 1024 tokens (NarrativeQA) |
| Page-level (mixed tasks) | ~Page | 0.648 accuracy, lowest variance (NVIDIA) |

- Source: [Rethinking Chunk Size (arXiv:2505.21700)](https://arxiv.org/html/2505.21700v2)

**Chroma's chunking benchmark**: RecursiveCharacterTextSplitter with 400-512 tokens delivered 85-90% recall without the overhead of semantic chunking. Semantic chunking improved recall by up to 9% but at significant computational cost.
- Source: [Chroma Research -- Evaluating Chunking](https://research.trychroma.com/evaluating-chunking)

### Context Engineering: The Four Pillars

From Anthropic and LangChain's converging frameworks:

| Pillar | Strategy | Example |
|--------|----------|---------|
| **Write** | Persist information outside the context window | CLAUDE.md files, scratchpads, episodic memory |
| **Select** | Retrieve the right information at the right time | Just-in-time loading via glob/grep; embedding-based retrieval |
| **Compress** | Retain only tokens required for the current task | Auto-compaction at 95-98% window; observation masking |
| **Isolate** | Partition context across specialized systems | Sub-agents with focused context windows |

**Key finding**: Anthropic's multi-agent researcher showed multiple agents with isolated contexts outperformed a single agent by **90.2%**.
- Source: [LangChain Blog](https://blog.langchain.com/context-engineering-for-agents/), [Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### Prompt Compression

LLMLingua achieves up to **20x compression** with only 1.5 point performance drop across GSM8K, BBH, ShareGPT, and Arxiv-March23. LLMLingua-2 is 3-6x faster while maintaining 95-98% accuracy retention.
- Source: [Microsoft Research -- LLMLingua](https://www.microsoft.com/en-us/research/blog/llmlingua-innovating-llm-efficiency-with-prompt-compression/)

### How Top Coding Agents Handle Context

| Agent | Strategy |
|-------|----------|
| **Claude Code** | Just-in-time retrieval via glob/grep; CLAUDE.md pre-loaded; auto-compaction at 95-98%; multi-agent parallelism |
| **Cursor** | AST-based chunking (tree-sitter, ~500 token blocks); custom embedding model; hybrid vector + grep search; 128K-200K window |
| **GitHub Copilot** | Neighboring open tabs as context signals; precompiled repo index; file-level understanding |
| **Aider** | Repo map via tree-sitter AST; graph ranking to select relevant identifiers; default 1K token budget for repo map |

- Sources: [How Claude Code Works](https://code.claude.com/docs/en/how-claude-code-works), [How Cursor Indexes Your Codebase](https://towardsdatascience.com/how-cursor-actually-indexes-your-codebase/), [Aider Repo Map](https://aider.chat/docs/repomap.html)

---

## Design Alignment Matrix

| Dewey Principle | Finding | Verdict | Recommendation |
|-----------------|---------|---------|----------------|
| **#1 Source Primacy** | LLMs 28-40% more likely to cite content with structural elements | **Confirmed** | No change needed; consider adding citation anchors |
| **#2 Dual Audience** | Frontier models handle human-readable formats well (p=0.484 for format effect); coherent docs paradoxically harder for retrieval | **Confirmed with nuance** | Human readability is correct default; add structural markers (headers, sections) that also aid model navigation |
| **#3 Three-Dimensional Quality** | Relevance, accuracy, and structural fitness all independently affect model performance | **Confirmed** | No change needed |
| **#5 Provenance & Traceability** | YAML frontmatter adds marginal token cost; metadata-enriched indexing improves retrieval 22-35% | **Confirmed** | No change needed |
| **#6 Domain-Shaped Organization** | Hierarchical indexing outperforms flat; coherent structure aids both humans and (structured) retrieval | **Confirmed** | No change needed |
| **#7 Right-Sized Scope** | Focused 300 tokens beats unfocused 113K; 47% degradation from 40K dilution tokens; inverted-U performance curve | **Strongly confirmed** | This is Dewey's strongest design advantage. Consider adding explicit token budget guidance per depth level |
| **#8 Empirical Feedback** | Context engineering failures are top barrier (32% of orgs); organizations with feedback loops see 40% quality gains | **Confirmed** | Utilization tracking (#3) should be prioritized |
| **#9 Progressive Disclosure** | 98% token savings; 54% agent task improvement; architectural necessity given context rot | **Strongly confirmed** | This is Dewey's second strongest advantage. The metadata -> summary -> full content -> deep reference layering directly addresses context rot |
| **#10 Explain the Why** | Causal explanations are harder to corrupt via positional bias than bare facts | **Confirmed (indirect)** | No change needed |
| **#11 Concrete Before Abstract** | Worked examples improve model performance; Claude's "canonical examples" guidance aligns | **Confirmed** | No change needed |
| **#12 Multiple Representations** | Multiple depths prevent the Kalyuga effect (novice material hindering experts); models self-select depth based on task | **Confirmed** | No change needed |

### Suggested New Principle

**#13 Position-Aware Organization** -- Place the most critical information at the beginning and end of documents. Structure content so that even if middle sections receive less attention, the key takeaways are reinforced at natural attention peaks. This is supported by the U-shaped attention pattern (Liu et al.), Anthropic's 30% improvement from document-first placement, and the Gold Panning framework (ICLR 2025).

---

## Key Takeaways

1. **Dewey's value proposition is strongly validated.** Curated, structured, right-sized context decisively outperforms naive approaches. The evidence is overwhelming and multi-sourced.

2. **Context length is toxic.** Even with perfect retrieval, performance degrades 13.9%-85% as input grows. This is architectural, not a training artifact. Dewey's tight size bounds (5-150 lines for overview, 10-400 for working) are exactly right.

3. **Progressive disclosure is the highest-leverage pattern.** It addresses the root cause (context length) rather than symptoms. The metadata -> summary -> full content layering is supported by Anthropic, LangChain, and empirical token savings of up to 98%.

4. **Structured formatting helps, but Markdown is the right default.** YAML frontmatter for metadata, Markdown for content. XML tags for prompt engineering delimiters. Avoid JSON/XML for prose content (token-expensive, no accuracy advantage for frontier models).

5. **Curation becomes MORE important as windows grow.** Bigger windows mean more room for noise, higher costs, and greater attention dilution. The "we can fit everything" premise is false -- effective context is 10-60% of advertised.

6. **The hybrid future.** The optimal architecture is curated context for the core knowledge base (<200K tokens, Dewey's sweet spot) + RAG for large external corpora + progressive disclosure for managing what's loaded at any given moment.

## Remaining Unknowns

- [ ] **No controlled A/B study of progressive disclosure by name** -- evidence is converging but indirect
- [ ] **Format effects on frontier models are diminishing** (p=0.484 in McMillan) -- monitor whether structural formatting remains valuable as models improve
- [ ] **Optimal token budgets per depth level** -- Dewey has line-count bounds but not token-count bounds; research suggests token budgets may be more predictive of performance
- [ ] **Context rot mitigation techniques** -- the Chroma finding that it's architectural suggests model-level fixes may eventually reduce curation's advantage
- [ ] **Multi-agent context partitioning patterns** -- 90.2% improvement is dramatic but under-studied; how to optimally partition knowledge across sub-agents?

## Implementation Context

<claude_context>
<application>
- when_to_use: Curated context for domain knowledge bases <200K tokens; progressive disclosure for agent workflows; structured Markdown + YAML for content format
- when_not_to_use: Do not curate when the model has zero prior knowledge of the domain (use maximum context); do not use RAG when corpus is small and stable
- prerequisites: Domain expertise to select what to include/exclude; structural conventions (frontmatter, sections, depth levels)
</application>
<technical>
- formats: Markdown for content, YAML for metadata, XML tags for prompt section delimiters
- chunk_sizes: 64-128 tokens for fact lookup, 256-512 for general RAG, 512-1024 for narrative
- retrieval: Hybrid three-way (BM25 + dense + sparse) with cross-encoder reranking
- gotchas: Coherent documents are harder to search than random text; "lost in the middle" persists in all models; effective context is 10-60% of advertised
</technical>
<integration>
- works_with: RAG (for large corpora), prompt caching (for cost reduction), multi-agent architectures (for context isolation)
- conflicts_with: "Dump everything in" strategies; naive long-context approaches
- alternatives: Fine-tuning (for stable, frequently-accessed knowledge); pure RAG (for large, dynamic corpora)
</integration>
</claude_context>

---

## Sources

### Foundational Papers
- Liu et al. "Lost in the Middle" (TACL 2024) -- [arXiv](https://arxiv.org/abs/2307.03172) | [ACL Anthology](https://aclanthology.org/2024.tacl-1.9/)
- Du et al. "Context Length Alone Hurts LLM Performance Despite Perfect Retrieval" (EMNLP 2025) -- [arXiv](https://arxiv.org/abs/2510.05381)
- Chroma Research "Context Rot" (2025) -- [Report](https://research.trychroma.com/context-rot) | [GitHub](https://github.com/chroma-core/context-rot)

### Benchmarks
- Google DeepMind LOFT -- [arXiv](https://arxiv.org/abs/2406.13121)
- NVIDIA RULER -- [arXiv](https://arxiv.org/abs/2404.06654)
- BABILong (NeurIPS 2024) -- [arXiv](https://arxiv.org/abs/2406.10149)
- LongBench v2 -- [Website](https://longbench2.github.io/)
- Adobe NoLiMa -- [arXiv](https://arxiv.org/abs/2502.05167)
- LaRA (ICML 2025) -- [arXiv](https://arxiv.org/abs/2502.09977)
- MECW -- [arXiv](https://arxiv.org/abs/2509.21361)
- Li et al. Long Context vs. RAG -- [arXiv](https://arxiv.org/abs/2501.01880)
- Self-Route -- [arXiv](https://arxiv.org/abs/2407.16833)
- ARAGOG -- [arXiv](https://arxiv.org/pdf/2404.01037)
- Chroma Evaluating Chunking -- [Report](https://research.trychroma.com/evaluating-chunking)
- Rethinking Chunk Size -- [arXiv](https://arxiv.org/html/2505.21700v2)

### Provider Guidance
- Anthropic Contextual Retrieval -- [Blog](https://www.anthropic.com/news/contextual-retrieval)
- Anthropic Context Engineering for Agents -- [Blog](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Anthropic Long Context Tips -- [Docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips)
- Anthropic Prompting Long Context -- [Blog](https://www.anthropic.com/news/prompting-long-context)
- OpenAI GPT-4.1 Prompting Guide -- [Cookbook](https://cookbook.openai.com/examples/gpt4-1_prompting_guide)
- OpenAI Optimizing LLM Accuracy -- [Docs](https://platform.openai.com/docs/guides/optimizing-llm-accuracy)
- Google Gemini Long Context -- [Docs](https://ai.google.dev/gemini-api/docs/long-context)
- Gemini 1.5 Technical Report -- [arXiv](https://arxiv.org/abs/2403.05530)

### Structured Context Research
- He et al. "Does Prompt Formatting Have Any Impact?" -- [arXiv](https://arxiv.org/abs/2411.10541)
- Liu et al. CFPO -- [arXiv](https://arxiv.org/abs/2502.04295)
- McMillan File-Native Agentic Systems -- [arXiv](https://arxiv.org/abs/2602.05447)
- DSPy+HELM Structured Prompting -- [arXiv](https://arxiv.org/abs/2511.20836)
- ACE Agentic Context Engineering -- [arXiv](https://arxiv.org/abs/2510.04618)
- ImprovingAgents Nested Data Formats -- [Blog](https://www.improvingagents.com/blog/best-nested-data-format/)
- ImprovingAgents Table Formats -- [Blog](https://www.improvingagents.com/blog/best-input-data-format-for-llms/)

### Attention & Position Research
- "Never Lost in the Middle" (ACL 2024) -- [ACL Anthology](https://aclanthology.org/2024.acl-long.736/)
- "Lost in the Middle, and In-Between" -- [arXiv](https://arxiv.org/abs/2412.10079)
- "Hidden in the Haystack" -- [arXiv](https://arxiv.org/abs/2505.18148)
- "Intelligence Degradation" -- [arXiv](https://arxiv.org/abs/2601.15300)
- "Gold Panning" (ICLR 2025) -- [arXiv](https://arxiv.org/abs/2510.09770)
- "From Bias to Benefit" (ICLR 2026) -- [OpenReview](https://openreview.net/forum?id=XNar6WUIit)
- "Mitigate Position Bias" (ICML 2024) -- [arXiv](https://arxiv.org/abs/2406.02536)

### Context Engineering & Practice
- LangChain Context Engineering -- [Blog](https://blog.langchain.com/context-engineering-for-agents/)
- Gartner Context Engineering -- [Article](https://www.gartner.com/en/articles/context-engineering)
- Factory.ai Context Window Problem -- [Blog](https://factory.ai/news/context-window-problem)
- JetBrains Complexity Trap (NeurIPS 2025) -- [Blog](https://blog.jetbrains.com/research/2025/12/efficient-context-management/)
- Pinecone Less is More -- [Blog](https://www.pinecone.io/blog/why-use-retrieval-instead-of-larger-context/)
- Databricks Long Context RAG -- [Blog](https://www.databricks.com/blog/long-context-rag-performance-llms)
- IBM Blended RAG -- [arXiv](https://arxiv.org/html/2404.07220)
- Microsoft LLMLingua -- [Research](https://www.microsoft.com/en-us/research/blog/llmlingua-innovating-llm-efficiency-with-prompt-compression/)
- Epoch AI Context Windows -- [Data](https://epoch.ai/data-insights/context-windows)
- Vectara Hallucination Leaderboard -- [Blog](https://www.vectara.com/blog/context-engineering-can-you-trust-long-context)
- RAGFlow 2025 Review -- [Blog](https://ragflow.io/blog/rag-review-2025-from-rag-to-context)
- Google GSM-IC -- [GitHub](https://github.com/google-research-datasets/GSM-IC)
- ICLR 2025 Long-Context LLMs Meet RAG -- [Proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5df5b1f121c915d8bdd00db6aac20827-Abstract-Conference.html)

### Coding Agent Context Strategies
- How Claude Code Works -- [Docs](https://code.claude.com/docs/en/how-claude-code-works)
- How Cursor Indexes Your Codebase -- [TDS](https://towardsdatascience.com/how-cursor-actually-indexes-your-codebase/)
- Aider Repo Map -- [Docs](https://aider.chat/docs/repomap.html)
- GitHub Copilot Context -- [Blog](https://roman.pt/posts/copilot-context/)

**Next Action:** Map findings to specific Dewey design principle updates, create follow-up issues for token budget guidance and position-aware organization, and update `design-principles.md` if the suggested #13 principle is approved.
