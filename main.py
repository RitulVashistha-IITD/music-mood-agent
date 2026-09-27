import os
from dotenv import load_dotenv

# Load the API keys BEFORE importing the agent
load_dotenv(os.path.join(os.path.dirname(__file__), "mood_agent", ".env"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from mood_agent.agent import root_agent

APP_NAME = "mood_agent"
USER_ID = "web_user"

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "web_session"


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

    reply = ""
    async for event in runner.run_async(
        user_id=USER_ID, session_id=req.session_id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply = "".join(part.text or "" for part in event.content.parts)

    return {"reply": reply}


# Serve the web page — must be mounted LAST so /chat still works
app.mount("/", StaticFiles(directory="static", html=True), name="static")