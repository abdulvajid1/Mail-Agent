from mail_agent.agent import build_graph
from mail_agent.model import load_model
from mail_agent.prompts import SYSTEM_PROMPT
from mail_agent.tools import _send_mail
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from mail_agent.mcp import connect_to_mcp

import asyncio

async def main():
    app = build_graph()
    llm = load_model()
    mcp_client = connect_to_mcp()
    tools = await mcp_client.get_tools()

    if tools:
        llm = llm.bind_tools(tools)

    tool_registory = {tool.name: tool for tool in tools}

    user_input = "send a mail to my self mail saying i am good, my mail is bbad48882@gmail.com"   
    # user_input = "hey hru"   
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]

    input_state = {"messages": messages}
    config = RunnableConfig(configurable={'thread_id': "1", "llm": llm, "tools": tool_registory})

    async for msg, _ in app.astream(input_state, config, stream_mode='messages'): # type: ignore
        print(msg.content, end='', flush=True) # type: ignore

    state = app.get_state(config)
    messages = state.values['messages']
    for msg in messages:
        msg.pretty_print()

    
if __name__ == "__main__":
    asyncio.run(main())


        # user_input = input("User: ")
