import os
import re
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "mood_agent", ".env"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from mood_agent.agent import root_agent
from mood_agent.tools import search_songs

APP_NAME = "mood_agent"
USER_ID = "web_user"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_session"


def parse_reply(text: str) -> dict:
    """Pull the JSON object out of the model's reply, tolerating stray text/fences."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        cleaned = m.group(0)
    return json.loads(cleaned)


def _norm(s: str) -> str:
    """Lowercase, strip spaces/punctuation for forgiving name comparison."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def enrich(songs: list) -> list:
    """Look each song up and KEEP IT ONLY IF the found artist matches the claim."""
    queries = [f"{s.get('title','')} {s.get('artist','')}" for s in songs]
    # ask iTunes for a few matches per query, not just the top one
    found = search_songs(queries, limit=5).get("results", {})
    out = []
    for s, q in zip(songs, queries):
        claimed = _norm(s.get("artist", ""))
        tracks = found.get(q, {}).get("tracks", [])
        match = None
        for t in tracks:
            got = _norm(t.get("artist", ""))
            # accept if the claimed artist name appears in the found one (or vice versa)
            if claimed and (claimed in got or got in claimed):
                match = t
                break
        if not match:
            continue  # couldn't confirm the real artist -> drop it, don't fake it
        art = (match.get("artwork_url") or "").replace("100x100", "300x300")
        out.append({
            "title": match.get("title"),          # use iTunes' real title/artist
            "artist": match.get("artist"),
            "reason": s.get("reason", ""),
            "apple_url": match.get("apple_url"),
            "preview_url": match.get("preview_url"),
            "artwork_url": art,
        })
    return out


@app.post("/chat")
async def chat(req: ChatRequest):
    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=req.session_id
    )
    if session is None:
        await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=req.session_id
        )

    message = types.Content(role="user", parts=[types.Part(text=req.message)])

    # Run the agent; catch model/quota failures so the UI shows a friendly note
    reply = ""
    try:
        async for event in runner.run_async(
            user_id=USER_ID, session_id=req.session_id, new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                reply = "".join(part.text or "" for part in event.content.parts)
    except Exception as e:
        msg = str(e).lower()
        if "429" in msg or "ratelimit" in msg or "rate limit" in msg or "quota" in msg or "resource_exhausted" in msg:
            return {
                "intro": ("I've hit today's free-request limit across all the models — "
                          "the tradeoff of running fully free. Try again in a minute, or "
                          "later today after the daily reset."),
                "songs": [],
            }
        return {
            "intro": "Something went wrong reaching the models — please try again in a moment.",
            "songs": [],
        }

    # Parse the model's JSON and attach real, verified playable links
    try:
        data = parse_reply(reply)
        return {"intro": data.get("intro", ""), "songs": enrich(data.get("songs", []))}
    except Exception:
        return {"intro": "", "songs": [], "text": reply}  # graceful fallback


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True), name="static")