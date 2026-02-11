---
description: Run quality checks on context files (pre-commit hook style)
---

# Check Context Quality

Run pre-commit style quality checks on context files to ensure they meet best practices and quality standards.

## How to Use

```
/dewey:check
/dewey:check --fast
/dewey:check --fix-links
```

## Status

🚧 **Under Development** - Coming in Phase 1

This command will validate:
- File sizes (<500 lines)
- No dead links
- No excessive duplication
- Token budget within limits
- Best practices compliance

---

**Arguments**: $ARGUMENTS
