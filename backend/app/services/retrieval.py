
from app.database import supabase
from app.services.embeddings import create_embedding
from app.services.reranker import rerank_chunks


def retrieve_chunks(
    query: str,
    match_count: int = 5,
    document_id: str | None = None
):
    query_embedding = create_embedding(query)

    # Retrieve more candidates than the final result count.
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

    # Keep the existing threshold for now.
    chunks = [
        chunk for chunk in chunks
        if chunk.get("similarity", 0) >= 0.05
    ]

    print("CHUNKS AFTER FILTER:", len(chunks))

    # Inspect the entire content during debugging.
    for index, chunk in enumerate(chunks, start=1):
        print(f"\n--- CHUNK {index} ---")
        print("SIMILARITY:", chunk.get("similarity"))
        print("PAGE:", chunk.get("page_number"))
        print("CONTENT:")
        print(chunk.get("content", ""))
        print("--------------------")

    # Rerank the candidate chunks.
    ranked_chunks = rerank_chunks(
        query,
        chunks,
        top_k=match_count
    )

    print("\n--- FINAL RERANKED CHUNKS ---")

    for index, chunk in enumerate(ranked_chunks, start=1):
        print(f"\nRANK {index}")
        print("SIMILARITY:", chunk.get("similarity"))
        print("PAGE:", chunk.get("page_number"))
        print(chunk.get("content", ""))

    print("\n========== END DEBUG ==========\n")

    return ranked_chunks