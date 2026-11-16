"""FastAPI entry point.

Run locally:  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .data import DEMO_STUDENT_ID, STUDENTS
from .llm import Provider, build_provider

log = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 20  # messages kept per session (user + assistant)

app = FastAPI(title="AI Academic Assistant", version="0.1.0")

# session key -> list of {"role", "content"} text turns. In-memory: a real
# deployment would use Redis or a database.
_sessions: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    tools_used: list[str]
    provider: str


@lru_cache
def get_provider() -> Provider:
    return build_provider()


@app.get("/health")
def health(provider: Provider = Depends(get_provider)) -> dict:
    return {"status": "ok", "provider": provider.name}


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    provider: Provider = Depends(get_provider),
    x_student_id: str = Header(default=DEMO_STUDENT_ID),
) -> ChatResponse:
    # Demo auth: the header stands in for a real login token (e.g. a JWT from
    # the university's identity provider).
    if x_student_id not in STUDENTS:
        raise HTTPException(status_code=401, detail="Unknown student.")

    key = f"{x_student_id}:{request.session_id}"
    history = _sessions.setdefault(key, [])
    history.append({"role": "user", "content": request.message})

    try:
        result = provider.respond(list(history), x_student_id)
    except Exception:
        history.pop()  # don't keep a user turn that got no answer
        log.exception("Provider failed")
        raise HTTPException(status_code=502, detail="The assistant is unavailable. Try again shortly.")

    history.append({"role": "assistant", "content": result.reply})
    while len(history) > MAX_HISTORY_TURNS:
        del history[:2]  # drop whole user+assistant pairs so history still starts with a user turn

    return ChatResponse(reply=result.reply, tools_used=result.tools_used, provider=provider.name)
