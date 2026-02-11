---
name: report
description: Generate markdown dashboard reports with trends, KPIs, and insights from context analysis history
---

<essential_principles>
## What This Skill Does

Generates comprehensive dashboard reports showing context health trends over time. Analyzes historical analysis data to identify patterns, wins, and concerns.

## Core Workflow

1. **Python reads analysis history** - Loads baseline and comparison data
2. **Calculates trends and KPIs** - Week-over-week, month-over-month changes
3. **Generates structured data** - Statistics, trends, anomalies
4. **Claude creates dashboard** - Formats insights into readable markdown
5. **Saves to file** - Writes dashboard to `.claude/analytics/dashboard.md`

## Report Types

**Weekly Dashboard:**
- Last 7 days of changes
- Quick health check
- Recent optimization wins
- Emerging issues

**Monthly Dashboard:**
- Last 30 days of changes
- Long-term trends
- Cumulative impact
- Strategic insights

**Custom Dashboard:**
- Specific date range
- Comparative analysis
- Project milestones
- Custom KPIs

## Design Philosophy

- **Visual clarity** - Use charts, emojis, colors
- **Actionable insights** - Not just data, but "so what?"
- **Trend focus** - Direction matters more than absolute values
- **Celebrate wins** - Highlight successful optimizations
- **Flag concerns** - Early warning for degradation

## Key Variables

- `$ARGUMENTS` - Report type and options (--weekly, --monthly, etc.)
- `${CLAUDE_PLUGIN_ROOT}` - Root directory of the Dewey plugin
</essential_principles>

<intake>
What type of report would you like to generate?

1. **Weekly dashboard** - Last 7 days of context health
2. **Monthly dashboard** - Last 30 days with trends
3. **Custom range** - Specify dates or comparison points

**Default:** If no arguments, generates weekly dashboard
</intake>

<routing>
## Argument-Based Routing

Parse `$ARGUMENTS` for report type:

- Contains `--monthly` → Route to workflows/report-monthly.md
- Contains `--custom` or date arguments → Route to workflows/report-custom.md
- Otherwise (default/--weekly) → Route to workflows/report-weekly.md

**Interactive routing:**

| User Response | Workflow |
|---------------|----------|
| 1, "weekly", "week" | workflows/report-weekly.md |
| 2, "monthly", "month" | workflows/report-monthly.md |
| 3, "custom", "range" | workflows/report-custom.md |

After determining workflow, load and follow it exactly.
</routing>

<workflows_index>
## Available Workflows

All workflows in `workflows/`:

| Workflow | Purpose |
|----------|---------|
| report-weekly.md | Generate 7-day dashboard report |
| report-monthly.md | Generate 30-day dashboard with trends |
| report-custom.md | Generate custom date range report |
</workflows_index>

<references_index>
## Domain Knowledge

All references in `references/`:

| Reference | Content |
|-----------|---------|
| dashboard-design.md | Principles for effective dashboards |
| trend-analysis.md | Understanding and interpreting trends |
| kpis-tracking.md | Key performance indicators for context health |
</references_index>

<scripts_integration>
## Python Helper Script

Located in `scripts/`:

**generate_report.py** - Report generation script
- Reads baseline from `~/.claude/analytics/baseline.json`
- Loads historical analysis data if available
- Calculates trends and statistics
- Identifies wins and concerns
- Generates structured data for Claude

**Usage in workflows:**
```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/report/scripts/generate_report.py $ARGUMENTS
```

The script outputs:
- Summary statistics
- Trend data (if historical data exists)
- KPI status
- Recommendations for dashboard content

**Note:** If no historical data exists, provides guidance for setting up tracking.
</scripts_integration>

<success_criteria>
Report generation is successful when:
- ✅ Historical data loaded (or handled gracefully if missing)
- ✅ Trends calculated correctly
- ✅ Dashboard is visually clear and scannable
- ✅ Insights are actionable
- ✅ Wins are celebrated, concerns are flagged
- ✅ Dashboard saved to `.claude/analytics/dashboard.md`
- ✅ User knows when to run next report
</success_criteria>
