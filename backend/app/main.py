import os
import shutil
import json

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import supabase
from app.services.retrieval import retrieve_chunks
from app.services.llm import (
    generate_answer,
    generate_answer_stream,
    rewrite_query,
    detect_intent,
    get_conversation_response
)
from app.services.ingestion import process_pdf

app = FastAPI(title="RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://farhannisar01-rag-chatbot-frontend.static.hf.space",
        "https://farhannisar01-rag-chatbot-frontend-41bfb80.static.hf.space",
     ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "RAG Chatbot API is running"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join("uploads", file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document_id = process_pdf(
        file_path,
        file.filename
    )

    return {
        "message": "Document processed successfully",
        "document_id": document_id
    }
    
    
@app.get("/documents")
def get_documents():
    result = (
        supabase
        .table("documents")
        .select("id, filename, created_at")
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []
    
from app.services.retrieval import retrieve_chunks

@app.get("/search")
def search(query: str):
    chunks = retrieve_chunks(query)

    return {
        "results": chunks
    }    
    
    
@app.get("/chat")
def chat(query: str):

    chunks = retrieve_chunks(query)

    context = "\n\n".join(
        chunk["content"]
        for chunk in chunks
    )

    answer = generate_answer(
        query,
        context
    )

    return {
        "question": query,
        "answer": answer,
        "sources": chunks
    }




@app.get("/chat/stream")
def chat_stream(
    query: str,
    history: str = "[]",
    document_id: str | None = None
):
    import json

    conversation_history = json.loads(history)

    # Detect user intent
    intent = detect_intent(query)

    print("Original query:", query)
    print("Detected intent:", intent)
    
    # Validate document selection for document-related questions
    if intent == "document" and not document_id:
     raise HTTPException(
        status_code=400,
        detail="Please select a document first."
    )

    # Handle normal conversation without RAG
    if intent != "document":
        response_text = get_conversation_response(intent)

        def generate_conversation():
            yield f"event: sources\ndata: {json.dumps([])}\n\n"

            for word in response_text.split(" "):
                yield f"event: token\ndata: {json.dumps(word + ' ')}\n\n"

            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(
            generate_conversation(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Rewrite document-related question
    rewritten_query = rewrite_query(
        query,
        conversation_history
    )

    print("Rewritten query:", rewritten_query)

    # Retrieve relevant chunks
    chunks = retrieve_chunks(
        rewritten_query,
        document_id=document_id
    )

    context = "\n\n".join(
        chunk["content"]
        for chunk in chunks
    )

    def generate():
        yield f"event: sources\ndata: {json.dumps(chunks)}\n\n"

        for token in generate_answer_stream(
            query,
            context,
            conversation_history
        ):
            yield f"event: token\ndata: {json.dumps(token)}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
    
    
    
@app.delete("/documents/{document_id}")
def delete_document(document_id: str):
    # Find the document first
    result = (
        supabase
        .table("documents")
        .select("id, filename")
        .eq("id", document_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    filename = result.data[0]["filename"]

    # Delete the document from Supabase
    supabase.table("documents").delete().eq(
        "id", document_id
    ).execute()

    # Delete the corresponding uploaded PDF
    safe_filename = os.path.basename(filename)
    file_path = os.path.join("uploads", safe_filename)

    if os.path.isfile(file_path):
        os.remove(file_path)

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }    