"""Test suite for Parent-Document hierarchical chunking and document ingestion."""

from app.schemas.chat import DocumentChunk
from app.retrieval.parent_document import ParentDocumentRetriever, ParentDocumentStore


def test_hierarchical_chunking_and_parent_resolution():
    """Verify that child chunks map back to their full parent documents."""
    store = ParentDocumentStore()
    retriever = ParentDocumentRetriever(
        parent_chunk_size=500,
        parent_chunk_overlap=50,
        child_chunk_size=100,
        child_chunk_overlap=20,
        doc_store=store,
    )

    sample_doc = {
        "text": (
            "Parent Document Retrieval in RAG architectures solves the context dilemma. "
            "Instead of embedding large blocks that dilute semantic precision, or small blocks "
            "that lack surrounding context, we index small child segments for search and resolve "
            "the larger parent node for LLM synthesis. This ensures both high precision retrieval "
            "and comprehensive context grounding."
        ),
        "metadata": {"source": "rag_architecture_manual.pdf"},
    }

    parents, children = retriever.process_and_index_documents([sample_doc])

    assert len(parents) >= 1
    assert len(children) > len(parents)
    assert store.count() == len(parents)

    # Verify each child has parent_id mapped to store
    for child in children:
        parent_id = child.parent_id
        assert parent_id is not None
        parent_in_store = store.get(parent_id)
        assert parent_in_store is not None
        assert child.text in parent_in_store.text

    # Resolve parent from first two child hits
    resolved = retriever.resolve_parents(children[:2])
    assert len(resolved) == 1
    assert resolved[0].id == parents[0].id
