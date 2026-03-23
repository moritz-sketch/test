from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_crew

app = FastAPI(title="Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    topic: str

class AgentResponse(BaseModel):
    result: str
    topic: str

@app.get("/")
def root():
    return {"message": "Multi-Agent API laeuft! Gehe zu /docs fuer die API-Dokumentation."}

@app.post("/run-agents", response_model=AgentResponse)
def run_agents(request: AgentRequest):
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Thema darf nicht leer sein.")
    try:
        result = run_crew(request.topic)
        return AgentResponse(result=result, topic=request.topic)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# uvicorn api:app --reload
