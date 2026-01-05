#!/usr/bin/env python3
"""
MCP Server for Web Design Knowledge.

Provides tools to query a curated knowledge base of 23 web design books,
offering guidance on color theory, typography, layout, UX/UI patterns,
responsive design, and more.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("web_design_mcp")

# Constants
CHARACTER_LIMIT = 25000
DEFAULT_RESULTS = 5
MAX_RESULTS = 15

# Environment configuration
CHROMADB_PATH = os.environ.get(
    "CHROMADB_PATH",
    str(Path(__file__).parent.parent / "data" / "chromadb")
)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Global instances (initialized on first use)
_collection = None
_embedding_model = None


def get_collection():
    """Get or create the ChromaDB collection."""
    global _collection
    if _collection is None:
        logger.info(f"Connecting to ChromaDB at {CHROMADB_PATH}")
        client = chromadb.PersistentClient(
            path=CHROMADB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = client.get_collection("web_design_knowledge")
        logger.info(f"Connected to collection with {_collection.count()} documents")
    return _collection


def get_embedding_model():
    """Get or create the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


# Enums
class ResponseFormat(str, Enum):
    """Output format for responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class DesignTopic(str, Enum):
    """Design topic categories."""
    COLOR_THEORY = "color_theory"
    TYPOGRAPHY = "typography"
    LAYOUT = "layout"
    UX_PRINCIPLES = "ux_principles"
    UI_PATTERNS = "ui_patterns"
    RESPONSIVE = "responsive"
    CSS_TECHNIQUES = "css_techniques"
    VISUAL_HIERARCHY = "visual_hierarchy"
    BRANDING = "branding"
    NAVIGATION = "navigation"
    FORMS_INPUTS = "forms_inputs"
    PERFORMANCE = "performance"


class PageType(str, Enum):
    """Common page types for layout recommendations."""
    LANDING_PAGE = "landing_page"
    DASHBOARD = "dashboard"
    BLOG = "blog"
    PORTFOLIO = "portfolio"
    ECOMMERCE = "ecommerce"
    SETTINGS = "settings"
    PROFILE = "profile"
    SEARCH_RESULTS = "search_results"
    FORM_PAGE = "form_page"
    DOCUMENTATION = "documentation"


class Mood(str, Enum):
    """Emotional tones for color guidance."""
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    CALM = "calm"
    ENERGETIC = "energetic"
    LUXURIOUS = "luxurious"
    TRUSTWORTHY = "trustworthy"
    MODERN = "modern"
    MINIMALIST = "minimalist"
    BOLD = "bold"
    WARM = "warm"


# Pydantic Input Models
class DesignQueryInput(BaseModel):
    """Input for general web design queries."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(
        ...,
        description="Natural language question about web design (e.g., 'How do I create visual hierarchy?', 'What makes a good navigation menu?')",
        min_length=10,
        max_length=500
    )

    topics: Optional[List[DesignTopic]] = Field(
        default=None,
        description="Filter results by design topics. Leave empty to search all topics.",
        max_length=5
    )

    n_results: int = Field(
        default=DEFAULT_RESULTS,
        description="Number of relevant passages to retrieve",
        ge=1,
        le=MAX_RESULTS
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for readable text, 'json' for structured data"
    )


class ColorAdviceInput(BaseModel):
    """Input for specialized color guidance."""
    model_config = ConfigDict(str_strip_whitespace=True)

    context: str = Field(
        ...,
        description="Design context for color advice (e.g., 'e-commerce site for organic food', 'fintech mobile app', 'children's educational platform')",
        min_length=10,
        max_length=300
    )

    mood: Optional[Mood] = Field(
        default=None,
        description="Desired emotional tone for the color palette"
    )

    constraints: Optional[str] = Field(
        default=None,
        description="Color constraints (e.g., 'must include brand blue #0066CC', 'avoid red', 'use earth tones')",
        max_length=200
    )

    include_accessibility: bool = Field(
        default=True,
        description="Include WCAG accessibility guidance for color contrast"
    )


