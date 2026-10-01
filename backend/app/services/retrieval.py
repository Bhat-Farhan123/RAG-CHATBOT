
from app.database import supabase
from app.services.embeddings import create_embedding


def retrieve_chunks(
    query: str,
    match_count: int = 5,
    document_id: str | None = None
):
    query_embedding = create_embedding(query)

    candidate_count = 10

    result = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": candidate_count,
            "filter_document_id": document_id
        }
    ).execute()

    chunks = result.data or []

    print("\n========== RETRIEVAL DEBUG ==========")
    print("QUERY:", query)
    print("DOCUMENT ID:", document_id)
    print("RETRIEVED CHUNKS:", len(chunks))

    chunks = [
        chunk for chunk in chunks
        if chunk.get("similarity", 0) >= 0.05
    ]

    print("CHUNKS AFTER FILTER:", len(chunks))

    # Return chunks without reranking.
    ranked_chunks = chunks[:match_count]

    print("\n========== END RETRIEVAL ==========\n")

    return ranked_chunks