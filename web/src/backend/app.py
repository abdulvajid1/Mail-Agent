import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from mail_agent import MailAgent
from mail_agent.utils import is_ollama_running, load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = MailAgent()
    app.state.agent_ready = False
    app.state.agent_error = None
    try:
        await app.state.agent.intialize()
        app.state.agent_ready = True
    except Exception as exc:  # noqa: BLE001
        # Don't crash the server: surface the error through /config and /chat
        app.state.agent_error = str(exc)
    yield


app = FastAPI(lifespan=lifespan)

# Allow the Vite dev server (and anything else in dev) to talk to the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def generate_response(user_input: str, agent: MailAgent):
    try:
        async for event in agent.stream(user_input):
            yield sse(event)
        yield sse({"type": "done", "data": None})
    except Exception as exc:  # noqa: BLE001
        yield sse({"type": "error", "data": str(exc)})
        yield sse({"type": "done", "data": None})


def _require_ready() -> None:
    if not app.state.agent_ready:
        raise RuntimeError(
            app.state.agent_error
            or "Agent is not initialized. Run `mail-agent setup` first."
        )


class ChatRequest(BaseModel):
    user_input: str


@app.get("/")
async def root():
    return {"status": "ok", "docs": "/docs", "chat": "/chat", "config": "/config"}


@app.get("/config")
async def config():
    config = load_config()
    return {
        "ready": app.state.agent_ready,
        "error": app.state.agent_error,
        "ollama_running": is_ollama_running(),
        "model": config.get("model"),
        "user_mail": config.get("user_mail"),
        "enabled_tools": config.get("enabled_tools", []),
        "mail_authorization": config.get("mail_authorization", False),
    }


# @app.get("/chat")
# async def chat_get(user_input: str):
#     _require_ready()
#     return StreamingResponse(
#         content=generate_response(user_input, app.state.agent),
#         media_type="text/event-stream",
#         headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
#     )
    
@app.post("/chat")
async def chat_post(body: ChatRequest):
    _require_ready()
    return StreamingResponse(
        content=generate_response(body.user_input, app.state.agent),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
    
