from pypdf import PdfReader

from app.database import supabase
from app.services.embeddings import create_embedding

import re


def split_text(text, chunk_size=150, overlap=30):
    # Detect headings such as:
    # 6.1 ELISA
    # 6.2 Immunofluorescence
    # 6.3 Western Blot
    # 6.4 Agglutination Tests
    heading_pattern = r'(?=\d+\.\d+\s+[A-Za-z])'

    sections = re.split(heading_pattern, text)

    chunks = []

    for section in sections:
        section = section.strip()

        if not section:
            continue

        words = section.split()

        start = 0

        while start < len(words):
            end = start + chunk_size

            chunk = " ".join(words[start:end]).strip()

            if chunk:
                chunks.append(chunk)

            start += chunk_size - overlap

    return chunks


def process_pdf(file_path: str, filename: str):
    reader = PdfReader(file_path)

    document = supabase.table("documents").insert({
        "filename": filename
    }).execute()

    document_id = document.data[0]["id"]

    chunk_index = 0

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if not text:
            continue
        
        is_reference = page_number == len(reader.pages)


        chunks = split_text(text)

        for chunk in chunks:

            embedding = create_embedding(chunk)

            supabase.table("document_chunks").insert({
                "document_id": document_id,
                "content": chunk,
                "embedding": embedding,
                "page_number": page_number,
                "chunk_index": chunk_index,
                "is_reference": is_reference

            }).execute()

            chunk_index += 1

    return document_id