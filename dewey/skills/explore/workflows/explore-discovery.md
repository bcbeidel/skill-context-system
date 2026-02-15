<objective>
Help the user discover what knowledge domains to capture by exploring their problems, tasks, and goals through structured conversation.
</objective>

<process>
## Phase 1: Understand the Problem Space

Ask ONE question at a time. Start with:

"What are the main problems or challenges you're trying to solve? What's frustrating or taking too long?"

If `$ARGUMENTS` provided context (e.g., "I work in marketing"), tailor the opening:

"You mentioned you work in [context]. What are the biggest problems or frustrations you run into in that work?"

Listen for: recurring themes, specific tools/platforms mentioned, skill gaps, pain points.

Follow up with WHY questions:
- "Why is that a problem? What happens when it goes wrong?"
- "Why does that take so long? What's the bottleneck?"
- "What would change if you had an expert guiding you through that?"

The WHY matters because it reveals the underlying knowledge gaps. Someone who says "I can't get my dashboards right" might need knowledge about data visualization, the specific BI tool, or the underlying data model -- the WHY tells you which.

Continue until you have 3-5 distinct problem areas identified. Summarize what you've heard before moving on:

"So far I'm hearing these pain points: [list]. Does that capture it, or is there something else?"

## Phase 2: Map Recurring Tasks

Ask: "What tasks do you do repeatedly where having an expert guide would help? Think about the things you do weekly or daily."

Listen for:
- Tasks with decision points (where judgment matters)
- Tasks requiring domain expertise (where getting it wrong is costly)
- Tasks where quality varies (good days vs. bad days)
- Tasks where the user second-guesses themselves

Follow up on the most promising ones:
- "Walk me through how you do [task] today. Where do you get stuck or slow down?"
- "What would a perfect version of that workflow look like?"

## Phase 3: Identify Knowledge Domains

Based on Phases 1 and 2, identify the knowledge domains that would address their problems and support their tasks. Group related problems and tasks into 3-5 coherent domains.

Present your thinking:

"Based on what you've described, I see these knowledge areas emerging:

1. **[Domain Name]** -- [why it matters to their problems]
2. **[Domain Name]** -- [why it matters]
3. **[Domain Name]** -- [why it matters]

Do these capture the right areas? Is anything missing?"

Key principles for domain naming:
- Use the practitioner's language, not academic categories
- Each domain should map to a real area of their work
- Domains should be distinct but collectively cover the full problem space
- 3-5 is the sweet spot -- fewer is too thin, more is too scattered

## Phase 4: Frame the Role

Propose a role framing that captures who the KB serves:

"It sounds like we're building a knowledge base for a **[Role Name]** -- someone who [brief description of what this role does and what success looks like].

Does that feel right, or would you frame it differently?"

The role name should be:
- Specific enough to be meaningful ("Paid Media Analyst" over "Marketer")
- Broad enough to capture the full scope ("Platform Engineer" over "Terraform User")
- Natural to the user -- if they wouldn't use this title to describe themselves, adjust it

## Phase 5: Handoff to Init

Once the user confirms the role and domains, summarize the full picture and hand off:

"Here's what we've got:

**Role:** [Role Name]
**Knowledge Domains:**
1. **[Domain]** -- [what it covers]
2. **[Domain]** -- [what it covers]
3. **[Domain]** -- [what it covers]

Let's set up the knowledge base with this structure."

Run: `/dewey:init --role "[Role Name]" --areas "[Area 1],[Area 2],[Area 3]"`

If in a context where you cannot invoke skills directly, instruct:

"Run `/dewey:init --role '[Role Name]' --areas '[Area 1],[Area 2],[Area 3]'` to create the knowledge base structure."
</process>

<key_principles>
- ONE question at a time -- don't overwhelm
- Always ask WHY -- surface the underlying knowledge gap, not just the symptom
- The user is the expert -- we help them articulate, not prescribe
- Summarize and confirm before moving to the next phase
- 3-5 domain areas is the sweet spot -- fewer is too thin, more is too scattered
- The role framing should feel natural to the user, not imposed
- Use the practitioner's own language for domain names
</key_principles>

<success_criteria>
- User feels heard and understood
- 3-5 domain areas identified with clear rationale tied to real problems
- Role framing agreed upon by the user
- Knowledge base initialized via /dewey:init
</success_criteria>
