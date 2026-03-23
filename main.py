from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────────
# AGENTS
# ─────────────────────────────────────────

researcher = Agent(
    role="Researcher",
    goal="Sammle die wichtigsten Fakten und Hintergruende zum gegebenen Thema.",
    backstory="Du bist ein erfahrener Recherche-Experte. Du lieferst strukturierte, praezise Fakten.",
    llm="claude-haiku-4-5-20251001",
    verbose=True
)

writer = Agent(
    role="Writer",
    goal="Schreibe einen strukturierten Bericht mit 500-700 Woertern auf Basis der Recherche.",
    backstory="Du bist ein professioneller Texter. Du schreibst klar, strukturiert und ansprechend.",
    llm="claude-haiku-4-5-20251001",
    verbose=True
)

reviewer = Agent(
    role="Reviewer",
    goal="Pruefe den Bericht kurz auf offensichtliche Fehler und gib ihn unveraendert zurueck falls er gut ist.",
    backstory="Du bist ein schneller Lektor. Du korrigierst nur grobe Fehler und gibst den Text sonst direkt weiter.",
    llm="claude-haiku-4-5-20251001",
    verbose=True
)

# ─────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────

def create_tasks(topic: str):
    task_research = Task(
        description=f"Recherchiere '{topic}'. Erstelle eine strukturierte Liste der 5 wichtigsten Fakten und Hintergruende.",
        expected_output="Eine kompakte Liste mit 5 Fakten zum Thema.",
        agent=researcher
    )

    task_write = Task(
        description=(
            "Schreibe einen Bericht mit 500-700 Woertern. "
            "Struktur (Pflicht): # Ueberschrift, Einleitung, ## Abschnitt 1, ## Abschnitt 2, ## Abschnitt 3, Fazit. "
            "Nutze Markdown und **Fettschrift** fuer Schluesselbegriffe."
        ),
        expected_output="Fertiger Markdown-Bericht, 500-700 Woerter, mit Ueberschriften und Fazit.",
        agent=writer,
        context=[task_research]
    )

    task_review = Task(
        description=(
            "Lies den Bericht. Falls er klar, vollstaendig und ca. 500-700 Woerter lang ist, "
            "gib ihn UNVERAENDERT zurueck. Korrigiere NUR offensichtliche Tippfehler oder fehlende Ueberschriften. "
            "Kein Kommentar, kein Meta-Text - nur der fertige Bericht."
        ),
        expected_output="Der finale Markdown-Bericht ohne Kommentare.",
        agent=reviewer,
        context=[task_write]
    )

    return [task_research, task_write, task_review]

# ─────────────────────────────────────────
# CREW
# ─────────────────────────────────────────

def run_crew(topic: str) -> str:
    tasks = create_tasks(topic)
    crew = Crew(
        agents=[researcher, writer, reviewer],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    return str(crew.kickoff())

if __name__ == "__main__":
    topic = "Kuenstliche Intelligenz in der Medizin"
    print(f"\nStarte Agents fuer: {topic}\n")
    print(run_crew(topic))
