from job_agent.nodes import chat_node
from job_agent.states import AgentState

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("chat_node", chat_node)
    graph.set_entry_point('chat_node')
    graph.set_finish_point('chat_node')
    app = graph.compile(checkpointer=MemorySaver())
    return app

def main():
    print("Its Working")

