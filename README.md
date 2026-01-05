# Web Design Knowledge RAG Skill

A Claude Code skill that provides expert web design guidance backed by a curated library of design books. Uses RAG (Retrieval-Augmented Generation) with ChromaDB and sentence-transformers for semantic search.

## Features

- **9,500+ indexed passages** from 20 professional design books
- **4 specialized MCP tools** for querying design knowledge
- **12 topic categories**: color theory, typography, layout, UX principles, UI patterns, responsive design, CSS techniques, visual hierarchy, branding, navigation, forms/inputs, performance
- **Local embeddings** using sentence-transformers (no API keys needed)
- **GPU acceleration** supported (CUDA)

## Requirements

- Python 3.10+
- Claude Code CLI
- ~500MB disk space (with indexed data)
- ~2GB disk space (for Python dependencies including PyTorch)

## Installation

### Step 1: Extract the Skill

```bash
# Create skills directory if it doesn't exist
mkdir -p ~/.claude/skills

# Extract the zip file
unzip web-design-knowledge.zip -d ~/.claude/skills/
```

### Step 2: Set Up Python Environment

```bash
cd ~/.claude/skills/web-design-knowledge

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r server/requirements.txt
```

### Step 3: Register MCP Server

```bash
claude mcp add --transport stdio web_design_mcp --scope user \
    --env CHROMADB_PATH="$HOME/.claude/skills/web-design-knowledge/data/chromadb" \
    -- "$HOME/.claude/skills/web-design-knowledge/venv/bin/python" \
    "$HOME/.claude/skills/web-design-knowledge/server/web_design_mcp.py"
```

### Step 4: Restart Claude Code

```bash
# Exit current session and restart
exit
claude
```

### Step 5: Verify Installation

```bash
# Check MCP server is connected
claude mcp list
```

You should see `web_design_mcp` in the list with status "Connected".

## Processing Your Own Books (Optional)

If you want to index your own PDF design books:

```bash
cd ~/.claude/skills/web-design-knowledge
source venv/bin/activate

# Install processing dependencies
pip install -r scripts/requirements.txt

# Process PDFs from a directory
python scripts/process_pdfs.py --pdf-dir /path/to/your/pdf/books
```

## Usage

Once installed, the skill is automatically available in Claude Code. Simply ask design-related questions:

- "What color palette should I use for a healthcare app?"
- "How should I structure the layout for a dashboard?"
- "What are best practices for checkout flow UX?"
- "Help me design the typography hierarchy for this landing page"

### Available MCP Tools

| Tool | Purpose |
|------|---------|
| `web_design_query` | General design questions with topic filtering |
| `web_design_color_advice` | Color palette and harmony guidance |
| `web_design_layout_patterns` | Layout recommendations by page type |
| `web_design_ux_review` | UX best practices for specific features |

### Topic Filters

When using `web_design_query`, you can filter by topic:
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

## Troubleshooting

### MCP Server Won't Connect

1. Check Python path is correct:
   ```bash
   ls -la ~/.claude/skills/web-design-knowledge/venv/bin/python
   ```

2. Verify ChromaDB data exists:
   ```bash
   ls -la ~/.claude/skills/web-design-knowledge/data/chromadb/
   ```

3. Test server manually:
   ```bash
   cd ~/.claude/skills/web-design-knowledge
   source venv/bin/activate
   python server/web_design_mcp.py --help
   ```

### Slow First Query

The first query loads the embedding model (~400MB) into memory. Subsequent queries are fast. GPU acceleration (CUDA) significantly speeds this up.

### Out of Memory

If you run out of memory, the system will fall back to CPU. Ensure you have at least 4GB RAM available.

## File Structure

```
web-design-knowledge/
├── SKILL.md              # Claude Code skill definition
├── README.md             # This file
├── LICENSE.txt           # License information
├── server/
│   ├── web_design_mcp.py # MCP server implementation
│   └── requirements.txt  # Server dependencies
├── scripts/
│   ├── process_pdfs.py   # PDF processing pipeline
│   ├── chunk_processor.py # Smart chunking logic
│   └── requirements.txt  # Processing dependencies
├── config/
│   ├── books_metadata.yaml   # Book categorization
│   └── topic_taxonomy.yaml   # Topic definitions
├── data/
│   └── chromadb/         # Vector database (indexed content)
└── references/
    └── design_topics.md  # Topic reference guide
```

## Uninstall

```bash
# Remove MCP server
claude mcp remove web_design_mcp

# Delete skill directory
rm -rf ~/.claude/skills/web-design-knowledge
```
