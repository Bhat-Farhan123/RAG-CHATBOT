import { useState, useEffect, useRef } from "react";
import {
  Upload,
  FileText,
  Send,
  CheckCircle,
  Bot,
  BookOpen,
  Loader2,
  Trash2,

} from "lucide-react";

import ReactMarkdown from "react-markdown";
import "./App.css";
const API_BASE_URL = "https://rag-chatbot-backend-8cuk.onrender.com";

function App() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [sources, setSources] = useState([]);
  const [messagesByDocument, setMessagesByDocument] = useState({});
  
  
  const chatScrollRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const messages = selectedDocument
  ? messagesByDocument[selectedDocument.id] || []
  : [];


 const fetchDocuments = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/documents`);

    if (!response.ok) {
      throw new Error("Failed to fetch documents");
    }

    const data = await response.json();

    setDocuments(data);

    if (data.length > 0 && !selectedDocument) {
      setSelectedDocument(data[0]);
    }
  } catch (error) {
    console.error("DOCUMENT FETCH ERROR:", error);
  }
};

useEffect(() => {
  fetchDocuments();
}, []);

const deleteDocument = async (document) => {
  const confirmed = window.confirm(
    `Are you sure you want to delete "${document.filename}"?`
  );

  if (!confirmed) return;

  try {
   const response = await fetch(
      `${API_BASE_URL}/documents/${document.id}`,
      { method: "DELETE" }
     );

    if (!response.ok) {
      throw new Error("Failed to delete document");
    }

    const remaining = documents.filter(
      (doc) => doc.id !== document.id
    );

    setDocuments(remaining);

    if (selectedDocument?.id === document.id) {
      setSelectedDocument(remaining[0] || null);
      setAnswer("");
      setSources([]);
      setQuestion("");
    }

    setMessagesByDocument((prev) => {
      const updated = { ...prev };
      delete updated[document.id];
      return updated;
    });

    setMessage("Document deleted successfully.");
  } catch (error) {
    console.error("DELETE ERROR:", error);
    setMessage("Could not delete the document.");
  }
};
  


 useEffect(() => {
  if (chatScrollRef.current) {
    chatScrollRef.current.scrollTo({
      top: chatScrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }
}, [messages, answer, loading]);

 const uploadFile = async () => {
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(
       `${API_BASE_URL}/upload`,
         {
           method: "POST",
           body: formData,
         }
      );

    if (!response.ok) {
      throw new Error("Upload failed");
    }

    const data = await response.json();

setMessage(data.message);

// Refresh document list
await fetchDocuments();

// Clear selected file
setFile(null);

  } catch (error) {
    console.error("UPLOAD ERROR:", error);
    setMessage("Upload failed.");
  }
};

const askQuestion = async () => {
  const currentQuestion = question.trim();

  if (!currentQuestion) return;
    if (!selectedDocument) {
    setMessage("Please select a document first.");
    return;
  }

  const documentId = selectedDocument.id;

  setQuestion("");
 // Save user question to conversation history
setMessagesByDocument((prev) => ({
  ...prev,
  [documentId]: [
    ...(prev[documentId] || []),
    {
      role: "user",
      content: currentQuestion,
    },
  ],
}));
  setLoading(true);
  setAnswer("");
  setSources([]);

  try {
    const response = await fetch(
  `${API_BASE_URL}/chat/stream?query=${encodeURIComponent(
    currentQuestion
  )}&history=${encodeURIComponent(
    JSON.stringify(messages)
  )}&document_id=${encodeURIComponent(documentId)}`
);
    if (!response.ok) {
      throw new Error("Failed to get response");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let accumulatedAnswer = "";

        while (true) {
      const { value, done } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, {
        stream: true,
      });

      const events = buffer.split("\n\n");

      buffer = events.pop();

      for (const event of events) {
        const lines = event.split("\n");

        let eventType = "";
        let data = "";

        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventType = line.slice(6).trim();
          }

          if (line.startsWith("data:")) {
            data += line.slice(5).trim();
          }
        }

        if (eventType === "sources") {
          const sources = JSON.parse(data);
          setSources(sources);
        }

        if (eventType === "token") {
          const token = JSON.parse(data);

          accumulatedAnswer += token;

          setAnswer(accumulatedAnswer);
        }

        if (eventType === "done") {
          console.log("Streaming complete");
        }
      }
    }

    // Save AI response to conversation history
  setMessagesByDocument((prev) => ({
  ...prev,
  [documentId]: [
    ...(prev[documentId] || []),
    {
      role: "assistant",
      content: accumulatedAnswer,
    },
  ],
}));

  } catch (error) {
    console.error("ERROR:", error);
    setAnswer("Something went wrong.");
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">
            <Bot size={24} />
          </div>

          <div>
            <h1>RAG Chatbot</h1>
            <p>Chat with your documents using AI</p>
          </div>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Online
        </div>
      </header>


      <main className="container">

     {/* DOCUMENT BAR */}

<section className="document-bar">
  <div className="document-info">
    <div className="document-icon">
      <FileText size={20} />
    </div>

    <div>
      <span className="document-label">
        Documents
      </span>

      <strong>
        {documents.length}{" "}
        {documents.length === 1 ? "document" : "documents"}
      </strong>
    </div>
  </div>

  <div className="document-actions">
    <label className="change-file-button">
      <Upload size={16} />
      Upload PDF

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => setFile(e.target.files[0])}
        hidden
      />
    </label>

    {file && (
      <button
        className="upload-button compact-upload"
        onClick={uploadFile}
      >
        <Upload size={16} />
        Upload
      </button>
    )}
  </div>
</section>
{documents.length > 0 && (
  <div className="document-list">
    {documents.map((document) => (
      <div
        key={document.id}
        className={`document-item ${
          selectedDocument?.id === document.id ? "active" : ""
        }`}
        onClick={() => setSelectedDocument(document)}
      >
        <div className="document-item-icon">
          <FileText size={16} />
        </div>

        <div className="document-item-info">
          <strong>{document.filename}</strong>
          <span>
            {new Date(document.created_at).toLocaleDateString()}
          </span>
        </div>

        {selectedDocument?.id === document.id && (
          <CheckCircle
            size={16}
            className="document-active-icon"
          />
        )}

        <button
          className="delete-document-button"
          title="Delete document"
          onClick={(e) => {
            e.stopPropagation();
            deleteDocument(document);
          }}
        >
          <Trash2 size={16} />
        </button>
      </div>
    ))}
  </div>
)}

{message && (
  <div className="success-message compact-success">
    <CheckCircle size={16} />
    {message}
  </div>
)}

       

 {/* CHAT AREA */}

<div
  className="chat-scroll"
  ref={chatScrollRef}
>
  {/* EMPTY CHAT / WELCOME */}

  {messages.length === 0 && (
    <section className="welcome">

      <div className="welcome-icon">
        <Bot size={28} />
      </div>

      <h2>
        Ask anything about
        <span> your document</span>
      </h2>

      <p>
        Upload a PDF and start exploring the information
        inside it with AI-powered search.
      </p>

      <div className="suggestions">

        <button
          onClick={() =>
            setQuestion("Summarize this document")
          }
        >
          <span className="suggestion-icon purple">
            ✨
          </span>

          Summarize this document
        </button>


        <button
          onClick={() =>
            setQuestion("What are the main findings?")
          }
        >
          <span className="suggestion-icon blue">
            🔍
          </span>

          What are the main findings?
        </button>


        <button
          onClick={() =>
            setQuestion(
              "Explain this document in simple terms"
            )
          }
        >
          <span className="suggestion-icon cyan">
            💡
          </span>

          Explain it simply
        </button>

      </div>

    </section>
  )}


  {/* CONVERSATION */}

  {messages.length > 0 && (
    <section className="chat-area">

      {messages.map((message, index) => (

        <div
          key={index}
          className={`message ${
            message.role === "user"
              ? "user-message"
              : "ai-message"
          }`}
        >

          <div
            className={`message-avatar ${
              message.role === "assistant"
                ? "ai-avatar"
                : ""
            }`}
          >
            {message.role === "assistant" ? (
              <Bot size={18} />
            ) : (
              "You"
            )}
          </div>


          <div className="message-content">

            <span className="message-label">
              {message.role === "user"
                ? "You"
                : "AI"}
            </span>


            <div
              className={
                message.role === "user"
                  ? "user-bubble"
                  : "ai-bubble"
              }
            >

              {message.role === "assistant" ? (
                <ReactMarkdown>
                  {message.content}
                </ReactMarkdown>
              ) : (
                message.content
              )}

            </div>

          </div>

        </div>

      ))}


      {/* LIVE AI RESPONSE */}

      {loading && (
        <div className="message ai-message">

          <div className="message-avatar ai-avatar">
            <Bot size={18} />
          </div>

          <div className="message-content">

            <span className="message-label">
              AI
            </span>

            <div className="ai-bubble">

              {answer ? (
                <ReactMarkdown>
                  {answer}
                </ReactMarkdown>
              ) : (
                <div className="typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              )}

            </div>

          </div>

        </div>
      )}

    </section>
  )}

</div>


{/* FIXED CHAT INPUT */}

<div className="chat-input-container">

  <div className="chat-input">

    <input
      type="text"
      placeholder="Ask anything about your document..."
      value={question}
      onChange={(e) =>
        setQuestion(e.target.value)
      }
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          askQuestion();
        }
      }}
    />

    <button
      onClick={askQuestion}
      disabled={loading || !question.trim()}
    >
      {loading ? (
        <Loader2
          size={18}
          className="spinner"
        />
      ) : (
        <Send size={18} />
      )}
    </button>

  </div>

</div>


        {/* SOURCES */}
        {sources.length > 0 && (
          <section className="card">

            <div className="section-title">
              <BookOpen size={20} />

              <div>
                <h2>Sources</h2>
                <p>
                  Information retrieved from your document.
                </p>
              </div>
            </div>


            <div className="sources">

              {sources.map((source, index) => (

                <div
                  className="source"
                  key={source.id || index}
                >

                  <div className="source-header">

                    <div>
                      <strong>
                        📄 {source.filename}
                      </strong>

                      <span>
                        Page {source.page_number}
                      </span>
                    </div>

                    <div className="scores">
                      <span>
                        Similarity{" "}
                        {source.similarity.toFixed(3)}
                      </span>

                      {source.rerank_score !== undefined && (
                        <span>
                          Rerank{" "}
                          {source.rerank_score.toFixed(3)}
                        </span>
                      )}
                    </div>

                  </div>

                  <p className="source-content">
                    {source.content}
                  </p>

                </div>

              ))}

            </div>

          </section>
        )}

      </main>

      <footer>
        Built with React + FastAPI + Supabase + RAG
      </footer>

    </div>
  );
}

export default App;