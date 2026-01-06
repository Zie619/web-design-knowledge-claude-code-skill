---
description: Disable UX Advisor - removes design skill for zero context overhead
---

# Disable UX Advisor

Remove symlink to disable the skill:

```bash
rm -f ~/.claude/skills/ux-advisor
```

After running this command, output:

```
UX Advisor DISABLED

Restart Claude Code to take effect. The skill will no longer consume context.

To re-enable: /ux-advisor-on
```
