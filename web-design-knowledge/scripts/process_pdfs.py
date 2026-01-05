#!/usr/bin/env python3
"""
PDF Processing Pipeline for Web Design RAG

Extracts text from PDF books, chunks intelligently, classifies by topic,
and indexes into ChromaDB for retrieval.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime

import yaml
import fitz  # PyMuPDF
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from chunk_processor import (
    SmartChunker,
    TopicClassifier,
    ChunkMetadata,
    TextChunk,
    process_book_text
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Track processing statistics."""
    books_processed: int = 0
    books_failed: int = 0
    total_pages: int = 0
    total_chunks: int = 0
    total_characters: int = 0
    topics_distribution: Dict[str, int] = None

    def __post_init__(self):
        if self.topics_distribution is None:
            self.topics_distribution = {}


class PDFExtractor:
    """Extract text and structure from PDF files."""

    def __init__(self):
        self.monospace_fonts = {
            'courier', 'consolas', 'monaco', 'menlo',
            'inconsolata', 'source code', 'fira code',
            'roboto mono', 'ubuntu mono'
        }

    def extract(self, pdf_path: Path) -> Tuple[str, Dict[int, int]]:
        """
        Extract text from PDF with page break tracking.

        Returns:
            Tuple of (full_text, page_breaks_dict)
            where page_breaks_dict maps character positions to page numbers
        """
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"Failed to open PDF {pdf_path}: {e}")
            return "", {}

        full_text = []
        page_breaks = {}
        current_pos = 0

        for page_num, page in enumerate(doc, start=1):
            # Track page break position
            page_breaks[current_pos] = page_num

            # Extract text from page
            text = page.get_text("text")

            # Clean and normalize text
            text = self._clean_text(text)

            full_text.append(text)
            current_pos += len(text) + 1  # +1 for page separator

        doc.close()

        # Join all pages with separator
        combined_text = "\n\n".join(full_text)

        return combined_text, page_breaks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove lines that are just page numbers or headers
            stripped = line.strip()
            if stripped.isdigit() and len(stripped) < 4:
                continue
            # Remove excessive spaces within lines
            cleaned = ' '.join(line.split())
            cleaned_lines.append(cleaned)

        # Remove excessive blank lines
        result = []
        prev_blank = False
        for line in cleaned_lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            result.append(line)
            prev_blank = is_blank

        return '\n'.join(result)


