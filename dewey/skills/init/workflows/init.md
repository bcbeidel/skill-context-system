<objective>
Understand the user's goals, evaluate the repo, and scaffold a knowledge base organized around what they're trying to accomplish.
</objective>

<required_reading>
Load `references/kb-spec-summary.md` for context on the KB specification.
</required_reading>

<process>
## Step 1: Evaluate the repo

Look at what already exists in the target directory:
- README, CLAUDE.md, or other documentation
- Directory structure and key files
- Recent git history (if available)

Build a mental model of what this project is about.

## Step 2: Ask the user what they're trying to accomplish

Ask one question: **"What are you trying to accomplish with this knowledge base, and why?"**

If `$ARGUMENTS` already provides this context, skip asking. Use what they gave you.

Listen for:
- What outcomes they want (better decisions, faster onboarding, consistent quality, etc.)
- What kind of knowledge they need to capture (domain expertise, processes, reference material, etc.)
- Who the audience is (themselves, a team, an AI assistant, etc.)

## Step 3: Propose a persona and domain areas

Based on the repo context and the user's answer, propose:

1. **A short persona** -- a 1-sentence description of who the KB serves (this becomes the role name in AGENTS.md)
2. **3-5 domain areas** -- organized around how the user thinks about the work, not technical categories

Present it conversationally:

"Based on what you've described, here's how I'd organize the knowledge base:

**Persona:** <1-sentence description>

**Domain areas:**
1. **Area Name** -- what this covers
2. **Area Name** -- what this covers
3. **Area Name** -- what this covers

These should map to how you actually think about the work. Want to adjust anything before I create the structure?"

**Key principle:** Domain-Shaped Organization. Mirror the practitioner's mental model, not textbook categories.

## Step 4: Scaffold

After the user confirms or adjusts:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <directory> --role "<persona>" --areas "<area1>,<area2>,<area3>"
```

## Step 5: Report and suggest next steps

Show what was created. Then:

1. For each domain area, suggest 2-3 starter topics based on the user's stated goals
2. Present as a numbered sequence of `/dewey:curate add <topic> in <area>` commands
3. Ask: "Want to start with the first one?"
4. Also suggest editing the "Who You Are" section in AGENTS.md to refine the persona

Example:

"Here's a plan to populate the knowledge base:

### Campaign Management
1. `/dewey:curate add Bid Strategies in campaign-management`
2. `/dewey:curate add Budget Allocation in campaign-management`

### Measurement
3. `/dewey:curate add Attribution Models in measurement`

Want to start with the first one? You can also edit the 'Who You Are' section in AGENTS.md to refine the persona."
</process>

<success_criteria>
- User's goals understood before any scaffolding
- Persona and domain areas proposed and confirmed
- Directory structure created with domain area directories
- AGENTS.md, CLAUDE.md, and index.md generated
- User has clear next steps
</success_criteria>
