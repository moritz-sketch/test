from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
import anthropic
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="Lokaler AI Agent mit Gedaechtnis")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["*"]
)

@app.middleware("http")
async def add_cloudflare_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

memory = chromadb.PersistentClient(path="./memory")
collection = memory.get_or_create_collection("agent_memory")

claude = anthropic.Anthropic(api_key=os.getenv("_my-key5"))

class ChatRequest(BaseModel):
    message: str
    save_memory: bool = True

class MemoryRequest(BaseModel):
    content: str
    category: str
    tags: list[str] = []

def search_memory(query: str, n=5) -> list[str]:
    try:
        results = collection.query(query_texts=[query], n_results=min(n, collection.count()))
        return results["documents"][0] if results["documents"] else []
    except:
        return []

def save_to_memory(content: str, category: str, tags: list[str] = []):
    doc_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    collection.add(
        documents=[content],
        metadatas=[{"category": category, "tags": str(tags), "date": datetime.now().isoformat()}],
        ids=[doc_id]
    )
    return doc_id

def extract_and_save_knowledge(user_msg: str, assistant_response: str):
    keywords = ["github", "render", "website", "deploy", "error", "fix", "trick",
                "url", "api", "button", "setting", "install", "command"]
    combined = (user_msg + " " + assistant_response).lower()
    if any(kw in combined for kw in keywords):
        content = f"Frage: {user_msg[:200]}\nAntwort: {assistant_response[:500]}"
        save_to_memory(content, "auto_learned", ["auto"])

@app.post("/chat")
def chat(req: ChatRequest):
    memories = search_memory(req.message)
    memory_context = ""
    if memories:
        memory_context = "\n\nRelevante Erinnerungen:\n"
        for i, m in enumerate(memories, 1):
            memory_context += f"{i}. {m[:300]}\n"

    system_prompt = f"""Du bist ein persoenlicher KI-Assistent fuer Moritz in Muenchen.
Du hilfst bei Web-Entwicklung, KI-Projekten und technischen Aufgaben.
Du antwortest auf Deutsch und bist direkt und hilfreich.
{memory_context}"""

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": req.message}]
    )
    answer = response.content[0].text

    if req.save_memory:
        extract_and_save_knowledge(req.message, answer)

    return {
        "answer": answer,
        "memories_used": len(memories),
        "memory_snippets": memories[:2]
    }

@app.post("/memory/add")
def add_memory(req: MemoryRequest):
    doc_id = save_to_memory(req.content, req.category, req.tags)
    return {"saved": True, "id": doc_id}

@app.get("/memory/search")
def search(query: str, n: int = 5):
    results = collection.query(query_texts=[query], n_results=min(n, max(1, collection.count())))
    return {"results": results["documents"][0] if results["documents"] else [],
            "metadata": results["metadatas"][0] if results["metadatas"] else []}

@app.get("/memory/all")
def get_all():
    all_docs = collection.get()
    return {"count": len(all_docs["ids"]),
            "memories": [{"id": i, "content": d[:200], "meta": m}
                        for i, d, m in zip(all_docs["ids"],
                                           all_docs["documents"],
                                           all_docs["metadatas"])]}

@app.delete("/memory/{doc_id}")
def delete_memory(doc_id: str):
    collection.delete(ids=[doc_id])
    return {"deleted": doc_id}

@app.get("/")
def root():
    return {"status": "Agent laeuft",
            "memories": collection.count(),
            "endpoints": ["/chat", "/memory/add", "/memory/search", "/memory/all"]}
