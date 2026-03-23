from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv
import os

load_dotenv()

researcher = Agent(
    role="Researcher",
    goal="Sammle praezise und aktuelle Informationen ueber das gegebene Thema.",
    backstory=(
        "Du bist ein erfahrener Recherche-Experte. "
        "Du analysierst Themen gruendlich und lieferst strukturierte Fakten."
    ),
    llm="claude-sonnet-4-20250514",
    verbose=True
)

writer = Agent(
    role="Writer",
    goal="Schreibe einen klaren, gut strukturierten Bericht auf Basis der Recherche.",
    backstory=(
        "Du bist ein professioneller Texter. "
        "Du verwandelst Rohdaten in verstaendliche, ansprechende Texte."
    ),
    llm="claude-sonnet-4-20250514",
    verbose=True
)

reviewer = Agent(
    role="Reviewer",
    goal="Pruefe den Bericht auf Fehler, Luecken und Qualitaet. Verbessere ihn.",
    backstory=(
        "Du bist ein kritischer Redakteur mit hohen Qualitaetsstandards. "
        "Du findest Schwaechen und gibst konkretes Verbesserungs-Feedback."
    ),
    llm="claude-sonnet-4-20250514",
    verbose=True
)

def create_tasks(topic: str):
    task_research = Task(
        description=f"Recherchiere das Thema: '{topic}'. "
                    "Sammle die wichtigsten Fakten, Hintergruende und aktuelle Entwicklungen. "
                    "Strukturiere sie als detaillierte Liste mit Unterpunkten.",
        expected_output="Eine detaillierte, strukturierte Liste mit allen wichtigen Fakten zum Thema.",
        agent=researcher
    )

    task_write = Task(
        description="Schreibe einen strukturierten Bericht mit exakt 500-700 Woertern. "
                    "Pflichtstruktur: "
                    "1. Ueberschrift (mit # Markdown) "
                    "2. Einleitung (1 Absatz, Ueberblick und Relevanz) "
                    "3. Hauptteil mit 3 Unterabschnitten (je mit ## Ueberschrift) "
                    "4. Fazit (1 Absatz, Ausblick) "
                    "Nutze Markdown-Formatierung fuer Ueberschriften und **Fettschrift** fuer Schluesselbegriffe.",
        expected_output="Ein vollstaendiger Markdown-Bericht mit 500-700 Woertern, Ueberschriften und Fazit.",
        agent=writer,
        context=[task_research]
    )

    task_review = Task(
        description="Reviewe den Bericht: Pruefe Wortanzahl (muss 500-700 Woerter sein), "
                    "Struktur (Einleitung, 3 Abschnitte, Fazit), Korrektheit und Lesbarkeit. "
                    "Gib ausschliesslich den finalen, verbesserten Markdown-Bericht zurueck - "
                    "keine Review-Kommentare, nur den fertigen Text.",
        expected_output="Nur der finale, fertige Markdown-Bericht (500-700 Woerter), ohne Meta-Kommentare.",
        agent=reviewer,
        context=[task_write]
    )

    return [task_research, task_write, task_review]

def run_crew(topic: str) -> str:
    tasks = create_tasks(topic)
    crew = Crew(
        agents=[researcher, writer, reviewer],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    result = crew.kickoff()
    return str(result)

if __name__ == "__main__":
    topic = "Kuenstliche Intelligenz in der Medizin 2025"
    print(f"\n Starte Agents fuer Thema: {topic}\n")
    result = run_crew(topic)
    print("\n FINALES ERGEBNIS:\n")
    print(result)