class ChromaDBIndexer:
    """Index chunks into ChromaDB with embeddings."""

    COLLECTION_NAME = "web_design_knowledge"

    def __init__(self, persist_path: Path, embedding_model: str = "all-MiniLM-L6-v2"):
        """Initialize ChromaDB client and embedding model."""
        self.persist_path = persist_path
        persist_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at {persist_path}")

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Load embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "description": "Web design knowledge from curated design books",
                "hnsw:space": "cosine",
                "created_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"Collection '{self.COLLECTION_NAME}' ready with {self.collection.count()} existing documents")

    def add_chunks(self, chunks: List[TextChunk], batch_size: int = 100):
        """Add chunks to the collection in batches."""
        if not chunks:
            return

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Prepare batch data
            ids = [chunk.chunk_id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.metadata.to_chromadb_metadata() for chunk in batch]

            # Generate embeddings
            embeddings = self.embedding_model.encode(
                documents,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()

            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

    def get_stats(self) -> Dict:
        """Get collection statistics."""
        count = self.collection.count()

        # Sample some documents to get topic distribution
        if count > 0:
            sample_size = min(1000, count)
            results = self.collection.get(
                limit=sample_size,
                include=["metadatas"]
            )

            topics = {}
            for meta in results['metadatas']:
                topic = meta.get('primary_topic', 'unknown')
                topics[topic] = topics.get(topic, 0) + 1

            return {
                "total_documents": count,
                "sample_topic_distribution": topics
            }

        return {"total_documents": 0}


class WebDesignRAGProcessor:
    """Main processor for building the web design RAG system."""

    def __init__(
        self,
        pdf_dir: Path,
        config_dir: Path,
        data_dir: Path
    ):
        self.pdf_dir = pdf_dir
        self.config_dir = config_dir
        self.data_dir = data_dir

        # Load configurations
        self.books_config = self._load_config("books_metadata.yaml")
        self.taxonomy_path = config_dir / "topic_taxonomy.yaml"

        # Initialize components
        self.extractor = PDFExtractor()
        self.indexer = ChromaDBIndexer(data_dir / "chromadb")

        # Build book lookup
        self.books_by_filename = {
            book['filename']: book
            for book in self.books_config.get('books', [])
        }
        self.duplicates = set(self.books_config.get('duplicates', []))

    def _load_config(self, filename: str) -> Dict:
        """Load YAML configuration file."""
        config_path = self.config_dir / filename
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def process_all(self) -> ProcessingStats:
        """Process all PDF books in the directory."""
        stats = ProcessingStats()

        # Find all PDFs
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")

        # Filter out duplicates
        pdf_files = [
            f for f in pdf_files
            if f.name not in self.duplicates
        ]
        logger.info(f"Processing {len(pdf_files)} unique PDFs (excluding duplicates)")

        # Process each PDF
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                chunks = self.process_single(pdf_path)
                stats.books_processed += 1
                stats.total_chunks += len(chunks)
                stats.total_characters += sum(len(c.content) for c in chunks)

                # Update topic distribution
                for chunk in chunks:
                    topic = chunk.metadata.primary_topic or "unclassified"
                    stats.topics_distribution[topic] = \
                        stats.topics_distribution.get(topic, 0) + 1

            except Exception as e:
                logger.error(f"Failed to process {pdf_path.name}: {e}")
                stats.books_failed += 1

        # Log final stats
        logger.info(f"\n{'='*50}")
        logger.info("Processing Complete!")
        logger.info(f"Books processed: {stats.books_processed}")
        logger.info(f"Books failed: {stats.books_failed}")
        logger.info(f"Total chunks: {stats.total_chunks}")
        logger.info(f"Total characters: {stats.total_characters:,}")
        logger.info(f"\nTopic distribution:")
        for topic, count in sorted(stats.topics_distribution.items(), key=lambda x: -x[1]):
            logger.info(f"  {topic}: {count}")

        # Get indexer stats
        indexer_stats = self.indexer.get_stats()
        logger.info(f"\nChromaDB collection: {indexer_stats['total_documents']} documents")

        return stats

    def process_single(self, pdf_path: Path) -> List[TextChunk]:
        """Process a single PDF file."""
        filename = pdf_path.name

        # Get book metadata
        book_meta = self.books_by_filename.get(filename)
        if not book_meta:
            logger.warning(f"No metadata found for {filename}, using defaults")
            book_meta = {
                'id': Path(filename).stem[:50],
                'title': filename,
                'author': 'Unknown',
                'year': 2020,
                'primary_topics': [],
                'tags': []
            }

        logger.info(f"Processing: {book_meta['title']}")

        # Extract text
        text, page_breaks = self.extractor.extract(pdf_path)
        if not text:
            logger.warning(f"No text extracted from {filename}")
            return []

        # Process into chunks
        chunks = process_book_text(
            text=text,
            book_metadata=book_meta,
            taxonomy_path=self.taxonomy_path,
            page_breaks=page_breaks
        )

        logger.info(f"  Generated {len(chunks)} chunks from {len(page_breaks)} pages")

        # Index chunks
        self.indexer.add_chunks(chunks)

        return chunks


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process web design PDF books into RAG index"
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=Path("/home/elios/redditkarmagame"),
        help="Directory containing PDF files"
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path(__file__).parent.parent / "config",
        help="Directory containing configuration files"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent.parent / "data",
        help="Directory for output data (ChromaDB)"
    )
    parser.add_argument(
        "--single",
        type=str,
        help="Process only a single PDF file (filename)"
    )

    args = parser.parse_args()

    # Validate paths
    if not args.pdf_dir.exists():
        logger.error(f"PDF directory not found: {args.pdf_dir}")
        sys.exit(1)

    if not args.config_dir.exists():
        logger.error(f"Config directory not found: {args.config_dir}")
        sys.exit(1)

    # Create processor
    processor = WebDesignRAGProcessor(
        pdf_dir=args.pdf_dir,
        config_dir=args.config_dir,
        data_dir=args.data_dir
    )

    # Process
    if args.single:
        pdf_path = args.pdf_dir / args.single
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            sys.exit(1)
        chunks = processor.process_single(pdf_path)
        logger.info(f"Processed {len(chunks)} chunks")
    else:
        stats = processor.process_all()

    logger.info("Done!")


if __name__ == "__main__":
    main()
