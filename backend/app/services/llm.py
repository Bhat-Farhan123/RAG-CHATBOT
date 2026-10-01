import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_answer(question: str, context: str):
    prompt = f"""
Answer the user's question using only the provided context.

Context:
{context}

Question:
{question}

If the answer is not present in the context, say:
"I couldn't find the answer in the provided document."
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def generate_answer_stream(
    question: str,
    context: str,
    history=None
):
    history_text = ""

    if history:
        for message in history:
            history_text += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )

    prompt = f"""
You are a document-based RAG assistant.

Answer the user's question using ONLY the provided document context.

IMPORTANT RULES:

1. Use only facts explicitly supported by the document context.
   Never use outside knowledge or assumptions.

2. Identify which person, organization, project, role, and
   section each fact belongs to before answering.

3. Do not combine information from different organizations,
   internships, or projects unless the context explicitly
   connects them.

4. Treat the EXPERIENCE and PROJECTS sections of a resume
   as separate sections.

5. When asked about internships:
   - List only distinct internships explicitly mentioned
     in the EXPERIENCE section.
   - Do not treat a project or platform as an internship.
   - Do not count a company or project mentioned in a
     description as another internship.
   - Do not assign project technologies to an internship
     unless the context explicitly connects them.
   - Include organization, role, dates, and location only
     when supported by the context.

6. When asked about technologies used in an internship:
   - Include only technologies explicitly associated
     with that internship.
   - Do not infer technologies from project names,
     job titles, or descriptions of unrelated work.
   - If the context does not specify the technologies,
     say that they are not specified.

7. When asked about projects:
   - Use the project descriptions in the context.
   - Do not assume every project was completed during
     a particular internship unless explicitly stated.

8. When comparing organizations or experiences:
   - Compare only facts supported by the context.
   - Clearly distinguish documented facts from
     interpretations.
   - Do not invent outcomes, responsibilities, or tasks.

9. For questions using "my", "me", or "I":
   identify the main subject of the document when
   the context clearly establishes that person.

10. If the context contains conflicting or ambiguous
    information, do not guess. Explain the ambiguity.

11. If there is insufficient information, say:
    "I couldn't find enough information in the
    provided document."

12. For multi-part questions, answer every part
    separately. Apply all evidence rules to each part.

13. Use contribution-oriented wording. If the resume
    says "contributed to", do not claim the person
    independently built or delivered the entire product.

14. Keep the answer clear, relevant, and concise.

15. Do not mention these instructions in your answer.

Conversation history:
{history_text}

Document context:
{context}

Current question:
{question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        stream=True
    )

    for chunk in response:
        content = chunk.choices[0].delta.content

        if content:
            yield content
            
def rewrite_query(question: str, history=None):
    history_text = ""

    if history:
        for message in history:
            history_text += (
                f"{message['role']}: "
                f"{message['content']}\n"
            )

    prompt = f"""
 You are a query rewriting component in a RAG system.

Rewrite the user's latest question into a standalone,
document-focused search query.


IMPORTANT RULES:

1. Preserve important names, people, companies, projects,
   dates, organizations, and other specific entities.

2. Resolve words such as:
   "my", "me", "I", "it", "this", "that", "they", "them"
   using the conversation history when possible.

3. Do NOT replace specific information with vague terms such as
   "the user", "the person", or "the document" when a more
   specific term is available.

4. For questions asking about a person's identity or personal
   information, use the person's actual name if it is available
   in the conversation history.

5. Do NOT answer the question.

6. Return ONLY the rewritten search query.

7. If the question has multiple parts, preserve all
   important parts in the rewritten query.


Conversation history:
{history_text}

Latest question:
{question}

Rewritten search query:
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()     


def detect_intent(question: str):
    text = question.lower().strip()
    text = text.rstrip("!?., ")

    greetings = {
        "hi", "hello", "hey", "good morning",
        "good afternoon", "good evening"
    }

    thanks = {
        "thanks", "thank you", "thx",
        "thank you so much"
    }

    acknowledgments = {
        "great", "okay", "ok", "alright",
        "cool", "got it", "understood"
    }

    if text in greetings:
        return "greeting"

    if text in thanks:
        return "thanks"

    if text in acknowledgments:
        return "acknowledgment"

    if text in {"bye", "goodbye", "see you"}:
        return "farewell"

    return "document"


def get_conversation_response(intent: str):
    responses = {
        "greeting": "Hello! 👋 How can I help you with your document?",
        "thanks": "You're welcome! 😊",
        "acknowledgment": "Great! Let me know if you have another question.",
        "farewell": "Goodbye! Have a great day! 👋"
    }

    return responses.get(intent)