# UX Advisor - Web Design Knowledge Skill

A Claude Code skill that provides expert web design guidance backed by a curated library of 23 design books. Uses RAG (Retrieval-Augmented Generation) with ChromaDB and sentence-transformers for semantic search.

## Key Feature: On-Demand Activation

Unlike always-on MCP servers that consume context tokens constantly, this skill uses **symlink-based activation**:

- **OFF**: Zero context overhead (skill doesn't exist)
- **ON**: Natural language design queries work automatically

Toggle with `/ux-advisor-on` and `/ux-advisor-off` commands.

## Features

- **9,500+ indexed passages** from 23 professional design books
- **On-demand activation** - zero overhead when disabled
- **Natural language queries** - ask design questions conversationally
- **12 topic categories**: color theory, typography, layout, UX principles, UI patterns, responsive design, CSS techniques, visual hierarchy, branding, navigation, forms/inputs, performance
- **Local embeddings** using sentence-transformers (no API keys needed)
- **Concise responses** - optimized for minimal context consumption

## Requirements

- Python 3.10+
- Claude Code CLI
- ~500MB disk space (with indexed data)
- ~2GB disk space (for Python dependencies including PyTorch)

## Installation

### Step 1: Clone/Extract the Project

```bash
# Clone or extract to any location
git clone <repo> ~/projects/ux-advisor
# or
unzip ux-advisor.zip -d ~/projects/
```

### Step 2: Set Up Python Environment

```bash
cd ~/projects/ux-advisor/web-design-knowledge

# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install chromadb sentence-transformers pyyaml
```

### Step 3: Install Toggle Commands

```bash
# Create commands directory if needed
mkdir -p ~/.claude/commands

# Copy the toggle commands
cp commands/ux-advisor-on.md ~/.claude/commands/
cp commands/ux-advisor-off.md ~/.claude/commands/
```

Or manually create them (see [Toggle Commands](#toggle-commands) below).

### Step 4: Enable the Skill

```bash
# Run the enable command in Claude Code
/ux-advisor-on

# Then restart Claude Code
exit
claude
```

## Usage

### Enable/Disable

```bash
/ux-advisor-on   # Enable skill (creates symlink, restart required)
/ux-advisor-off  # Disable skill (removes symlink, restart required)
```

### Ask Design Questions

Once enabled, just ask naturally:

- "What color palette should I use for a healthcare app?"
- "How should I structure the layout for a dashboard?"
- "What are best practices for checkout flow UX?"
- "Help me design the typography hierarchy for this landing page"

### Query Types

The skill automatically routes queries based on keywords:

| Detected Keywords | Query Type | Focus |
|-------------------|------------|-------|
| color, palette, contrast, hue | Color | Color theory, harmony, accessibility |
| layout, grid, spacing, structure | Layout | Page structure, responsive design |
| UX, usability, flow, onboarding | UX | User experience, best practices |
| Other design questions | General | All topics |

### Topic Filters

Available topics for filtering:
- `color_theory` - Color palettes, contrast, harmony
- `typography` - Font selection, hierarchy, readability
- `layout` - Grid systems, spacing, composition
- `ux_principles` - Usability, accessibility, user research
- `ui_patterns` - Common UI components and patterns
- `responsive` - Mobile-first, breakpoints, fluid design
- `css_techniques` - CSS properties, animations, modern features
- `visual_hierarchy` - Emphasis, contrast, attention flow
- `branding` - Brand identity, consistency, design systems
- `navigation` - Menus, wayfinding, information architecture
- `forms_inputs` - Form design, validation, user input
- `performance` - Load times, optimization, Core Web Vitals

## Toggle Commands

### ux-advisor-on.md

```markdown
---
description: Enable UX Advisor - expert web design guidance from 23 design books
---

# Enable UX Advisor

Create symlink to enable the skill:

\`\`\`bash
ln -sf /path/to/your/project/web-design-knowledge ~/.claude/skills/ux-advisor
\`\`\`

After running this command, output:

UX Advisor ENABLED. Restart Claude Code to activate.
```

### ux-advisor-off.md

```markdown
---
description: Disable UX Advisor - removes design skill for zero context overhead
---

# Disable UX Advisor

Remove symlink:

\`\`\`bash
rm -f ~/.claude/skills/ux-advisor
\`\`\`

After running, output:

UX Advisor DISABLED. Restart Claude Code to take effect.
```

**Important**: Update the path in `ux-advisor-on.md` to match your installation location.

## CLI Script (Advanced)

You can also query the knowledge base directly:

```bash
cd /path/to/web-design-knowledge

# General query
./venv/bin/python scripts/query_kb.py --query "How do I create visual hierarchy?"

# Color-specific query
./venv/bin/python scripts/query_kb.py --query "fintech app" --type color --mood trustworthy

# Layout query
./venv/bin/python scripts/query_kb.py --query "dashboard" --type layout --page-type dashboard

# UX query
./venv/bin/python scripts/query_kb.py --query "checkout flow" --type ux
```

### CLI Options

```
--query, -q      Design question (required)
--type, -t       Query type: general|color|layout|ux (default: general)
--n-results, -n  Number of results (default: 3, max: 10)
--format, -f     Output: markdown|json (default: markdown)
--topics         Topic filter (comma-separated, for general queries)
--mood           For color: professional|playful|calm|energetic|luxurious|trustworthy|modern|minimalist|bold|warm
--page-type      For layout: landing_page|dashboard|blog|portfolio|ecommerce|settings|profile|search_results|form_page|documentation
--user-context   For UX: target user description
```

## Processing Your Own Books (Optional)

To index additional PDF design books:

```bash
cd /path/to/web-design-knowledge
source venv/bin/activate

# Install processing dependencies
pip install -r scripts/requirements.txt

# Process PDFs from a directory
python scripts/process_pdfs.py --pdf-dir /path/to/your/pdf/books
```

## Troubleshooting

### Skill Not Triggering

1. Verify symlink exists:
   ```bash
   ls -la ~/.claude/skills/ux-advisor
   ```

2. Check it points to the correct location:
   ```bash
   readlink ~/.claude/skills/ux-advisor
   ```

3. Restart Claude Code after enabling/disabling

### Slow First Query

The first query loads the embedding model (~400MB) into memory. Subsequent queries are fast. GPU acceleration (CUDA) significantly speeds this up.

### Out of Memory

If you run out of memory, the system will fall back to CPU. Ensure you have at least 4GB RAM available.

### Test CLI Directly

```bash
cd /path/to/web-design-knowledge
./venv/bin/python scripts/query_kb.py --query "test query" --n-results 1
```

## File Structure

```
web-design-knowledge/
├── SKILL.md              # Claude Code skill definition
├── README.md             # This file
├── LICENSE.txt           # License information
├── commands/             # Template commands (copy to ~/.claude/commands/)
│   ├── ux-advisor-on.md  # Enable skill command
│   └── ux-advisor-off.md # Disable skill command
├── scripts/
│   ├── query_kb.py       # CLI query tool
│   ├── process_pdfs.py   # PDF processing pipeline
│   ├── chunk_processor.py # Smart chunking logic
│   └── requirements.txt  # Processing dependencies
├── server/
│   └── web_design_mcp.py # Legacy MCP server (optional)
├── config/
│   ├── books_metadata.yaml   # Book categorization
│   └── topic_taxonomy.yaml   # Topic definitions
├── data/
│   └── chromadb/         # Vector database (indexed content)
├── venv/                 # Python virtual environment
└── references/
    └── design_topics.md  # Topic reference guide
```

## Uninstall

```bash
# Disable the skill
/ux-advisor-off

# Remove toggle commands
rm ~/.claude/commands/ux-advisor-on.md
rm ~/.claude/commands/ux-advisor-off.md

# Optionally remove the project
rm -rf /path/to/web-design-knowledge
```

## Context Efficiency

| State | Context Overhead |
|-------|-----------------|
| Disabled (symlink removed) | **0 tokens** |
| Enabled, idle | ~500-1,000 tokens (skill metadata) |
| Enabled, after query | +1,500-3,000 tokens (results) |

Compare to always-on MCP: **4,000-8,000 tokens constant overhead**.