class LayoutPatternsInput(BaseModel):
    """Input for layout pattern recommendations."""
    model_config = ConfigDict(str_strip_whitespace=True)

    page_type: PageType = Field(
        ...,
        description="Type of page to design"
    )

    device_target: str = Field(
        default="responsive",
        description="Target device: 'responsive', 'mobile', 'tablet', 'desktop'"
    )

    content_density: str = Field(
        default="medium",
        description="Content density: 'low' (minimal), 'medium' (balanced), 'high' (data-rich)"
    )

    key_elements: Optional[str] = Field(
        default=None,
        description="Key elements to include (e.g., 'hero section, feature cards, testimonials')",
        max_length=300
    )


class UXReviewInput(BaseModel):
    """Input for UX best practices review."""
    model_config = ConfigDict(str_strip_whitespace=True)

    feature: str = Field(
        ...,
        description="Feature or flow to review (e.g., 'checkout flow', 'user onboarding', 'search functionality', 'settings page')",
        min_length=5,
        max_length=200
    )

    current_approach: Optional[str] = Field(
        default=None,
        description="Brief description of current implementation (if reviewing existing design)",
        max_length=500
    )

    user_context: Optional[str] = Field(
        default=None,
        description="Target user context (e.g., 'first-time users', 'power users', 'mobile users')",
        max_length=200
    )


