"""Parent-Document Retriever implementation.

Maps small child chunks (e.g. 200 characters) to larger parent document nodes
(e.g. 1000 characters) stored in a local document repository.
When a child chunk matches during search, the full parent context is retrieved and returned.
"""

import uuid
from typing import List, Dict, Optional, Tuple, Any
from app.schemas.chat import DocumentChunk
from app.core.config import get_settings


class ParentDocumentStore:
    """In-memory key-value store for parent document nodes."""

    def __init__(self) -> None:
        self._store: Dict[str, DocumentChunk] = {}

    def put(self, parent_id: str, document: DocumentChunk) -> None:
        """Store a parent document by its unique parent_id."""
        self._store[parent_id] = document

    def get(self, parent_id: str) -> Optional[DocumentChunk]:
        """Retrieve a parent document by its unique parent_id."""
        return self._store.get(parent_id)

    def multi_get(self, parent_ids: List[str]) -> List[DocumentChunk]:
        """Retrieve multiple parent documents by their IDs."""
        results = []
        for pid in parent_ids:
            doc = self.get(pid)
            if doc:
                results.append(doc)
        return results

    def clear(self) -> None:
        """Clear all stored parent documents."""
        self._store.clear()

    def count(self) -> int:
        """Return the count of parent documents."""
        return len(self._store)


class ParentDocumentRetriever:
    """Manages hierarchical chunking and maps child matches back to parent context."""

    def __init__(
        self,
        parent_chunk_size: Optional[int] = None,
        parent_chunk_overlap: Optional[int] = None,
        child_chunk_size: Optional[int] = None,
        child_chunk_overlap: Optional[int] = None,
        doc_store: Optional[ParentDocumentStore] = None,
    ) -> None:
        settings = get_settings()
        self.parent_chunk_size = parent_chunk_size or settings.PARENT_CHUNK_SIZE
        self.parent_chunk_overlap = parent_chunk_overlap or settings.PARENT_CHUNK_OVERLAP
        self.child_chunk_size = child_chunk_size or settings.CHILD_CHUNK_SIZE
        self.child_chunk_overlap = child_chunk_overlap or settings.CHILD_CHUNK_OVERLAP
        self.doc_store = doc_store or ParentDocumentStore()

    def split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split text into chunks of specified size and overlap based on character boundaries."""
        if not text or chunk_size <= 0:
            return []
        if chunk_overlap >= chunk_size:
            chunk_overlap = max(chunk_size // 4, 0)
        chunks = []
        start = 0
        text_len = len(text)
        step = max(chunk_size - chunk_overlap, 1)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            start += step
        return chunks

    def process_and_index_documents(
        self, raw_documents: List[Dict[str, Any]]
    ) -> Tuple[List[DocumentChunk], List[DocumentChunk]]:
        """Splits raw documents into parent nodes and child chunks, returning both.

        Each parent chunk is indexed in the doc_store.
        Each child chunk is annotated with its parent_id for retrieval mapping.
        """
        all_parents: List[DocumentChunk] = []
        all_children: List[DocumentChunk] = []

        for doc in raw_documents:
            text = doc.get("text", "")
            base_metadata = doc.get("metadata", {})

            # 1. Segment raw text into larger parent nodes (e.g. 1000 chars)
            parent_texts = self.split_text(
                text, self.parent_chunk_size, self.parent_chunk_overlap
            )
            if not parent_texts and text.strip():
                parent_texts = [text.strip()]

            for p_idx, p_text in enumerate(parent_texts):
                parent_id = str(uuid.uuid4())
                parent_metadata = {
                    **base_metadata,
                    "parent_index": p_idx,
                    "type": "parent",
                }
                parent_doc = DocumentChunk(
                    id=parent_id,
                    text=p_text,
                    parent_id=None,
                    metadata=parent_metadata,
                )
                self.doc_store.put(parent_id, parent_doc)
                all_parents.append(parent_doc)

                # 2. Segment each parent into smaller child chunks (e.g. 200 chars)
                child_texts = self.split_text(
                    p_text, self.child_chunk_size, self.child_chunk_overlap
                )
                if not child_texts and p_text.strip():
                    child_texts = [p_text.strip()]

                for c_idx, c_text in enumerate(child_texts):
                    child_id = str(uuid.uuid4())
                    child_metadata = {
                        **parent_metadata,
                        "child_index": c_idx,
                        "parent_id": parent_id,
                        "type": "child",
                    }
                    child_doc = DocumentChunk(
                        id=child_id,
                        text=c_text,
                        parent_id=parent_id,
                        metadata=child_metadata,
                    )
                    all_children.append(child_doc)

        return all_parents, all_children

    def resolve_parents(
        self, matched_children: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """Given a list of matched child chunks, resolve and return the unique parent documents

        maintaining the relevance order of the first child appearance.
        """
        seen_parent_ids = set()
        resolved_parents: List[DocumentChunk] = []

        for child in matched_children:
            parent_id = child.parent_id or (
                child.metadata.get("parent_id") if child.metadata else None
            )
            if not parent_id:
                # If chunk has no parent_id, treat it as its own document
                if child.id not in seen_parent_ids:
                    seen_parent_ids.add(child.id)
                    resolved_parents.append(child)
                continue

            if parent_id not in seen_parent_ids:
                seen_parent_ids.add(parent_id)
                parent_doc = self.doc_store.get(parent_id)
                if parent_doc:
                    # Propagate score from matched child if present
                    parent_copy = DocumentChunk(
                        id=parent_doc.id,
                        text=parent_doc.text,
                        parent_id=None,
                        metadata=parent_doc.metadata,
                        score=child.score,
                    )
                    resolved_parents.append(parent_copy)

        return resolved_parents
