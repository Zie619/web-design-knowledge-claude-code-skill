#!/usr/bin/env python3
"""
Smart Chunking Module for Web Design RAG

Handles intelligent text chunking with topic-aware segmentation,
metadata enrichment, and structure preservation.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from pathlib import Path
import yaml

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class ChunkMetadata:
    """Metadata associated with each text chunk."""
    book_id: str
    book_title: str
    author: str
    year: int
    chapter: str = ""
    section: str = ""
    page_start: int = 0
    page_end: int = 0
    primary_topic: str = ""
    secondary_topics: List[str] = field(default_factory=list)
    content_type: str = "prose"  # prose, code, example
    has_code: bool = False
    tags: List[str] = field(default_factory=list)

    def to_chromadb_metadata(self) -> Dict:
        """Convert to ChromaDB-compatible metadata dict."""
        return {
            "book_id": self.book_id,
            "book_title": self.book_title,
            "author": self.author,
            "year": self.year,
            "chapter": self.chapter,
            "section": self.section,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "primary_topic": self.primary_topic,
            "secondary_topics": ",".join(self.secondary_topics),
            "content_type": self.content_type,
            "has_code": self.has_code,
            "tags": ",".join(self.tags),
        }


@dataclass
class TextChunk:
    """A processed text chunk ready for indexing."""
    content: str
    metadata: ChunkMetadata
    chunk_id: str = ""

    def __post_init__(self):
        if not self.chunk_id:
            import hashlib
            content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]
            self.chunk_id = f"{self.metadata.book_id}_{content_hash}"


class TopicClassifier:
    """Classifies text chunks into design topics based on keyword matching."""

    def __init__(self, taxonomy_path: Path):
        """Load topic taxonomy from YAML config."""
        with open(taxonomy_path, 'r') as f:
            config = yaml.safe_load(f)

        self.topics = config.get('topics', {})
        self.settings = config.get('classification', {})
        self.min_matches = self.settings.get('min_keyword_matches', 2)
        self.max_topics = self.settings.get('max_topics_per_chunk', 3)

        # Build keyword lookup
        self._build_keyword_index()

    def _build_keyword_index(self):
        """Build efficient keyword lookup structures."""
        self.keyword_to_topic = {}
        for topic_id, topic_data in self.topics.items():
            for keyword in topic_data.get('keywords', []):
                keyword_lower = keyword.lower()
                if keyword_lower not in self.keyword_to_topic:
                    self.keyword_to_topic[keyword_lower] = []
                self.keyword_to_topic[keyword_lower].append(topic_id)

    def classify(self, text: str) -> tuple[str, List[str]]:
        """
        Classify text into primary and secondary topics.

        Returns:
            Tuple of (primary_topic, secondary_topics)
        """
        text_lower = text.lower()
        topic_scores = {}

        # Score each topic based on keyword matches
        for keyword, topic_ids in self.keyword_to_topic.items():
            # Count occurrences (case-insensitive)
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text_lower))
            if count > 0:
                for topic_id in topic_ids:
                    if topic_id not in topic_scores:
                        topic_scores[topic_id] = 0
                    topic_scores[topic_id] += count

        if not topic_scores:
            return "", []

        # Sort by score
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        # Filter by minimum matches
        valid_topics = [(t, s) for t, s in sorted_topics if s >= self.min_matches]

        if not valid_topics:
            # Fall back to top topic even if below threshold
            valid_topics = sorted_topics[:1]

        primary = valid_topics[0][0] if valid_topics else ""
        secondary = [t for t, s in valid_topics[1:self.max_topics]]

        return primary, secondary


class SmartChunker:
    """
    Intelligent text chunking with context preservation.

    Features:
    - Respects paragraph and section boundaries
    - Keeps code blocks with explanatory text
    - Preserves lists and numbered items
    - Adds overlap for context continuity
    """

    # Separators in order of preference (try to split on major breaks first)
    SEPARATORS = [
        "\n\n\n",      # Major section breaks
        "\n\n",        # Paragraph breaks
        "\n",          # Line breaks
        ". ",          # Sentence boundaries
        ", ",          # Clause boundaries
        " ",           # Word boundaries
    ]

    # Patterns for detecting content types
    CODE_PATTERNS = [
        r'```[\s\S]*?```',  # Markdown code blocks
        r'<code>[\s\S]*?</code>',  # HTML code tags
        r'^\s{4,}\S',  # Indented code (4+ spaces)
        r'function\s*\(',  # JavaScript functions
        r'def\s+\w+\(',  # Python functions
        r'class\s+\w+',  # Class definitions
        r'\{\s*\n',  # Opening braces
        r';\s*$',  # Semicolon endings
    ]

    def __init__(
        self,
        target_size: int = 1200,
        max_size: int = 2000,
        min_size: int = 300,
        overlap: int = 200
    ):
        self.target_size = target_size
        self.max_size = max_size
        self.min_size = min_size
        self.overlap = overlap

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=target_size,
            chunk_overlap=overlap,
            separators=self.SEPARATORS,
            length_function=len,
            add_start_index=True,
        )

    def chunk_document(
        self,
        text: str,
        base_metadata: ChunkMetadata,
        page_breaks: Optional[Dict[int, int]] = None
    ) -> List[TextChunk]:
        """
        Chunk a document into smart segments.

        Args:
            text: Full document text
            base_metadata: Base metadata to copy for each chunk
            page_breaks: Optional mapping of character positions to page numbers

        Returns:
            List of TextChunk objects with enriched metadata
        """
        if not text.strip():
            return []

        # Use LangChain splitter for base chunking
        docs = self.text_splitter.create_documents([text])

        chunks = []
        for i, doc in enumerate(docs):
            content = doc.page_content
            start_index = doc.metadata.get('start_index', 0)

            # Skip chunks that are too small
            if len(content.strip()) < self.min_size:
                continue

            # Create chunk metadata
            chunk_meta = ChunkMetadata(
                book_id=base_metadata.book_id,
                book_title=base_metadata.book_title,
                author=base_metadata.author,
                year=base_metadata.year,
                chapter=self._extract_chapter(content, text, start_index),
                section=self._extract_section(content),
                content_type=self._detect_content_type(content),
                has_code=self._has_code(content),
                tags=list(base_metadata.tags),
            )

            # Add page range if available
            if page_breaks:
                chunk_meta.page_start, chunk_meta.page_end = self._get_page_range(
                    start_index, start_index + len(content), page_breaks
                )

            chunks.append(TextChunk(content=content, metadata=chunk_meta))

        return chunks

    def _extract_chapter(self, chunk: str, full_text: str, start_index: int) -> str:
        """Extract chapter/section heading that applies to this chunk."""
        # Look backwards in text for chapter headings
        search_text = full_text[max(0, start_index - 2000):start_index]

        # Common chapter patterns
        patterns = [
            r'Chapter\s+(\d+)[:\s]+([^\n]+)',
            r'CHAPTER\s+(\d+)[:\s]+([^\n]+)',
            r'^#+\s+(.+)$',  # Markdown headers
            r'^(\d+\.)\s+([^\n]+)',  # Numbered sections
        ]

        for pattern in patterns:
            matches = list(re.finditer(pattern, search_text, re.MULTILINE))
            if matches:
                match = matches[-1]  # Get the last (most recent) match
                groups = match.groups()
                if len(groups) >= 2:
                    return f"{groups[0]} {groups[1]}".strip()
                elif groups:
                    return groups[0].strip()

        return ""

    def _extract_section(self, chunk: str) -> str:
        """Extract section heading from chunk if present."""
        lines = chunk.split('\n')[:5]  # Check first 5 lines

        for line in lines:
            line = line.strip()
            # Check for heading-like patterns
            if re.match(r'^#+\s+', line):  # Markdown
                return re.sub(r'^#+\s+', '', line)
            if re.match(r'^[A-Z][^.!?]*$', line) and len(line) < 100:
                return line
            if re.match(r'^\d+\.\d+', line):  # Numbered section
                return line

        return ""

    def _detect_content_type(self, chunk: str) -> str:
        """Detect the primary content type of the chunk."""
        code_ratio = self._calculate_code_ratio(chunk)

        if code_ratio > 0.5:
            return "code"
        elif code_ratio > 0.2:
            return "example"
        else:
            return "prose"

    def _has_code(self, chunk: str) -> bool:
        """Check if chunk contains code examples."""
        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, chunk, re.MULTILINE):
                return True
        return False

    def _calculate_code_ratio(self, chunk: str) -> float:
        """Calculate the ratio of code-like content in the chunk."""
        if not chunk:
            return 0.0

        code_chars = 0
        total_chars = len(chunk)

        # Count characters in code-like patterns
        for pattern in self.CODE_PATTERNS[:3]:  # Use main patterns
            for match in re.finditer(pattern, chunk):
                code_chars += len(match.group())

        return code_chars / total_chars if total_chars > 0 else 0.0

    def _get_page_range(
        self,
        start_pos: int,
        end_pos: int,
        page_breaks: Dict[int, int]
    ) -> tuple[int, int]:
        """Determine page range for a chunk given page break positions."""
        if not page_breaks:
            return 0, 0

        sorted_positions = sorted(page_breaks.keys())

        start_page = 1
        end_page = 1

        for pos in sorted_positions:
            if pos <= start_pos:
                start_page = page_breaks[pos]
            if pos <= end_pos:
                end_page = page_breaks[pos]

        return start_page, end_page


def process_book_text(
    text: str,
    book_metadata: Dict,
    taxonomy_path: Path,
    page_breaks: Optional[Dict[int, int]] = None
) -> List[TextChunk]:
    """
    Process a book's text into classified chunks.

    Args:
        text: Full book text
        book_metadata: Book metadata from config
        taxonomy_path: Path to topic taxonomy YAML
        page_breaks: Optional page break positions

    Returns:
        List of classified TextChunk objects
    """
    # Create base metadata
    base_meta = ChunkMetadata(
        book_id=book_metadata['id'],
        book_title=book_metadata['title'],
        author=book_metadata['author'],
        year=book_metadata['year'],
        tags=book_metadata.get('tags', []),
    )

    # Initialize chunker and classifier
    chunker = SmartChunker()
    classifier = TopicClassifier(taxonomy_path)

    # Chunk the document
    chunks = chunker.chunk_document(text, base_meta, page_breaks)

    # Classify each chunk
    for chunk in chunks:
        primary, secondary = classifier.classify(chunk.content)
        chunk.metadata.primary_topic = primary
        chunk.metadata.secondary_topics = secondary

        # If no topic found, use book's primary topics
        if not primary and book_metadata.get('primary_topics'):
            chunk.metadata.primary_topic = book_metadata['primary_topics'][0]

    return chunks


if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    Chapter 1: Understanding Color Theory

    Color is one of the most important elements in web design. It affects
    user perception, brand recognition, and overall usability.

    The color wheel is a fundamental tool for understanding color relationships.
    Primary colors (red, yellow, blue) form the basis of all other colors.

    ## Complementary Colors

    Complementary colors sit opposite each other on the color wheel.
    Using complementary colors creates high contrast and visual interest.

    For example, blue and orange are complementary colors that work well
    together in web design when used thoughtfully.

    ```css
    .primary-button {
        background-color: #0066CC;
        color: white;
    }

    .accent {
        color: #FF6600;
    }
    ```

    This code shows how to implement a complementary color scheme in CSS.
    """

    # Would need taxonomy file to run this test
    print("Chunk processor module loaded successfully")
