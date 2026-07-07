from job_agent.nodes import chat_node
from job_agent.nodes import tool_condition
from job_agent.states import AgentState

from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langgraph.checkpoint.memory import MemorySaver

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("chat_node", chat_node)
    graph.add_edge(START, 'chat_node')
    graph.add_conditional_edges('chat_node', tool_condition)
    graph.add_edge("chat_node", END)
    app = graph.compile(checkpointer=MemorySaver())
    return app

def main():
    print("Its Working")

