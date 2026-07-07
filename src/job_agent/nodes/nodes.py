from job_agent.states import AgentState
from langchain_ollama import ChatOllama

def chat_node(state: AgentState, config):
    messages = state['messages']
    llm = config['configurable']['llm']
    ai_message = llm.invoke(messages)
    return {"messages": [ai_message]}


def tool_conditional_node(state: AgentState, config):
    tool_name = state["messages"].tool_calls