# Helper Functions
def query_knowledge_base(
    query: str,
    n_results: int = 5,
    topic_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Query the ChromaDB knowledge base."""
    collection = get_collection()
    model = get_embedding_model()

    # Generate query embedding
    query_embedding = model.encode([query])[0].tolist()

    # Build where clause for topic filtering
    where_clause = None
    if topic_filter and len(topic_filter) > 0:
        if len(topic_filter) == 1:
            where_clause = {"primary_topic": {"$eq": topic_filter[0]}}
        else:
            where_clause = {
                "$or": [{"primary_topic": {"$eq": t}} for t in topic_filter]
            }

    # Query collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_clause,
        include=["documents", "metadatas", "distances"]
    )

    # Format results
    passages = []
    if results and results['documents'] and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i] if results['metadatas'] else {}
            distance = results['distances'][0][i] if results['distances'] else 0

            passages.append({
                "content": doc,
                "source": {
                    "book": meta.get("book_title", "Unknown"),
                    "author": meta.get("author", "Unknown"),
                    "chapter": meta.get("chapter", ""),
                    "page_range": f"{meta.get('page_start', '')}-{meta.get('page_end', '')}",
                },
                "topic": meta.get("primary_topic", ""),
                "relevance_score": round(1 - distance, 3) if distance else 0,
            })

    return passages


def format_passages_markdown(passages: List[Dict], query: str) -> str:
    """Format passages as markdown."""
    if not passages:
        return f"No relevant design guidance found for: '{query}'\n\nTry rephrasing your question or removing topic filters."

    lines = [f"# Design Guidance: {query[:50]}...\n" if len(query) > 50 else f"# Design Guidance: {query}\n"]
    lines.append(f"Found {len(passages)} relevant passages from the design knowledge base.\n")

    for i, p in enumerate(passages, 1):
        lines.append(f"## Source {i}: {p['source']['book']}")
        if p['source']['author']:
            lines.append(f"*By {p['source']['author']}*")
        if p['topic']:
            lines.append(f"\n**Topic**: {p['topic'].replace('_', ' ').title()}")
        lines.append(f"\n{p['content']}\n")
        lines.append("---\n")

    return "\n".join(lines)


def format_passages_json(passages: List[Dict], query: str) -> str:
    """Format passages as JSON."""
    return json.dumps({
        "query": query,
        "result_count": len(passages),
        "passages": passages
    }, indent=2)


# Tool Definitions
@mcp.tool(
    name="web_design_query",
    annotations={
        "title": "Query Web Design Knowledge",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def web_design_query(params: DesignQueryInput) -> str:
    """
    Query the web design knowledge base for principles, best practices, and techniques.

    This tool searches through 23 curated web design books covering color theory,
    typography, layout, UX/UI patterns, responsive design, CSS techniques, and more.

    Args:
        params (DesignQueryInput): Query parameters including:
            - query (str): Natural language question about web design
            - topics (Optional[List[DesignTopic]]): Filter by design topics
            - n_results (int): Number of passages to retrieve (1-15)
            - response_format (ResponseFormat): Output format (markdown/json)

    Returns:
        str: Relevant passages from the knowledge base with source citations

    Examples:
        - "How do I create effective visual hierarchy?" - General design question
        - "What are best practices for form validation?" - Specific UX question
        - "How should I choose typography for a corporate website?" - Typography focused
    """
    try:
        # Convert topic enums to strings for query
        topic_filter = [t.value for t in params.topics] if params.topics else None

        # Query knowledge base
        passages = query_knowledge_base(
            query=params.query,
            n_results=params.n_results,
            topic_filter=topic_filter
        )

        # Format response
        if params.response_format == ResponseFormat.JSON:
            result = format_passages_json(passages, params.query)
        else:
            result = format_passages_markdown(passages, params.query)

        # Check character limit
        if len(result) > CHARACTER_LIMIT:
            result = result[:CHARACTER_LIMIT] + "\n\n[Output truncated due to size limit]"

        return result

    except Exception as e:
        logger.error(f"Error in web_design_query: {e}")
        return f"Error querying design knowledge base: {str(e)}"


@mcp.tool(
    name="web_design_color_advice",
    annotations={
        "title": "Get Color Palette Advice",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def web_design_color_advice(params: ColorAdviceInput) -> str:
    """
    Get specialized color palette and harmony advice for web design.

    Provides color theory guidance, palette suggestions, and accessibility
    recommendations based on the design context and desired mood.

    Args:
        params (ColorAdviceInput): Parameters including:
            - context (str): Design context (e.g., 'healthcare app', 'fashion e-commerce')
            - mood (Optional[Mood]): Desired emotional tone
            - constraints (Optional[str]): Color constraints or requirements
            - include_accessibility (bool): Include WCAG guidance

    Returns:
        str: Color guidance with palette suggestions and best practices

    Examples:
        - context="fintech dashboard", mood="trustworthy" - Professional palette
        - context="children's learning app", mood="playful" - Vibrant palette
        - context="luxury hotel booking", mood="luxurious" - Elegant palette
    """
    try:
        # Build comprehensive query
        query_parts = [f"color palette for {params.context}"]

        if params.mood:
            query_parts.append(f"{params.mood.value} color scheme")

        if params.constraints:
            query_parts.append(params.constraints)

        if params.include_accessibility:
            query_parts.append("color contrast accessibility WCAG")

        full_query = " ".join(query_parts)

        # Query with color theory focus
        passages = query_knowledge_base(
            query=full_query,
            n_results=7,
            topic_filter=["color_theory", "visual_hierarchy"]
        )

        # Build response
        lines = [f"# Color Advice for: {params.context}\n"]

        if params.mood:
            lines.append(f"**Mood**: {params.mood.value.title()}\n")

        if params.constraints:
            lines.append(f"**Constraints**: {params.constraints}\n")

        lines.append("\n## Color Theory Guidance\n")

        for i, p in enumerate(passages[:5], 1):
            lines.append(f"### Insight {i} ({p['source']['book']})")
            lines.append(f"\n{p['content']}\n")

        if params.include_accessibility:
            lines.append("\n## Accessibility Reminders\n")
            lines.append("- Maintain minimum 4.5:1 contrast ratio for normal text (WCAG AA)")
            lines.append("- Use 3:1 minimum for large text and UI components")
            lines.append("- Don't rely on color alone to convey information")
            lines.append("- Test with color blindness simulators\n")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error in web_design_color_advice: {e}")
        return f"Error getting color advice: {str(e)}"


@mcp.tool(
    name="web_design_layout_patterns",
    annotations={
        "title": "Get Layout Pattern Recommendations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def web_design_layout_patterns(params: LayoutPatternsInput) -> str:
    """
    Get layout patterns and structural recommendations for specific page types.

    Provides grid systems, spacing guidance, and layout best practices
    tailored to the page type and device target.

    Args:
        params (LayoutPatternsInput): Parameters including:
            - page_type (PageType): Type of page to design
            - device_target (str): Target device (responsive/mobile/tablet/desktop)
            - content_density (str): Content density (low/medium/high)
            - key_elements (Optional[str]): Key elements to include

    Returns:
        str: Layout recommendations with patterns and spacing guidance

    Examples:
        - page_type="dashboard", content_density="high" - Data-rich layout
        - page_type="landing_page", device_target="mobile" - Mobile-first landing
        - page_type="portfolio", key_elements="project cards, about section"
    """
    try:
        # Build comprehensive query
        query_parts = [
            f"layout design for {params.page_type.value.replace('_', ' ')}",
            f"{params.device_target} layout",
            f"{params.content_density} content density"
        ]

        if params.key_elements:
            query_parts.append(params.key_elements)

        full_query = " ".join(query_parts)

        # Query with layout focus
        passages = query_knowledge_base(
            query=full_query,
            n_results=7,
            topic_filter=["layout", "responsive", "visual_hierarchy"]
        )

        # Build response
        lines = [f"# Layout Patterns: {params.page_type.value.replace('_', ' ').title()}\n"]
        lines.append(f"**Target**: {params.device_target.title()}")
        lines.append(f"**Density**: {params.content_density.title()}\n")

        if params.key_elements:
            lines.append(f"**Key Elements**: {params.key_elements}\n")

        lines.append("\n## Layout Recommendations\n")

        for i, p in enumerate(passages[:5], 1):
            lines.append(f"### Pattern {i} ({p['source']['book']})")
            lines.append(f"\n{p['content']}\n")

        # Add page-type specific tips
        lines.append("\n## Quick Tips\n")

        if params.page_type == PageType.DASHBOARD:
            lines.append("- Use a 12-column grid for flexible widget placement")
            lines.append("- Group related metrics in card components")
            lines.append("- Prioritize critical data above the fold")
        elif params.page_type == PageType.LANDING_PAGE:
            lines.append("- Lead with a compelling hero section")
            lines.append("- Use visual hierarchy to guide the eye downward")
            lines.append("- Include clear calls-to-action at key points")
        elif params.page_type == PageType.ECOMMERCE:
            lines.append("- Optimize product grid for scanning")
            lines.append("- Keep filters accessible but not intrusive")
            lines.append("- Make cart/checkout always visible")

        lines.append("")
        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error in web_design_layout_patterns: {e}")
        return f"Error getting layout patterns: {str(e)}"


@mcp.tool(
    name="web_design_ux_review",
    annotations={
        "title": "Get UX Best Practices Review",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def web_design_ux_review(params: UXReviewInput) -> str:
    """
    Get UX best practices and usability guidelines for specific features or flows.

    Provides user experience principles, common pitfalls, and recommendations
    for improving usability of specific interface features.

    Args:
        params (UXReviewInput): Parameters including:
            - feature (str): Feature or flow to review
            - current_approach (Optional[str]): Current implementation description
            - user_context (Optional[str]): Target user context

    Returns:
        str: UX guidance with best practices and improvement suggestions

    Examples:
        - feature="checkout flow" - E-commerce checkout UX
        - feature="user onboarding", user_context="first-time users"
        - feature="search functionality", current_approach="basic search box"
    """
    try:
        # Build comprehensive query
        query_parts = [f"UX best practices for {params.feature}"]

        if params.current_approach:
            query_parts.append(f"improving {params.current_approach}")

        if params.user_context:
            query_parts.append(f"for {params.user_context}")

        full_query = " ".join(query_parts)

        # Query with UX focus
        passages = query_knowledge_base(
            query=full_query,
            n_results=8,
            topic_filter=["ux_principles", "ui_patterns", "forms_inputs", "navigation"]
        )

        # Build response
        lines = [f"# UX Review: {params.feature}\n"]

        if params.user_context:
            lines.append(f"**Target Users**: {params.user_context}\n")

        if params.current_approach:
            lines.append(f"**Current Approach**: {params.current_approach}\n")

        lines.append("\n## UX Best Practices\n")

        for i, p in enumerate(passages[:6], 1):
            lines.append(f"### Principle {i} ({p['source']['book']})")
            lines.append(f"\n{p['content']}\n")

        lines.append("\n## Key UX Heuristics to Apply\n")
        lines.append("1. **Visibility of system status** - Keep users informed")
        lines.append("2. **Match with the real world** - Use familiar language")
        lines.append("3. **User control and freedom** - Provide undo/escape")
        lines.append("4. **Consistency** - Follow established patterns")
        lines.append("5. **Error prevention** - Design to prevent mistakes")
        lines.append("6. **Recognition over recall** - Minimize memory load")
        lines.append("7. **Flexibility** - Support both novice and expert users")
        lines.append("8. **Aesthetic and minimal** - Remove unnecessary elements\n")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Error in web_design_ux_review: {e}")
        return f"Error getting UX review: {str(e)}"


if __name__ == "__main__":
    mcp.run()
