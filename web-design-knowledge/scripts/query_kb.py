#!/usr/bin/env python3
"""
CLI tool for querying the Web Design Knowledge Base.

Usage:
    python query_kb.py --query "How do I create visual hierarchy?"
    python query_kb.py --query "color palette for fintech" --type color --mood trustworthy
    python query_kb.py --query "dashboard" --type layout --page-type dashboard
    python query_kb.py --query "checkout flow" --type ux
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Constants
DEFAULT_RESULTS = 3  # Reduced from 5 to keep context lean
MAX_RESULTS = 10
CHARACTER_LIMIT = 8000  # Reduced from 25000 to keep context lean

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CHROMADB_PATH = os.environ.get(
    "CHROMADB_PATH",
    str(PROJECT_DIR / "data" / "chromadb")
)
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Global instances (lazy loaded)
_collection = None
_embedding_model = None


def get_collection():
    """Get or create the ChromaDB collection."""
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(
            path=CHROMADB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = client.get_collection("web_design_knowledge")
    return _collection


def get_embedding_model():
    """Get or create the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def query_knowledge_base(
    query: str,
    n_results: int = DEFAULT_RESULTS,
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
                },
                "topic": meta.get("primary_topic", ""),
                "relevance": round(1 - distance, 2) if distance else 0,
            })

    return passages


def format_markdown(passages: List[Dict], query: str, query_type: str = "general") -> str:
    """Format passages as concise markdown."""
    if not passages:
        return f"No results found for: '{query}'"

    lines = [f"## {query_type.title()} Guidance\n"]

    for i, p in enumerate(passages, 1):
        # Truncate content to keep response lean
        content = p['content']
        if len(content) > 600:
            content = content[:600] + "..."

        lines.append(f"**{i}. {p['source']['book']}** ({p['topic'].replace('_', ' ')})")
        lines.append(f"> {content}\n")

    return "\n".join(lines)


def format_json(passages: List[Dict], query: str) -> str:
    """Format passages as JSON."""
    return json.dumps({
        "query": query,
        "count": len(passages),
        "passages": passages
    }, indent=2)


def query_general(args) -> str:
    """Handle general design queries."""
    topic_filter = args.topics.split(",") if args.topics else None
    passages = query_knowledge_base(
        query=args.query,
        n_results=args.n_results,
        topic_filter=topic_filter
    )

    if args.format == "json":
        return format_json(passages, args.query)
    return format_markdown(passages, args.query, "Design")


def query_color(args) -> str:
    """Handle color-specific queries."""
    query_parts = [f"color palette for {args.query}"]

    if args.mood:
        query_parts.append(f"{args.mood} color scheme")

    full_query = " ".join(query_parts)

    passages = query_knowledge_base(
        query=full_query,
        n_results=args.n_results,
        topic_filter=["color_theory", "visual_hierarchy"]
    )

    result = format_markdown(passages, args.query, "Color")

    # Add accessibility reminder
    if args.accessibility:
        result += "\n**Accessibility**: 4.5:1 contrast for text, 3:1 for UI. Don't rely on color alone.\n"

    return result


def query_layout(args) -> str:
    """Handle layout-specific queries."""
    query_parts = [f"layout design for {args.query}"]

    if args.page_type:
        query_parts.append(f"{args.page_type.replace('_', ' ')} page")
    if args.density:
        query_parts.append(f"{args.density} content density")

    full_query = " ".join(query_parts)

    passages = query_knowledge_base(
        query=full_query,
        n_results=args.n_results,
        topic_filter=["layout", "responsive", "visual_hierarchy"]
    )

    return format_markdown(passages, args.query, "Layout")


def query_ux(args) -> str:
    """Handle UX-specific queries."""
    query_parts = [f"UX best practices for {args.query}"]

    if args.user_context:
        query_parts.append(f"for {args.user_context}")

    full_query = " ".join(query_parts)

    passages = query_knowledge_base(
        query=full_query,
        n_results=args.n_results,
        topic_filter=["ux_principles", "ui_patterns", "forms_inputs", "navigation"]
    )

    return format_markdown(passages, args.query, "UX")


def main():
    parser = argparse.ArgumentParser(
        description="Query the Web Design Knowledge Base",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="Design question or topic to search"
    )

    # Query type
    parser.add_argument(
        "--type", "-t",
        choices=["general", "color", "layout", "ux"],
        default="general",
        help="Query type (default: general)"
    )

    # General options
    parser.add_argument(
        "--n-results", "-n",
        type=int,
        default=DEFAULT_RESULTS,
        help=f"Number of results (default: {DEFAULT_RESULTS}, max: {MAX_RESULTS})"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--topics",
        help="Comma-separated topic filters (for general queries)"
    )

    # Color-specific
    parser.add_argument(
        "--mood",
        choices=["professional", "playful", "calm", "energetic", "luxurious",
                 "trustworthy", "modern", "minimalist", "bold", "warm"],
        help="Mood for color queries"
    )
    parser.add_argument(
        "--accessibility", "-a",
        action="store_true",
        default=True,
        help="Include accessibility guidance (default: true)"
    )

    # Layout-specific
    parser.add_argument(
        "--page-type",
        choices=["landing_page", "dashboard", "blog", "portfolio", "ecommerce",
                 "settings", "profile", "search_results", "form_page", "documentation"],
        help="Page type for layout queries"
    )
    parser.add_argument(
        "--density",
        choices=["low", "medium", "high"],
        help="Content density for layout queries"
    )

    # UX-specific
    parser.add_argument(
        "--user-context",
        help="Target user context for UX queries"
    )

    args = parser.parse_args()

    # Clamp n_results
    args.n_results = min(max(1, args.n_results), MAX_RESULTS)

    try:
        # Route to appropriate handler
        if args.type == "color":
            result = query_color(args)
        elif args.type == "layout":
            result = query_layout(args)
        elif args.type == "ux":
            result = query_ux(args)
        else:
            result = query_general(args)

        # Enforce character limit
        if len(result) > CHARACTER_LIMIT:
            result = result[:CHARACTER_LIMIT] + "\n\n[Truncated]"

        print(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
