from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from mail_agent import MailAgent
from contextlib import asynccontextmanager

import json


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = MailAgent()
    await app.state.agent.intialize()
    yield
    

app = FastAPI(lifespan=lifespan)


async def generate_response(user_input: str, agent: MailAgent):
    async for event in agent.stream(user_input): # event : {type, data}
        yield (
            f"data: {json.dumps(event)}\n\n"
        )

@app.get('/chat')
async def chat(user_input: str): 
    agent = app.state.agent
    return StreamingResponse(content=generate_response(user_input, agent), media_type="text/event-stream")