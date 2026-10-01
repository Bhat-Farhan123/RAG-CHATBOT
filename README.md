# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that allows users to upload documents and ask questions about their content.

## Features

* Upload PDF documents.
* Extract and process document text.
* Generate embeddings for document chunks.
* Store and retrieve embeddings using Supabase.
* Retrieve relevant document content for user questions.
* Use a language model to generate answers grounded in retrieved content.
* Display source information alongside answers.
* Stream responses from the backend to the frontend.

## Tech Stack

### Frontend

* React
* Vite
* JavaScript

### Backend

* Python
* FastAPI
* Supabase
* Sentence Transformers
* Groq API
* PyPDF

> Update this section to match the exact models, libraries, and services used by your project.

## Project Structure

```text
rag-chatbot/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
│
├── .gitignore
└── README.md
```

Adjust the structure above to match your actual folders and filenames.

## Prerequisites

* Python 3
* Node.js and npm
* A Supabase project
* A Groq API key

## Getting Started

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd rag-chatbot
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
```

Activate the environment.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file by copying `.env.example` to `.env`, then add your own credentials.

### 3. Configure Supabase

Create or configure the Supabase tables and vector-search function required by the application.

The exact schema and SQL function must match the database queries used in the backend. Add the verified SQL setup instructions here.

### 4. Run the backend

```bash
uvicorn app.main:app --reload
```

This command assumes that `main.py` is in the current backend directory. Change it if your application uses a different module path.

### 5. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
```

Create the frontend environment file if your application requires one. Add the correct backend API URL.

Start the development server:

```bash
npm run dev
```

Open the local URL printed by Vite.

## API Endpoints

| Method | Endpoint                   | Purpose                            |
| ------ | -------------------------- | ---------------------------------- |
| GET    | `/`                        | Backend health or welcome response |
| POST   | `/upload`                  | Upload a document                  |
| GET    | `/documents`               | List uploaded documents            |
| POST   | `/search`                  | Search document content            |
| POST   | `/chat`                    | Ask a question                     |
| POST   | `/chat/stream`             | Stream a chat response             |
| DELETE | `/documents/{document_id}` | Delete a document                  |

Verify the request formats and response structures against the actual backend before treating this table as complete.

## Environment Variables

See `backend/.env.example` for the required variable names.

Never commit real API keys or credentials.

## Limitations

* Answers depend on the quality of document extraction and retrieval.
* Retrieved content may be incomplete or irrelevant.
* Model responses can contain errors.
* Performance depends on the selected embedding model, reranker, language model, and hosting resources.

## Future Improvements

* Improve section-aware document chunking.
* Add retrieval evaluation.
* Improve source attribution.
* Add authentication and access controls.
* Deploy the frontend and backend.

## License

Choose and add a license before distributing the project. If you are unsure, leave this section out until you decide.
