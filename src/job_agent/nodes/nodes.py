from job_agent.states import AgentState
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableConfig
from langchain.messages import ToolMessage

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
    
def tool_node(state: AgentState, config: RunnableConfig):
    # print('hallowwwwwwwwwwwwwwwwwwwwwwww')
    tool_calls = state["messages"][-1].tool_calls # type: ignore , [{'name': 'send_mail', 'args': {'to':
    tool_registory = config['configurable']['tools'] # type: ignore {"tool_name": tool}
    tool_messages = []
    for tool in tool_calls:
        tool_name = tool['name']
        tool_args = tool['args']
        runnable_tool = tool_registory[tool_name]
        tool_output = runnable_tool.invoke(tool_args)
        tool_messages.append(ToolMessage(content=tool_output, tool_call_id=uuid4()))

    return {'messages': tool_messages}
