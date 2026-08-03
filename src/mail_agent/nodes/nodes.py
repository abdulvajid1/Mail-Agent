from mail_agent.states import AgentState
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableConfig
from langchain.messages import ToolMessage

from langgraph.config import get_stream_writer

from uuid import uuid4

def chat_node(state: AgentState, config: RunnableConfig):
    messages = state['messages']
    llm = config['configurable']['llm'] # type: ignore
    ai_message = llm.invoke(messages)
    return {"messages": [ai_message]}


def tool_condition(state: AgentState, config: RunnableConfig):
    last_message = state["messages"][-1]
    if last_message.tool_calls: # type: ignore
        return True
    else:
        return False
    
async def tool_node(state: AgentState, config: RunnableConfig):

    writer = get_stream_writer()
    tool_calls = state["messages"][-1].tool_calls # type: ignore , [{'name': 'send_mail', 'args': {'to':
    tool_registory = config['configurable']['tools'] # type: ignore {"tool_name": tool}
    tool_messages = []
    for tool in tool_calls:
        tool_name = tool['name']
        tool_args = tool['args']
        runnable_tool = tool_registory[tool_name]
        writer(f'Executing {tool_name} tool......')
        tool_output = await runnable_tool.ainvoke(tool_args)
        tool_messages.append(ToolMessage(content=tool_output, tool_call_id=tool.get('id') or str(uuid4())))

    return {'messages': tool_messages}
