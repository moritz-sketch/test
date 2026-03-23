# AI Research Agent

Eine Web-App mit 3 KI-Agents (Researcher, Writer, Reviewer), die zu einem beliebigen Thema einen strukturierten 500-700-Woerter-Bericht erstellen.

## Architektur

```
GitHub Pages (Frontend)  ->  Backend API (Python/FastAPI)  ->  CrewAI Agents  ->  Claude API
```

## Lokale Entwicklung

### Voraussetzungen
- Python 3.10+
- Anthropic API Key -> https://console.anthropic.com

### Setup

```bash
git clone https://github.com/moritz-sketch/test.git
cd test

python -m venv venv
venv\Scripts\activate
source venv/bin/activate

pip install crewai crewai-tools fastapi uvicorn python-dotenv

echo ANTHROPIC_API_KEY=dein-key > .env
```

### Starten

```bash
uvicorn api:app --reload

start index.html
```

## Deployment

- **Frontend**: GitHub Pages (automatisch ueber dieses Repo)
- **Backend**: Render.com oder Railway.app (kostenlose Tier verfuegbar)

Nach dem Backend-Deployment: In index.html die API_URL auf deine Backend-URL setzen.

## Projektstruktur

```
index.html       # Frontend (GitHub Pages)
main.py          # CrewAI Agents
api.py           # FastAPI Backend
requirements.txt # Python-Abhaengigkeiten
.env             # API Keys (nicht in Git!)
.gitignore
```
