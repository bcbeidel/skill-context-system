<objective>
Understand the user's goals, evaluate the repo, and scaffold a knowledge base organized around what they're trying to accomplish.
</objective>

<required_reading>
Load `references/kb-spec-summary.md` for context on the knowledge base specification.
</required_reading>

<process>
## Step 0: Check for existing knowledge base

Check if `.dewey/config.json` exists in the target directory.

If it does, this is a **re-init** — the user wants to modify an existing knowledge base:

1. Read existing config, AGENTS.md, and `.dewey/curation-plan.md`
2. Show the user: persona, domain areas, curated topic count, curation plan progress
3. Ask what they want to change (add areas, update persona, change directory)
4. For adding areas: propose only the NEW areas, then proceed to Step 5 with ALL areas (existing + new)

Important: scaffold preserves existing topic entries and curation progress automatically.
Pass the complete area list (existing + new) to the scaffold command.

If no config exists, proceed to Step 1 as normal.

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

1. **A short persona** -- a 1-sentence description of who the knowledge base serves (this becomes the role name in AGENTS.md)
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

## Step 4: Ask about knowledge directory location

Ask the user: **"Where would you like to store the knowledge base files? (default: `docs`)"**

If the user doesn't provide a specific answer, use `docs` as the default.

## Step 5: Scaffold

After the user confirms or adjusts:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/scaffold.py --target <directory> --role "<persona>" --areas "<area1>,<area2>,<area3>" --knowledge-dir "<user's answer or docs>"
```

## Step 6: Report, build the curation plan, and suggest next steps

Show what was created. Then build the curation plan:

1. For each domain area, propose 2-3 starter topics based on the user's stated goals
2. Present them conversationally grouped by area and ask the user to confirm or adjust
3. After confirmation, write `.dewey/curation-plan.md` directly with this format:

```markdown
---
last_updated: <today's date YYYY-MM-DD>
---

# Curation Plan

## <area-slug>
- [ ] Topic Name -- core -- brief rationale
- [ ] Topic Name -- core -- brief rationale

## <area-slug>
- [ ] Topic Name -- core -- brief rationale
```

4. Present the plan as the living roadmap:

"Here's your curation plan -- use `/dewey:curate plan` to track progress:

<show the plan content>

Start with the first unchecked item using `/dewey:curate add <first-topic> in <first-area>`. You can also edit the 'Who You Are' section in AGENTS.md to refine the persona."
</process>

<success_criteria>
- User's goals understood before any scaffolding
- Persona and domain areas proposed and confirmed
- Directory structure created with domain area directories
- AGENTS.md, CLAUDE.md, and index.md generated
- User has clear next steps
</success_criteria>
