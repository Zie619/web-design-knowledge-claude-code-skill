---
name: ux-advisor
description: Expert web design guidance backed by 23 design books. Use when users ask about color palettes, typography, layouts, UX patterns, responsive design, or CSS techniques. Triggers on design questions like "what colors", "how to layout", "UX best practices", "typography for".
version: 2.0.0
---

# UX Advisor - Web Design Knowledge

Expert design guidance from 23 curated professional books covering color theory, typography, layout, UX/UI patterns, responsive design, and CSS techniques.

## How to Query

Run the CLI script to search the knowledge base. The skill is installed at `~/.claude/skills/ux-advisor/`.

```bash
# General design question
~/.claude/skills/ux-advisor/venv/bin/python ~/.claude/skills/ux-advisor/scripts/query_kb.py --query "YOUR QUESTION"

# Color advice
~/.claude/skills/ux-advisor/venv/bin/python ~/.claude/skills/ux-advisor/scripts/query_kb.py --query "CONTEXT" --type color --mood MOOD

# Layout patterns
~/.claude/skills/ux-advisor/venv/bin/python ~/.claude/skills/ux-advisor/scripts/query_kb.py --query "PAGE TYPE" --type layout --page-type TYPE

# UX best practices
~/.claude/skills/ux-advisor/venv/bin/python ~/.claude/skills/ux-advisor/scripts/query_kb.py --query "FEATURE" --type ux
```

## Query Types

| Type | Use For | Key Options |
|------|---------|-------------|
| `general` | Open design questions | `--topics` (comma-separated) |
| `color` | Color palettes, harmony | `--mood` (professional, playful, calm, etc.) |
| `layout` | Page structure, grids | `--page-type` (dashboard, landing_page, etc.) |
| `ux` | Usability, user flows | `--user-context` |

## Routing Guide

Detect query type from user's question:

- **Color**: "color", "palette", "contrast", "hue", "scheme" → `--type color`
- **Layout**: "layout", "grid", "spacing", "structure", "responsive" → `--type layout`
- **UX**: "UX", "usability", "user experience", "flow", "onboarding" → `--type ux`
- **Other**: general design questions → `--type general`

## Options Reference

```
--query, -q     Design question (required)
--type, -t      Query type: general|color|layout|ux (default: general)
--n-results, -n Number of results (default: 3, max: 10)
--format, -f    Output: markdown|json (default: markdown)
--topics        Topic filter for general: color_theory,typography,layout,ux_principles,ui_patterns,responsive,css_techniques,visual_hierarchy,branding,navigation,forms_inputs,performance
--mood          For color: professional|playful|calm|energetic|luxurious|trustworthy|modern|minimalist|bold|warm
--page-type     For layout: landing_page|dashboard|blog|portfolio|ecommerce|settings|profile|search_results|form_page|documentation
--density       For layout: low|medium|high
--user-context  For UX: target user description
```

## Response Guidelines

1. **Synthesize** - Combine insights from multiple sources
2. **Adapt** - Apply principles to user's specific context
3. **Be concise** - Focus on actionable advice
4. **Cite when relevant** - Mention which book informed the advice

## Topics Covered

- Color Theory & Psychology
- Typography & Type Hierarchy
- Layout & Grid Systems
- UX Principles & Heuristics
- UI Patterns & Components
- Responsive Design
- CSS Techniques
- Visual Hierarchy
- Branding & Design Systems
- Navigation & Information Architecture
- Forms & Input Design
- Performance Optimization
