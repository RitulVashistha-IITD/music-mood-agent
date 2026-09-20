from google.adk.agents import Agent


def suggest_genre(mood: str) -> dict:
    """Suggest a music genre that fits a given mood.

    Args:
        mood: A short description of how the user feels.
    Returns:
        A dict with the mood and a suggested genre.
    """
    table = {
        "anxious": "ambient",
        "happy": "upbeat pop",
        "sad": "acoustic",
        "focused": "lo-fi",
    }
    return {"mood": mood, "suggested_genre": table.get(mood.lower(), "indie")}


root_agent = Agent(
    name="mood_agent",
    model="gemini-2.5-flash",
    description="Suggests a music genre based on how the user feels.",
    instruction=(
        "You are a warm music companion. When the user tells you how they feel, "
        "call the suggest_genre tool, then explain the pick in one friendly sentence."
    ),
    tools=[suggest_genre],
)